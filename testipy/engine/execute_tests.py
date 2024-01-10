#!/usr/bin/env python3

import os
import traceback

from typing import List, Dict

from testipy.configs import enums_data, default_config
from testipy.lib_modules import common_methods as cm
from testipy.lib_modules.state_counter import StateCounter
from testipy.lib_modules.textdecor import color_state
from testipy.lib_modules.start_arguments import StartArguments
from testipy.helpers.prettify import format_duration
from testipy.reporter.report_manager import ReportManager


class Executer:

    def __init__(self, execution_log, full_path_tests_scripts_foldername):
        self.execution_log = execution_log
        self._current_method_execution_id = 0
        self._total_failed_skipped = 0
        cm.TESTS_ROOT_FOLDER = full_path_tests_scripts_foldername

    def get_total_failed_skipped(self):
        return self._total_failed_skipped

    def execute_tests(self, report_manager, selected_tests, dryrun_mode=True, debug_code=False, onlyonce=False):
        total_methods_to_call = _get_total_runs_of_selected_methods(selected_tests)
        method_seq = 0

        for package in selected_tests:
            for _ in range(1 if onlyonce else package.get("ncycles", 1)):

                self._change_cwd_to_package(package["package_name"])
                report_manager.startPackage(package["package_name"])

                for suite in package["suite_list"]:
                    for _ in range(1 if onlyonce else suite.get("ncycles", 1)):

                        report_manager.startSuite(suite[enums_data.TAG_NAME], cm.dict_without_keys(suite, "suite_obj"))

                        # initialize suite __init__()
                        try:
                            suite["app"] = suite["suite_obj"](**suite.get("suite_kwargs", dict()))
                        except Exception as ex:
                            # skip all methods/tests under this suite
                            for test in suite["test_list"]:
                                method_seq += 1
                                percent_completed = method_seq * 100 / total_methods_to_call
                                rof = f"Init suite failed: {ex}"

                                report_manager.testSkipped(report_manager.startTest(test, usecase="AUTO-CREATED"), reason_of_state=rof, exc_value=ex)

                                self._print_progress_when_method_ends(state=enums_data.STATE_SKIPPED,
                                    percent_completed=percent_completed, duration=0.0, total_failed=0, total=1,
                                    package=package, suite=suite, test=test, ros=rof)
                        else:
                            for test in suite["test_list"]:
                                method_seq += 1
                                percent_completed = method_seq * 100 / total_methods_to_call

                                self._call_test_method(package, suite, dict(test), report_manager, dryrun_mode, debug_code, onlyonce, percent_completed)
                            del suite["app"]

                        report_manager.endSuite()

                report_manager.endPackage()

    def _print_progress_when_method_ends(self, state: str, percent_completed: float, duration: float, total_failed: int, total: int, package: Dict, suite: Dict, test: Dict, ros: str):
        self.execution_log("INFO", "{:<26} {:3.0f}% {} ({}/{}) {}/{} - {}({}) | {}".format(
            color_state(state),
            percent_completed,
            format_duration(duration).rjust(10),
            total_failed, total,
            package["package_name"], suite["filename"],
            test["method_name"][len(default_config.prefix_tests):], test["method_id"],
            ros[:70]))

    def _auto_close_single_test(self, rm: ReportManager, current_test, had_exception: Exception = None):
        if had_exception:
            # get full stacktrace
            tb = _get_stacktrace_string_for_tests(had_exception)
            rm.testInfo(current_test, f"Full stacktrace:\n{tb}", "ERROR")
            rm.testFailed(current_test, reason_of_state=str(had_exception), exc_value=had_exception)
        else:
            tc_state, tc_ros = current_test.get_test_step_counters().get_state_by_severity()
            rm.testEndAs(current_test, state=tc_state, reason_of_state=tc_ros or "!", exc_value=None)

    def _auto_close_all_open_tests(self, rm: ReportManager, test, had_exception: Exception = None):
        for current_test in list(rm.get_test_running_list(test["method_id"])):
            self._auto_close_single_test(rm, current_test, had_exception)

    def _calculate_state_for_all_tests_under_this_method(self, rm: ReportManager, package, suite, test, had_exception: Exception, percent_completed: float):
        # End not properly ended tests - this should never happen here
        self._auto_close_all_open_tests(rm=rm, test=test, had_exception=had_exception)

        # sum all tests counter for this method, for all ncycle
        results = StateCounter()
        all_tests_from_method_call = rm.get_test_list_by_method_id(test["method_id"])
        if len(all_tests_from_method_call) > 0:
            for current_test in all_tests_from_method_call:
                results.inc_states(current_test.get_counters())
        else:
            # no test created by the method call, impossible to get here - just a safeguard
            current_test = rm.startTest(test, usecase="AUTO-CREATED")
            rm.testEndAs(current_test, state=default_config.if_no_test_started_mark_as, reason_of_state=f"No test started by {test['method_name']}", exc_value=had_exception)

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

        self._print_progress_when_method_ends(method_state, percent_completed, duration, total_failed, total, package, suite, test, method_ros or "!")

    def _call_test_method(self, package, suite, test, rm: ReportManager, dryrun_mode, debug_code, onlyonce, percent_completed):
        had_exception = None

        if dryrun_mode:
            # if "--dryrun" was passed then will skip all tests execution
            rm.testSkipped(rm.startTest(test, usecase="dryrun"), reason_of_state="DRYRUN")
        else:
            # get @ON_FAILURE or @ON_SUCCESS dependency
            nok = _get_nok_on_success_or_on_failure(rm, test)

            for _ in range(1 if onlyonce else test["ncycles"]):
                # clear current test to see if the method call creates any new tests
                rm.clear_current_test()

                try:
                    if nok:
                        rm.testSkipped(rm.startTest(test, usecase="AUTO-CREATED"), reason_of_state=nok)
                        break
                    else:
                        td = cm.dict_without_keys(test, keys_to_remove="test_obj")
                        # -->> call the test method <<--
                        _ = getattr(suite["app"], test["method_name"])(td, rm, ncycles=test["ncycles"], param=test["param"])

                        # no test started by the method call, create one and close it
                        if rm.get_current_test() is None:
                            rm.testEndAs(rm.startTest(test, usecase="AUTO-CREATED"), state=default_config.if_no_test_started_mark_as, reason_of_state="!", exc_value=None)

                        self._auto_close_all_open_tests(rm=rm, test=test)
                except Exception as ex:
                    # no test started by the method call, create one
                    if rm.get_current_test() is None:
                        _ = rm.startTest(test, usecase="AUTO-CREATED")

                    self._auto_close_all_open_tests(rm=rm, test=test, had_exception=ex)

                    # if "--debug_code" was passed, then will stop all execution
                    if debug_code:
                        self.execution_log("CRITICAL", "- {}/{} - {}.{}({}) needs review because: {}\n{}".format(
                            package["package_name"], suite["filename"],
                            suite["suite_name"], test["method_name"], test["method_id"],
                            str(ex), _get_stacktrace_string_for_tests(ex)))
                        raise ex
                    had_exception = ex

        self._calculate_state_for_all_tests_under_this_method(rm, package, suite, test, had_exception, percent_completed)

    def _change_cwd_to_package(self, package_name):
        package_name = package_name.replace(default_config.separator_package, os.path.sep)
        os.chdir(os.path.join(cm.TESTS_ROOT_FOLDER, package_name))
        self.execution_log("DEBUG", f"Current folder {os.getcwd()}")

    def _inc_failed(self, qty=1):
        self._total_failed_skipped += qty


def _get_nok_on_success_or_on_failure(report_manager: ReportManager, test: Dict) -> str:
    if test[enums_data.TAG_ON_SUCCESS] or test[enums_data.TAG_ON_FAILURE]:
        # dict(k = @NAME, v = [current_test#1_(from_suite#1), c_t#2_s#1, c_t#3_s#2, ...])
        all_tests = report_manager.get_test_list()

        for prio in test[enums_data.TAG_ON_SUCCESS]:
            # all tests under same suite (even if from different suite runs, not only from latest)
            for test_name, test_list in all_tests.items():
                # may have other tests with other priority under the same testName
                for current_test in test_list:
                    if current_test.get_prio() == prio:
                        for ended_test in test_list[::-1]:
                            if ended_test.is_passed():
                                break   # goto next break (continue to next prio)
                        else:
                            continue    # continue to next current_test on test_list
                        break           # goto next break (continue to next prio)
                else:
                    continue            # continue to next test_list on all_tests
                break                   # continue to next prio
            else:
                return f"NO SUCCESS on {prio=}"

        for prio in test[enums_data.TAG_ON_FAILURE]:
            # all tests under same suite (even if from different suite runs, not only from latest)
            for test_name, test_list in all_tests.items():
                # may have other tests with other priority under the same testName
                for current_test in test_list:
                    if current_test.get_prio() == prio:
                        for ended_test in test_list[::-1]:
                            if ended_test.is_failed():
                                break   # goto next break (continue to next prio)
                        else:
                            continue    # continue to next current_test on test_list
                        break           # goto next break (continue to next prio)
                else:
                    continue            # continue to next test_list on all_tests
                break                   # continue to next prio
            else:
                return f"NO FAILURE on {prio=}"

    return ""


def _get_total_runs_of_selected_methods(selected_tests: List) -> int:
    total = 0
    for package in selected_tests:
        for suite in package["suite_list"]:
            for test in suite["test_list"]:
                total += 1 * suite.get("ncycles", 1) * package.get("ncycles", 1)
    return total


def _get_stacktrace_string_for_tests(ex: Exception) -> str:
    tb_list = traceback.format_tb(ex.__traceback__)
    tb = "v  " * 55 + "\n"
    tb += "".join(tb_list[1:])
    tb += "^  " * 55
    return tb


def run_selected_tests(execution_log, sa: StartArguments, selected_tests: List, report_manager: ReportManager) -> int:
    runner = Executer(execution_log, sa.full_path_tests_scripts_foldername)

    runner.execute_tests(report_manager, selected_tests, sa.dryrun, sa.debugcode, sa.onlyonce)

    return runner.get_total_failed_skipped()
