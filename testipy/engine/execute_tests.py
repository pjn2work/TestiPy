#!/usr/bin/env python3

import os
import traceback

from typing import List

from testipy.lib_modules import common_methods as cm
from testipy.lib_modules.state_counter import StateCounter
from testipy.lib_modules.textdecor import color_status
from testipy.lib_modules.start_arguments import StartArguments
from testipy.reporter.report_manager import ReportManager
from testipy.configs import enums_data, default_config


def _get_nok_on_success_or_on_failure(report_manager: ReportManager, test: dict) -> str:
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


class Executer:

    def __init__(self, execution_log, full_path_tests_scripts_foldername):
        self.execution_log = execution_log
        self._current_method_execution_id = 0
        self._total_failed_skipped = 0
        cm.TESTS_ROOT_FOLDER = full_path_tests_scripts_foldername

    def _change_cwd_to_package(self, package_name):
        package_name = package_name.replace(default_config.separator_package, os.path.sep)
        os.chdir(os.path.join(cm.TESTS_ROOT_FOLDER, package_name))
        self.execution_log("DEBUG", f"Current folder {os.getcwd()}")

    def _inc_failed(self, qty=1):
        self._total_failed_skipped += qty

    def get_total_failed_skipped(self):
        return self._total_failed_skipped

    def _finish_current_method_test(self, rm: ReportManager, package, suite, test, had_exception, percent_completed):
        # kill not properly ended tests (if had_exeption then they are already killed)
        for current_test in list(rm.get_test_running_list(test["method_id"])):
            tc = current_test.get_test_step_counters()

            if tc[enums_data.STATE_FAILED] > 0:
                rm.testFailed(current_test, tc.get_last_reason_of_state(enums_data.STATE_FAILED) or "!", had_exception)
            if tc[enums_data.STATE_FAILED_KNOWN_BUG] > 0:
                rm.testFailedKnownBug(current_test, tc.get_last_reason_of_state(
                    enums_data.STATE_FAILED_KNOWN_BUG) or "!", had_exception)
            elif tc[enums_data.STATE_SKIPPED] > 0:
                rm.testSkipped(current_test, tc.get_last_reason_of_state(enums_data.STATE_SKIPPED) or "!", had_exception)
            else:
                rm.testPassed(current_test, tc.get_last_reason_of_state(enums_data.STATE_PASSED) or "!", had_exception)

        # sum all tests counter for this method, for all ncycle
        all_tests_from_method_call = rm.get_test_list_by_method_id(test["method_id"])
        results = StateCounter()
        if len(all_tests_from_method_call) > 0:
            for current_test in all_tests_from_method_call:
                results.inc_states(current_test.get_counters())
        else:
            current_test = rm.startTest(test[enums_data.TAG_NAME], test, "AUTO-CREATED")
            rm.testEndAs(current_test, default_config.if_no_test_started_mark_as, f"No test started by {test['method_name']}", had_exception)

        # get Reason of Failure
        rof = results.get_last_reason_of_state(enums_data.STATE_FAILED)
        if not rof:
            rof = results.get_last_reason_of_state(enums_data.STATE_FAILED_KNOWN_BUG)
        if not rof:
            rof = results.get_last_reason_of_state(enums_data.STATE_SKIPPED)
        if not rof:
            rof = results.get_last_reason_of_state(enums_data.STATE_PASSED)
        rof = str(rof)[:70] if rof else "!"

        # increment global failed (skipped, bug)
        total_failed = sum([results[state] for state in default_config.count_as_failed_states])
        if total_failed == 0 and (had_exception or (
                results[enums_data.STATE_PASSED] == 0 and default_config.if_no_test_started_mark_as in default_config.count_as_failed_states)):
            total_failed = 1
        self._inc_failed(total_failed)

        # show summary
        total = max(results.get_total(), total_failed)
        test_result = enums_data.STATE_FAILED if total_failed > 0 else enums_data.STATE_PASSED
        duration = f"{results.get_sum_time_laps():.2f}".rjust(6)

        self.execution_log("INFO", "{} {:3.0f}% [{}s] ({}/{}) {}/{} - {}({}) | {}".format(color_status(test_result), percent_completed, duration, total_failed, total, package["package_name"], suite["filename"], test["method_name"], test["method_id"], rof))

    # !!!Run test!!!
    def _run_test(self, package, suite, test, rm: ReportManager, dryrun_mode, debug_code, onlyonce, percent_completed):
        def run_it():
            nok = _get_nok_on_success_or_on_failure(rm, test)
            if not nok:
                td = {k: v for k, v in test.items() if k != "test_obj"}
                _ = getattr(suite["app"], test["method_name"])(td, rm, ncycles=test["ncycles"], param=test["param"])

                if rm.get_current_test() is None:
                    current_test = rm.startTest(test, usecase="AUTO-CREATED")
            else:
                current_test = rm.startTest(test, usecase="AUTO-CREATED")
                rm.testSkipped(current_test, nok)

        had_exception = None

        if dryrun_mode:
            current_test = rm.startTest(test, usecase="dryrun")
            rm.testSkipped(current_test, "DRYRUN")
        else:
            if onlyonce:
                test["ncycles"] = 1

            # clear current test to see if the method call creates any new tests
            rm.clear_current_test()

            try:
                for _ in range(test["ncycles"]):
                    run_it()
            except Exception as e:
                had_exception = e

                # get full stacktrace
                tb_list = traceback.format_tb(e.__traceback__)
                tb = "v  "*55 + "\n"
                tb += "".join(tb_list[2:])
                tb += "^  "*55

                # no test started by the method call
                if rm.get_current_test() is None:
                    current_test = rm.startTest(test, usecase="AUTO-CREATED")

                # Fail all unEnded tests
                for current_test in list(rm.get_test_running_list(test["method_id"])):
                    rm.testInfo(current_test, f"Full stacktrace:\n{tb}", "ERROR")
                    rm.testFailed(current_test, str(e), exc_value=e)

                # If debug_code parameter is selected, then tests will end
                if debug_code:
                    self.execution_log("CRITICAL", "- {}/{} - {}.{}({}) needs review because: {}\n{}".format(package["package_name"], suite["filename"], suite["suite_name"], test["method_name"], test["method_id"], str(e), tb))
                    raise e

        # Kill unEnded tests if not properly ended by themselves and show summary
        self._finish_current_method_test(rm, package, suite, test, had_exception, percent_completed)

    def _get_total_number_of_methods(self, selected_tests):
        total = 0
        for package in selected_tests:
            for suite in package["suite_list"]:
                for test in suite["test_list"]:
                    total += 1 * suite.get("ncycles", 1) * package.get("ncycles", 1)
        return total

    def execute_tests(self, report_manager, selected_tests, dryrun_mode=True, debug_code=False, onlyonce=False):
        total_methods_to_call = self._get_total_number_of_methods(selected_tests)
        method_seq = 0

        for package in selected_tests:
            for _ in range(1 if onlyonce else package.get("ncycles", 1)):

                self._change_cwd_to_package(package["package_name"])
                report_manager.startPackage(package["package_name"])

                for suite in package["suite_list"]:
                    for _ in range(1 if onlyonce else suite.get("ncycles", 1)):

                        # initialize suite __init__()
                        suite["app"] = suite["suite_obj"](**suite.get("suite_kwargs", dict()))
                        report_manager.startSuite(suite[enums_data.TAG_NAME], cm.dict_without_keys(suite, "suite_obj"))

                        for test in suite["test_list"]:
                            method_seq += 1
                            self._run_test(package, suite, dict(test), report_manager, dryrun_mode, debug_code, onlyonce, method_seq * 100 / total_methods_to_call)

                        report_manager.endSuite()
                        del suite["app"]

                report_manager.endPackage()


def run(execution_log, sa: StartArguments, selected_tests: List, report_manager: ReportManager) -> int:
    runner = Executer(execution_log, sa.full_path_tests_scripts_foldername)

    runner.execute_tests(report_manager, selected_tests, sa.dryrun, sa.debugcode, sa.onlyonce)

    return runner.get_total_failed_skipped()
