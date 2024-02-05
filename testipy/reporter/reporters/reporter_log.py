import os
import logging

from typing import Dict
from tabulate import tabulate
from mss import mss

from testipy import get_exec_logger
from testipy.configs import enums_data
from testipy.helpers import get_traceback_list, prettify, format_duration
from testipy.lib_modules.common_methods import get_app_version
from testipy.lib_modules.start_arguments import StartArguments
from testipy.reporter import ReportManager, ReportInterface, PackageDetails, SuiteDetails, TestDetails


log_format = "%(asctime)s %(levelname)s - %(message)s"
table_format = "github"
_exec_logger = get_exec_logger()


class ReporterLog(ReportInterface):

    def __init__(self, rm: ReportManager, sa: StartArguments):
        super().__init__(self.__class__.__name__)

        self.results_folder_runtime = rm.get_results_folder_runtime()
        self.filename = "report.log"
        self.rm = rm
        self.sa = sa
        self._logger: logging.Logger = None
        self._screenshot_num = 0

        # create folder
        self.__create_folder(self.results_folder_runtime)

        # init logger if not inited
        self.__get_logger()

    def save_file(self, current_test: TestDetails, data, filename: str):
        try:
            with open(filename, "w") as fh:
                fh.write(data)
            self.__log(f"Created file {filename}", "INFO")
        except Exception as e:
            self.__log(f"Could not create file {filename}", "ERROR")

    def copy_file(self, current_test: TestDetails, orig_filename: str, dest_filename: str, data):
        try:
            with open(dest_filename, "wb") as fh:
                fh.write(data)
            self.__log(f"Copied from '{orig_filename}' to {dest_filename}", "INFO")
        except Exception as e:
            self.__log(f"Could not create file {dest_filename}", "ERROR")

    def _startup_(self, selected_tests: Dict):
        app, version, _ = get_app_version()
        self.__log(f"{app} {version}", "INFO")
        self.__log("Selected Tests:\n{}".format(tabulate(selected_tests["data"],
                                                         headers=selected_tests["headers"],
                                                         tablefmt=table_format)), "INFO")

    def _teardown_(self, end_state: str):
        sc = self.rm.pm.state_counter
        tab_resume = tabulate(sc.get_summary_per_state_without_ros(),
                              headers=("State", "Qty", "%"),
                              floatfmt=".2f",
                              tablefmt=table_format)
        self.__log("Teardown - {:.2f}% success for {} tests, took {} to {}\n{}".format(
            sc.get_state_percentage(enums_data.STATE_PASSED),
            sc.get_total(),
            format_duration(self.rm.pm.get_duration()),
            end_state,
            tab_resume), "INFO")

        self.__close_logger()

    def start_package(self, pd: PackageDetails):
        self.__log(f"Starting Package {pd.get_name(with_cycle_number=True)}", "INFO")

    def end_package(self, pd: PackageDetails):
        sc = pd.state_counter

        tab_resume = tabulate(sc.get_summary_per_state_without_ros(),
            headers=("State", "Qty", "%"),
            floatfmt=".2f",
            tablefmt=table_format)

        self.__log(
            "Ending Package {} - {:.2f}% success for {} tests, took {}\n{}".format(
                pd.get_name(with_cycle_number=True),
                sc.get_state_percentage(enums_data.STATE_PASSED),
                sc.get_total(),
                format_duration(pd.get_duration()),
                tab_resume),"INFO")

    def start_suite(self, sd: SuiteDetails):
        self.__log(f"Starting Suite {sd.get_full_name(with_cycle_number=True)}", "INFO")
        self.__create_folder(self.rm.get_results_folder_filename(sd, ""))

    def end_suite(self, sd: SuiteDetails):
        tab_resume = tabulate(sd.state_counter.get_summary_per_state_without_ros(),
                              headers=("State", "Qty", "%"),
                              floatfmt=".2f",
                              tablefmt=table_format)

        self.__log("Ending Suite {} - {:.2f}% success for {} tests, took {}\n{}".format(
            sd.get_full_name(with_cycle_number=True),
            sd.state_counter.get_state_percentage(enums_data.STATE_PASSED),
            sd.state_counter.get_total(),
            format_duration(sd.get_duration()),
            tab_resume), "INFO")

    def start_test(self, current_test: TestDetails):
        test_full_name = current_test.get_full_name(with_cycle_number=True)
        self.__log(f"Starting Test {test_full_name}", "INFO")

    def test_info(self, current_test: TestDetails, info, level, attachment=None):
        test_full_name = current_test.get_full_name(with_cycle_number=True)
        self.__log(f"{test_full_name}: {info}", level)

    def test_step(self,
                  current_test: TestDetails,
                  state: str,
                  reason_of_state: str = "",
                  description: str = "",
                  take_screenshot: bool = False,
                  qty: int = 1,
                  exc_value: BaseException = None):
        self.__log_exception(current_test, exc_value)
        if take_screenshot:
            with mss() as sct:
                self._screenshot_num += 1
                output_file = f"log_screenshot_{self._screenshot_num:03.0f}.png"
                sct.shot(output=output_file, mon=1)
                self.rm.copy_file(current_test, orig_filename=output_file, delete_source=True)

    def end_test(self, current_test: TestDetails, ending_state: str, end_reason: str = "", exc_value: BaseException = None):
        test_full_name = current_test.get_full_name(with_cycle_number=True)
        test_duration = current_test.get_duration()

        self.__log_test_steps(current_test)
        self.__log_exception(current_test, exc_value)

        self.__log(f"Ending Test {test_full_name} - {ending_state} - took {format_duration(test_duration)} - {end_reason}", "INFO")

    def show_status(self, message: str):
        pass

    def show_alert_message(self, message: str):
        pass

    def input_prompt_message(self, message: str, default_value: str = ""):
        pass

    def __get_logger(self, level=logging.DEBUG, format=log_format):
        # create logger
        if self._logger is None:
            fpn = os.path.join(self.results_folder_runtime, self.filename)
            f_handler = logging.FileHandler(fpn, mode="w", encoding="utf-8")
            f_handler.setFormatter(logging.Formatter(format))

            self._logger = logging.getLogger("testipy_reporter_log")
            self._logger.addHandler(f_handler)
            self._logger.setLevel(level)

        return self._logger

    def __log(self, info, level="DEBUG"):
        try:
            self.__get_logger().log(logging.getLevelName(level), info)
        except Exception as e:
            _exec_logger.critical(info)

    def __create_folder(self, folder_name):
        try:
            os.makedirs(folder_name, exist_ok=True)
            self.__log(f"Created results folder {folder_name}", level="DEBUG")
        except:
            self.__log(f"Could not create results folder {folder_name}", "ERROR")

    def __log_test_steps(self, current_test: TestDetails):
        test_full_name = current_test.get_full_name(with_cycle_number=True)
        tc = current_test.get_test_step_counters()
        if len(tc.get_timed_laps()) > 0:
            test_steps = current_test.get_test_step_counters_tabulate(tablefmt=table_format)
            self.__log(f"Test steps {test_full_name}:\n" + test_steps, "DEBUG")
            str_summary = "Steps Summary: " + tc.summary(verbose=False)
        else:
            str_summary = "Test Summary: " + current_test.get_counters().summary(verbose=False)
        self.__log(str_summary, "DEBUG")

    def __log_exception(self, current_test, exc_value):
        if exc_value:
            test_full_name = current_test.get_full_name(with_cycle_number=True)
            info = prettify(get_traceback_list(exc_value))

            self.__log(f"{test_full_name}: {type(exc_value).__name__}\n{info}", "ERROR")

    def __close_logger(self):
        try:
            for handler in self.__get_logger().handlers:
                handler.close()
        except Exception as ex:
            error_message = f"Cannot close {self.filename}! {ex}"
            _exec_logger.critical(error_message)
        self._logger = None
