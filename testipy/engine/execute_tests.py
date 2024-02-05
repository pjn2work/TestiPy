#!/usr/bin/env python3
import os
import traceback
import concurrent.futures

from typing import List, Dict

from testipy import get_exec_logger
from testipy.configs import enums_data, default_config
from testipy.lib_modules import common_methods as cm
from testipy.lib_modules.common_methods import synchronized
from testipy.lib_modules.state_counter import StateCounter
from testipy.lib_modules.textdecor import color_state
from testipy.lib_modules.start_arguments import StartArguments
from testipy.helpers.prettify import format_duration
from testipy.helpers.handle_assertions import ExpectedError
from testipy.reporter.report_manager import ReportManager
from testipy.reporter.package_manager import SuiteDetails


_exec_logger = get_exec_logger()


class ExecutionProgress:

    def __init__(self, total_methods_to_call):
        self.total_methods_to_call = total_methods_to_call
        self.percent_completed = 0.0
        self.method_seq = 0

    @synchronized
    def inc(self):
        self.method_seq += 1

    def get_percent_completed(self):
        return self.method_seq * 100 / self.total_methods_to_call

    @synchronized
    def method_progress(self, state: str, duration: float, total_failed: int, total: int, package_attr: Dict, suite_attr: Dict, method_attr: Dict, ros: str):
        _exec_logger.info("{:<26} {:3.0f}% {} ({}/{}) {}/{} - {}({}) | {}".format(
            color_state(state),
            self.get_percent_completed(),
            format_duration(duration).rjust(10),
            total_failed, total,
            package_attr["package_name"], suite_attr["filename"],
            method_attr["method_name"][len(default_config.prefix_tests):], method_attr["method_id"],
            ros[:70]))


class Executer:

    def __init__(self, full_path_tests_scripts_foldername, debug_testipy: bool = False):
        self._current_method_execution_id = 0
        self._total_failed_skipped = 0
        cm.TESTS_ROOT_FOLDER = full_path_tests_scripts_foldername
        self._debug_testipy = debug_testipy

    def get_total_failed_skipped(self):
        return self._total_failed_skipped

    def _execute_parallel(self, rm: ReportManager, selected_tests: List[Dict], dryrun_mode=True, debug_code=False, onlyonce=False, suite_threads=1):
        ep = ExecutionProgress(_get_total_runs_of_selected_methods(selected_tests))

        def _process_suite(suite_attr):
            for _ in range(1 if onlyonce else suite_attr.get("ncycles", 1)):
                sd = rm.startSuite(pd, suite_attr[enums_data.TAG_NAME],cm.dict_without_keys(suite_attr, ["suite_obj", "test_list"]))

                # initialize suite __init__()
                try:
                    suite_attr["app"] = suite_attr["suite_obj"](**suite_attr.get("suite_kwargs", dict()))
                    _error = None
                except Exception as ex:
                    _error = ex

                for method_attr in suite_attr["test_list"]:
                    ep.inc()
                    self._call_test_method(package_attr, suite_attr, dict(method_attr), sd, rm, dryrun_mode, debug_code, onlyonce, ep, _error)

                if "app" in suite_attr:
                    del suite_attr["app"]

                rm.end_suite(sd)

        for package_attr in selected_tests:
            for _ in range(1 if onlyonce else package_attr.get("ncycles", 1)):

                self._change_cwd_to_package(package_attr["package_name"])
                pd = rm.startPackage(package_attr["package_name"], package_attr)

                with concurrent.futures.ThreadPoolExecutor(max_workers=suite_threads) as executor:
                    tasks = {executor.submit(_process_suite, suite_attr): suite_attr for suite_attr in package_attr["suite_list"]}
                    concurrent.futures.wait(tasks)

                rm.end_package(pd)

    def _execute_sequential(self, rm: ReportManager, selected_tests: List[Dict], dryrun_mode=True, debug_code=False, onlyonce=False):
        ep = ExecutionProgress(_get_total_runs_of_selected_methods(selected_tests))

        for package_attr in selected_tests:
            for _ in range(1 if onlyonce else package_attr.get("ncycles", 1)):

                self._change_cwd_to_package(package_attr["package_name"])
                pd = rm.startPackage(package_attr["package_name"], package_attr)

                for suite_attr in package_attr["suite_list"]:
                    for _ in range(1 if onlyonce else suite_attr.get("ncycles", 1)):

                        sd = rm.startSuite(pd, suite_attr[enums_data.TAG_NAME], cm.dict_without_keys(suite_attr, ["suite_obj", "test_list"]))

                        # initialize suite __init__()
                        try:
                            suite_attr["app"] = suite_attr["suite_obj"](**suite_attr.get("suite_kwargs", dict()))
                            _error = None
                        except Exception as ex:
                            _error = ex

                        for method_attr in suite_attr["test_list"]:
                            ep.inc()
                            self._call_test_method(package_attr, suite_attr, dict(method_attr), sd, rm, dryrun_mode, debug_code, onlyonce, ep, _error)

                        if "app" in suite_attr:
                            del suite_attr["app"]

                        rm.end_suite(sd)

                rm.end_package(pd)

    def execute(self, rm: ReportManager, selected_tests: List[Dict], dryrun_mode=True, debug_code=False, onlyonce=False, suite_threads=1):
        if suite_threads > 1:
            self._execute_parallel(rm, selected_tests, dryrun_mode, debug_code, onlyonce, suite_threads)
        else:
            self._execute_sequential(rm, selected_tests, dryrun_mode, debug_code, onlyonce)

    def _auto_close_single_test(self, rm: ReportManager, current_test, had_exception: Exception = None):
        if had_exception:
            if isinstance(had_exception, ExpectedError):
                rm.testPassed(current_test, reason_of_state=f"Designed to fail with: {had_exception}", exc_value=had_exception)
            else:
                # get full stacktrace
                tb = _get_stacktrace_string_for_tests(had_exception)
                rm.test_info(current_test, f"Full stacktrace:\n{tb}", "ERROR")
                rm.testFailed(current_test, reason_of_state=str(had_exception), exc_value=had_exception)
        else:
            tc_state, tc_ros = current_test.get_test_step_counters().get_state_by_severity()
            rm.end_test(current_test, state=tc_state, reason_of_state=tc_ros or "!", exc_value=None)

    def _auto_close_all_open_tests_for_that_method(self, rm: ReportManager, sd: SuiteDetails, method_attr, had_exception: Exception = None):
        for current_test in list(sd.get_tests_running_by_meid(method_attr["method_id"])):
            self._auto_close_single_test(rm, current_test, had_exception)

    def _calculate_state_for_all_tests_under_this_method(self, rm: ReportManager, sd: SuiteDetails, package_attr, suite_attr, method_attr, had_exception: Exception, ep: ExecutionProgress):
        # End not properly ended tests - this should never happen here
        self._auto_close_all_open_tests_for_that_method(rm=rm, sd=sd, method_attr=method_attr, had_exception=had_exception)

        # sum all tests counter for this method, for all ncycle
        results = StateCounter()
        all_tests = sd.get_tests_by_meid(method_attr["method_id"])
        if all_tests:
            for current_test in all_tests:
                results.inc_states(current_test.get_counters())
        else:
            # no test created by the method call, impossible to get here - just a safeguard
            current_test = rm.startTest(method_attr, usecase="AUTO-CREATED")
            rm.end_test(current_test, state=default_config.if_no_test_started_mark_as, reason_of_state=f"No test started by {method_attr['method_name']}", exc_value=had_exception)

        # increment global failed (skipped, bug)
        total_failed = sum([results[state] for state in default_config.count_as_failed_states])
        if total_failed == 0 and (had_exception or (
                results[enums_data.STATE_PASSED] == 0 and default_config.if_no_test_started_mark_as in default_config.count_as_failed_states)):
            total_failed = 1
        self._inc_failed(total_failed)

        # show summary
        total = max(results.get_total(), total_failed)
        duration = results.get_sum_time_laps()
        method_state, method_ros = results.get_state_by_severity()

        ep.method_progress(method_state, duration, total_failed, total, package_attr, suite_attr, method_attr, method_ros or "!")

    def _call_test_method(self, package_attr, suite_attr, method_attr, sd: SuiteDetails, rm: ReportManager, dryrun_mode, debug_code, onlyonce, ep: ExecutionProgress, _error):
        had_exception = None
        method_attr["suite_details"] = sd

        if dryrun_mode:
            # if "--dryrun" was passed then will skip all tests execution
            rm.testSkipped(rm.startTest(method_attr, usecase="dryrun"), reason_of_state="DRYRUN")
        elif _error:
            rm.testSkipped(rm.startTest(method_attr, usecase="AUTO-CREATED"), reason_of_state=f"Init suite failed: {_error}", exc_value=_error)
            if self._debug_testipy:
                raise _error
        elif nok := _get_nok_on_success_or_on_failure(sd, method_attr):
            # get @ON_FAILURE or @ON_SUCCESS dependency
            rm.testSkipped(rm.startTest(method_attr, usecase="AUTO-CREATED"), reason_of_state=nok)
        else:
            for _ in range(1 if onlyonce else method_attr["ncycles"]):
                ma = cm.dict_without_keys(method_attr, keys_to_remove="test_obj")
                try:
                    # -->> call the test method <<--
                    _ = getattr(suite_attr["app"], method_attr["method_name"])(ma, rm, ncycles=method_attr["ncycles"], param=method_attr["param"])

                    # no test started by the method call, create one and close it
                    if len(sd.get_tests_by_meid(ma["method_id"])) == 0:
                        rm.end_test(rm.startTest(ma, usecase="AUTO-CREATED"), state=default_config.if_no_test_started_mark_as, reason_of_state="!", exc_value=None)

                    self._auto_close_all_open_tests_for_that_method(rm=rm, sd=sd, method_attr=ma)
                except Exception as ex:
                    # no test started by the method call, create one
                    if len(sd.get_tests_by_meid(ma["method_id"])) == 0:
                        _ = rm.startTest(ma, usecase="AUTO-CREATED")

                    self._auto_close_all_open_tests_for_that_method(rm=rm, sd=sd, method_attr=ma, had_exception=ex)

                    # if "--debug_code" was passed, then will stop all execution
                    if debug_code:
                        _exec_logger.critical("- {}/{} - {}.{}({}) needs review because: {}\n{}".format(
                            package_attr["package_name"], suite_attr["filename"],
                            suite_attr["suite_name"], ma["method_name"], ma["method_id"],
                            str(ex), _get_stacktrace_string_for_tests(ex)))
                        raise ex
                    had_exception = ex

        self._calculate_state_for_all_tests_under_this_method(rm, sd, package_attr, suite_attr, method_attr, had_exception, ep)

    def _change_cwd_to_package(self, package_name):
        package_name = package_name.replace(default_config.separator_package, os.path.sep)
        os.chdir(os.path.join(cm.TESTS_ROOT_FOLDER, package_name))
        _exec_logger.debug(f"Current folder {os.getcwd()}")

    def _inc_failed(self, qty=1):
        self._total_failed_skipped += qty


def _get_nok_on_success_or_on_failure(sd: SuiteDetails, method_attr: Dict) -> str:
    # at least one test, under same suite, with that prio has passed
    for prio in method_attr[enums_data.TAG_ON_SUCCESS]:
        if enums_data.STATE_PASSED not in sd.get_test_state_by_prio(prio):
            return f"NO SUCCESS on {prio=}"

    # at least one test, under same suite, with that prio has failed
    for prio in method_attr[enums_data.TAG_ON_FAILURE]:
        if (enums_data.STATE_FAILED not in sd.get_test_state_by_prio(prio) and
                enums_data.STATE_FAILED_KNOWN_BUG not in sd.get_test_state_by_prio(prio)):
            return f"NO FAILURE on {prio=}"

    return ""


def _get_total_runs_of_selected_methods(selected_tests: List) -> int:
    total = 0
    for package_attr in selected_tests:
        for suite_attr in package_attr["suite_list"]:
            for method_attr in suite_attr["test_list"]:
                total += 1 * suite_attr.get("ncycles", 1) * package_attr.get("ncycles", 1)
    return total


def _get_stacktrace_string_for_tests(ex: Exception) -> str:
    tb_list = traceback.format_tb(ex.__traceback__)
    tb = "v  " * 55 + "\n"
    tb += "".join(tb_list[1:])
    tb += "^  " * 55
    return tb


def run_selected_tests(sa: StartArguments, selected_tests: List[Dict], rm: ReportManager, debug_testipy: bool) -> int:
    runner = Executer(sa.full_path_tests_scripts_foldername, debug_testipy)

    runner.execute(rm, selected_tests, sa.dryrun, sa.debugcode, sa.onlyonce, sa.suite_threads)

    return runner.get_total_failed_skipped()
