import os

from typing import Dict

from testipy import get_exec_logger
from testipy.configs import enums_data
from testipy.helpers import get_traceback_list
from testipy.lib_modules.state_counter import StateCounter
from testipy.lib_modules.start_arguments import StartArguments
from testipy.reporter import ReportManager, ReportInterface, PackageDetails, SuiteDetails, TestDetails

HEADER = '<?xml version="1.0" encoding="UTF-8" ?>\n'


class ReporterJUnitXML(ReportInterface):

    def __init__(self, rm: ReportManager, sa: StartArguments):
        super().__init__(self.__class__.__name__)
        self.rm = rm

        # create results folder if doesnt exists
        self.__ensure_folder(rm.get_results_folder_runtime())

        # full path name
        self.fpn = os.path.join(rm.get_results_folder_runtime(), f"report.xml")

        # try to create empty file
        with open(self.fpn, "w"):
            pass

    def save_file(self, current_test: TestDetails, data, filename: str):
        pass

    def copy_file(self, current_test: TestDetails, orig_filename: str, dest_filename: str, data):
        pass

    def _startup_(self, selected_tests: Dict):
        pass

    def _teardown_(self, end_state: str):
        with open(self.fpn, "w") as xml_file:
            xml_file.write(HEADER)
            self._generate_tag_testsuites(xml_file)

    def start_package(self, pd: PackageDetails):
        pass

    def end_package(self, pd: PackageDetails):
        pass

    def start_suite(self, sd: SuiteDetails):
        pass

    def end_suite(self, sd: SuiteDetails):
        pass

    def start_test(self, current_test: TestDetails):
        pass

    def test_info(self, current_test: TestDetails, info, level, attachment=None):
        pass

    def test_step(self,
                  current_test: TestDetails,
                  state: str,
                  reason_of_state: str = "",
                  description: str = "",
                  take_screenshot: bool = False,
                  qty: int = 1,
                  exc_value: BaseException = None):
        pass

    def end_test(self, current_test: TestDetails, ending_state: str, end_reason: str = "", exc_value: BaseException = None):
        pass

    def show_status(self, message: str):
        pass

    def show_alert_message(self, message: str):
        pass

    def input_prompt_message(self, message: str, default_value: str = ""):
        pass

    def __ensure_folder(self, folder_name):
        try:
            if not os.path.exists(folder_name):
                os.makedirs(folder_name, exist_ok=True)
                _exec_logger.info(f"Created folder {folder_name}")
        except:
            _exec_logger.critical(f"Could not create folder {folder_name}")

    def _generate_tag_testsuites(self, xml_file):
        # all tests counter
        atc = self.rm.pm.state_counter

        # set id
        id = self.rm.get_foldername_runtime()

        # set name
        name = self.rm.get_project_name()

        # set total of tests
        tests = str(atc.get_total())

        # set total of failures
        failures = str(atc[enums_data.STATE_FAILED] + atc[enums_data.STATE_FAILED_KNOWN_BUG])

        # set total of duration
        time = "{:.3f}".format(self.rm.pm.get_duration())

        # Log XML tag
        xml_file.write(f"<testsuites {id=} {name=} {tests=} {failures=} {time=}>\n".replace("'", '"'))
        self._generate_tag_testsuite(xml_file)
        xml_file.write("</testsuites>")

    def _generate_tag_testsuite(self, xml_file):
        for pd in self.rm.pm.all_packages:
            for sd in pd.suite_manager.all_suites:
                sc = sd.state_counter

                # set id
                id = sd.get_full_name(with_cycle_number=True)

                # set name
                name = sd.get_name()

                # set total of tests
                tests = str(sc.get_total())

                # set total of failures
                failures = str(sc[enums_data.STATE_FAILED] + sc[enums_data.STATE_FAILED_KNOWN_BUG])

                # set total of duration
                time = "{:.3f}".format(sd.get_duration())

                # Log XML tag
                xml_file.write(f" <testsuite {id=} {name=} {tests=} {failures=} {time=}>\n".replace("'", '"'))
                self._generate_tag_testcase(xml_file, sd, id)
                xml_file.write(" </testsuite>\n")

    def _generate_tag_testcase(self, xml_file, sd: SuiteDetails, suite_id: str):
        for current_test in sd.test_manager.all_tests:
            usecase_name = current_test.get_usecase()

            # set id
            id = string_fixer(current_test.get_full_name(with_cycle_number=True))

            # set name
            name = string_fixer(f"{current_test.get_name()} - {usecase_name}")

            # set total of duration
            time = "{:.3f}".format(current_test.get_duration())

            # set total of failures
            fail_counters = current_test.get_test_step_counters()
            failures = fail_counters[enums_data.STATE_FAILED] + fail_counters[enums_data.STATE_FAILED_KNOWN_BUG]
            if failures == 0:
                fail_counters = current_test.get_counters()
                failures = fail_counters[enums_data.STATE_FAILED] + fail_counters[enums_data.STATE_FAILED_KNOWN_BUG]
            failures = str(failures)

            # show testcase
            xml_file.write(f'  <testcase id="{id}" name="{name}" failures="{failures}" time="{time}"')
            if failures == "0":
                xml_file.write(f' />\n')
            else:
                xml_file.write(f'>\n')
                self._generate_tag_failure(xml_file, fail_counters, current_test.get_counters())
                xml_file.write("  </testcase>\n")

    def _generate_tag_failure(self, xml_file, fail_counters: StateCounter, test_counters: StateCounter):
        self._generate_failure_detail(xml_file, fail_counters, test_counters, enums_data.STATE_FAILED)
        self._generate_failure_detail(xml_file, fail_counters, test_counters, enums_data.STATE_FAILED_KNOWN_BUG)

    def _generate_failure_detail(self, xml_file, fail_counters: StateCounter, test_counters: StateCounter, filter_state):
        is_test_failed = test_counters.get_last_state() == enums_data.STATE_FAILED
        failure_type = "ERROR" if is_test_failed else "WARNING"

        for state, qty, total_seconds, reason_of_state, description, exc_value, end_time in fail_counters.get_timed_laps(filter_state):

            message = string_fixer(reason_of_state)  # test_counters.get_last_reason_of_state())

            xml_file.write(f'   <failure message="{message}" type="{failure_type}">\n')

            if exc_value:
                tbl = get_traceback_list(exc_value)[-1]
                tbld = tbl["error_lines"][-1]

                category = tbl["type"]
                file = tbld["filename"]
                line = tbld["lineno"]
                method = tbld["method"]
                code = tbld["code"]
            else:
                category = file = method = code = "-"
                line = 0

            xml_file.write(f"{failure_type}: {reason_of_state}\n")
            xml_file.write(f"Category: {category}\n")
            xml_file.write(f"File: {file}\n")
            xml_file.write(f"Line: {line}\n")
            xml_file.write(f"Method: {method}\n")
            xml_file.write(f"Code: {code}\n")

            xml_file.write("   </failure>\n")


def string_fixer(text):
    if not isinstance(text, str):
        text = str(text)
    return text.replace('"', "'").replace("\n", " | ")
