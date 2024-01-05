import os
import logging

from typing import Dict
from tabulate import tabulate
from mss import mss

from testipy.lib_modules.common_methods import get_app_version, list_traceback, prettify, format_duration
from testipy.lib_modules.start_arguments import StartArguments
from testipy.reporter.report_manager import ReportManager, ReportBase
from testipy.configs import enums_data

default_format ="%(asctime)s %(levelname)s - %(message)s"


class ReporterLog(ReportBase):

    def __init__(self, rm: ReportManager, sa: StartArguments):
        super().__init__(self.__class__.__name__)

        self.results_folder_runtime = rm.get_results_folder_runtime()
        self.filename = f"{rm.get_project_name()}.log"
        self.rm = rm
        self._logger: logging.Logger = None
        self._screenshot_num = 0

        # create folder
        self.__create_folder(self.results_folder_runtime)

        # init logger if not inited
        self.get_logger()

    def get_logger(self, level=logging.DEBUG, format=default_format):
        # create logger
        if self._logger is None:
            fpn = os.path.join(self.results_folder_runtime, self.filename)
            f_handler = logging.FileHandler(fpn, mode="w", encoding="utf-8")
            f_handler.setFormatter(logging.Formatter(format))

            self._logger = logging.getLogger("reporter_log")
            self._logger.addHandler(f_handler)
            self._logger.setLevel(level)

        return self._logger

    def log(self, info, level="DEBUG"):
        try:
            self.get_logger().log(logging.getLevelName(level), info)
        except Exception as e:
            self.rm._execution_log("CRITICAL", info)

    def __create_folder(self, folder_name):
        try:
            os.makedirs(folder_name, exist_ok=True)
            self.log(f"Created results folder {folder_name}", level="DEBUG")
        except:
            self.log(f"Could not create results folder {folder_name}", "ERROR")

    def save_file(self, current_test, data, filename):
        try:
            with open(filename, "w") as fh:
                fh.write(data)
            self.log(f"Created file {filename}", "INFO")
        except Exception as e:
            self.log(f"Could not create file {filename}", "ERROR")

    def copy_file(self, current_test, orig_filename, dest_filename, data):
        try:
            with open(dest_filename, "wb") as fh:
                fh.write(data)
            self.log(f"Copied from '{orig_filename}' to {dest_filename}", "INFO")
        except Exception as e:
            self.log(f"Could not create file {dest_filename}", "ERROR")

    def __startup__(self, selected_tests):
        app, version, _ = get_app_version()
        self.log(f"{app} {version}", "INFO")
        self.log("Selected Tests:\n{}".format(tabulate(selected_tests["data"], headers=selected_tests["headers"], tablefmt="fancy_grid")), "INFO")

    def __teardown__(self, end_state):
        mb = self.get_report_manager_base()
        sc = mb.get_reporter_counter()
        tab_resume = tabulate(sc.get_summary_per_state(), headers=("State", "Qty", "%", "RoS"), floatfmt=".2f", tablefmt="fancy_grid")
        self.log("{} - {:.2f}%/{} took {} to {}\n{}".format(mb.get_reporter_name(), sc.get_state_percentage(
            enums_data.STATE_PASSED), sc.get_total(), format_duration(mb.get_reporter_duration()), end_state, tab_resume), "INFO")
        self.close_logger()

    def startPackage(self, package_name):
        mb = self.get_report_manager_base()
        self.log(f"Starting Package {mb.get_package_name(True)}", "INFO")

    def endPackage(self):
        mb = self.get_report_manager_base()
        sc = mb.get_package_counter()
        tab_resume = tabulate(sc.get_summary_per_state(), headers=("State", "Qty", "%", "RoS"), floatfmt=".2f", tablefmt="fancy_grid")
        self.log("Ending Package {} - {:.2f}%/{} took {}\n{}".format(mb.get_package_name(True), sc.get_state_percentage(
            enums_data.STATE_PASSED), sc.get_total(), format_duration(mb.get_package_duration()), tab_resume), "INFO")

    def startSuite(self, suite_name, attr=None):
        mb = self.get_report_manager_base()
        self.log(f"Starting Suite {mb.get_suite_name(True)}", "INFO")
        self.__create_folder(self.rm.get_results_folder_filename())

    def endSuite(self):
        mb = self.get_report_manager_base()
        sc = mb.get_suite_counter()
        tab_resume = tabulate(sc.get_summary_per_state(), headers=("State", "Qty", "%", "RoS"), floatfmt=".2f", tablefmt="fancy_grid")
        self.log("Ending Suite {} - {:.2f}%/{} took {}\n{}".format(mb.get_suite_name(True), sc.get_state_percentage(
            enums_data.STATE_PASSED), sc.get_total(), format_duration(mb.get_suite_duration()), tab_resume), "INFO")

    def startTest(self, attr: Dict, test_name: str = "", usecase: str = "", description: str = ""):
        mb = self.get_report_manager_base()

        test_full_name = mb.get_full_name(mb.get_current_test(), True)
        self.log(f"Starting Test {test_full_name} - {usecase}", "INFO")

        #str_attr = "\n".join([f"{k}: {str(v).replace('set()', '')}" for k, v in attr.items() if k != "test_comment"])
        #self.testInfo(mb.get_current_test(), f"TAGs:\n{str_attr}", "DEBUG")

    def testInfo(self, current_test, info, level, attachment=None):
        mb = self.get_report_manager_base()

        test_full_name = mb.get_full_name(current_test, True)
        usecase = current_test.get_usecase()

        self.log(f"{test_full_name} - {usecase}: {info}", level)

    def testStep(self, current_test, state: str, reason_of_state: str = "", description: str = "", take_screenshot: bool = False, qty: int = 1, exc_value: BaseException = None):
        self.__log_exception(current_test, exc_value)
        if take_screenshot:
            with mss() as sct:
                self._screenshot_num += 1
                output_file = f"log_screenshot_{self._screenshot_num:03.0f}.png"
                sct.shot(output=output_file, mon=1)
                self.rm.copy_file(current_test, orig_filename=output_file, delete_source=True)

    def testSkipped(self, current_test, reason_of_state="", exc_value: BaseException = None):
        self._endTest(current_test, enums_data.STATE_SKIPPED, reason_of_state, exc_value)

    def testPassed(self, current_test, reason_of_state="", exc_value: BaseException = None):
        self._endTest(current_test, enums_data.STATE_PASSED, reason_of_state, exc_value)

    def testFailed(self, current_test, reason_of_state="", exc_value: BaseException = None):
        self._endTest(current_test, enums_data.STATE_FAILED, reason_of_state, exc_value)

    def testFailedKnownBug(self, current_test, reason_of_state="", exc_value: BaseException = None):
        self._endTest(current_test, enums_data.STATE_FAILED_KNOWN_BUG, reason_of_state, exc_value)

    def showStatus(self, message: str):
        pass

    def showAlertMessage(self, message: str):
        pass

    def inputPromptMessage(self, message: str, default_value: str = ""):
        pass

    def _endTest(self, current_test, ending_state, end_reason, exc_value: BaseException = None):
        mb = self.get_report_manager_base()

        test_full_name = mb.get_full_name(current_test, True)
        usecase = current_test.get_usecase()
        duration = current_test.get_duration()

        self.__log_test_steps(current_test)
        self.__log_exception(current_test, exc_value)

        self.log(f"Ending Test {test_full_name} - {usecase} - {ending_state} - took {format_duration(duration)} - {end_reason}", "INFO")

    def __log_test_steps(self, current_test):
        tc = current_test.get_test_step_counters()
        if len(tc.get_timed_laps()) > 0:
            test_steps = current_test.get_test_step_counters_tabulate(tablefmt="fancy_grid")
            self.log("Test steps:\n" + test_steps, "DEBUG")
            str_summary = "Steps Summary: " + tc.summary(verbose=False)
        else:
            str_summary = "Test Summary: " + current_test.get_counters().summary(verbose=False)
        self.log(str_summary, "DEBUG")

    def __log_exception(self, current_test, exc_value):
        if exc_value:
            mb = self.get_report_manager_base()

            test_full_name = mb.get_full_name(current_test, True)
            usecase = current_test.get_usecase()
            info = prettify(list_traceback(exc_value))

            self.log(f"{test_full_name} - {usecase}: {type(exc_value).__name__}\n{info}", "ERROR")

    def close_logger(self):
        try:
            for handler in self.get_logger().handlers:
                handler.close()
        except Exception as ex:
            error_message = f"Cannot close {self.filename}! {ex}"
            self.rm._execution_log("CRITICAL", error_message)
        self._logger = None
