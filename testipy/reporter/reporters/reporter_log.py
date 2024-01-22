import os
import logging

from typing import Dict
from tabulate import tabulate
from mss import mss

from testipy.configs import enums_data
from testipy.helpers import get_traceback_list, prettify, format_duration
from testipy.lib_modules.common_methods import get_app_version
from testipy.lib_modules.start_arguments import StartArguments
from testipy.reporter import ReportManager, ReportInterface

default_format ="%(asctime)s %(levelname)s - %(message)s"


class ReporterLog(ReportInterface):

    def __init__(self, rm: ReportManager, sa: StartArguments):
        super().__init__(self.__class__.__name__)

        self.results_folder_runtime = rm.get_results_folder_runtime()
        self.filename = f"{rm.get_project_name()}.log"
        self.rm = rm
        self.sa = sa
        self._logger: logging.Logger = None
        self._screenshot_num = 0

        # create folder
        self.__create_folder(self.results_folder_runtime)

        # init logger if not inited
        self.get_logger()

    def get_report_manager_base(self):
        return self.rm.get_report_manager_base()

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

    def __startup__(self, selected_tests: Dict):
        app, version, _ = get_app_version()
        self.log(f"{app} {version}", "INFO")
        self.log("Selected Tests:\n{}".format(tabulate(selected_tests["data"], headers=selected_tests["headers"], tablefmt="fancy_grid")), "INFO")

    def __teardown__(self, end_state):
        rmb = self.get_report_manager_base()
        sc = rmb.get_reporter_counter()
        tab_resume = tabulate(sc.get_summary_per_state(), headers=("State", "Qty", "%", "RoS"), floatfmt=".2f", tablefmt="fancy_grid")
        self.log("{} - {:.2f}%/{} took {} to {}\n{}".format(rmb.get_reporter_name(), sc.get_state_percentage(
            enums_data.STATE_PASSED), sc.get_total(), format_duration(rmb.get_reporter_duration()), end_state, tab_resume), "INFO")
        self.close_logger()

    def startPackage(self, package_name: str, package_attr: Dict):
        rmb = self.get_report_manager_base()
        self.log(f"Starting Package {rmb.get_package_name(True)}", "INFO")

    def endPackage(self, package_name: str, package_attr: Dict):
        rmb = self.get_report_manager_base()
        sc = rmb.get_package_counter()
        tab_resume = tabulate(sc.get_summary_per_state(), headers=("State", "Qty", "%", "RoS"), floatfmt=".2f", tablefmt="fancy_grid")
        self.log("Ending Package {} - {:.2f}%/{} took {}\n{}".format(rmb.get_package_name(True), sc.get_state_percentage(
            enums_data.STATE_PASSED), sc.get_total(), format_duration(rmb.get_package_duration()), tab_resume), "INFO")

    def startSuite(self, suite_name: str, suite_attr: Dict):
        rmb = self.get_report_manager_base()
        self.log(f"Starting Suite {rmb.get_suite_name(True)}", "INFO")
        self.__create_folder(self.rm.get_results_folder_filename())

    def endSuite(self, suite_name: str, suite_attr: Dict):
        rmb = self.get_report_manager_base()
        sc = rmb.get_suite_counter()
        tab_resume = tabulate(sc.get_summary_per_state(), headers=("State", "Qty", "%", "RoS"), floatfmt=".2f", tablefmt="fancy_grid")
        self.log("Ending Suite {} - {:.2f}%/{} took {}\n{}".format(rmb.get_suite_name(True), sc.get_state_percentage(
            enums_data.STATE_PASSED), sc.get_total(), format_duration(rmb.get_suite_duration()), tab_resume), "INFO")

    def startTest(self, method_attr: Dict, test_name: str = "", usecase: str = "", description: str = ""):
        rmb = self.get_report_manager_base()

        test_full_name = rmb.get_full_name(rmb.get_current_test(), True)
        self.log(f"Starting Test {test_full_name} - {usecase}", "INFO")

        #str_attr = "\n".join([f"{k}: {str(v).replace('set()', '')}" for k, v in attr.items() if k != "test_comment"])
        #self.testInfo(rmb.get_current_test(), f"TAGs:\n{str_attr}", "DEBUG")

    def testInfo(self, current_test, info, level, attachment=None):
        rmb = self.get_report_manager_base()

        test_full_name = rmb.get_full_name(current_test, True)
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

    def showStatus(self, message: str):
        pass

    def showAlertMessage(self, message: str):
        pass

    def inputPromptMessage(self, message: str, default_value: str = ""):
        pass

    def endTest(self, current_test, ending_state, end_reason, exc_value: BaseException = None):
        rmb = self.get_report_manager_base()

        test_full_name = rmb.get_full_name(current_test, True)
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
            rmb = self.get_report_manager_base()

            test_full_name = rmb.get_full_name(current_test, True)
            usecase = current_test.get_usecase()
            info = prettify(get_traceback_list(exc_value))

            self.log(f"{test_full_name} - {usecase}: {type(exc_value).__name__}\n{info}", "ERROR")

    def close_logger(self):
        try:
            for handler in self.get_logger().handlers:
                handler.close()
        except Exception as ex:
            error_message = f"Cannot close {self.filename}! {ex}"
            self.rm._execution_log("CRITICAL", error_message)
        self._logger = None
