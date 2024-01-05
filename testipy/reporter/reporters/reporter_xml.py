import os

from typing import Dict

from testipy.configs import enums_data, default_config
from testipy.helpers import get_traceback_list
from testipy.lib_modules.state_counter import StateCounter
from testipy.lib_modules.start_arguments import StartArguments
from testipy.reporter.report_manager import ReportManager, ReportBase

HEADER = '<?xml version="1.0" encoding="UTF-8" ?>\n'


class ReporterJUnitXML(ReportBase):

    def __init__(self, rm: ReportManager, sa: StartArguments):
        super().__init__(self.__class__.__name__)
        self._rm = rm

        # create results folder if doesnt exists
        self.__ensure_folder(rm.get_results_folder_runtime())

        # full path name
        self.fpn = os.path.join(rm.get_results_folder_runtime(), f"report.xml")

        # try to create empty file
        with open(self.fpn, "w"):
            pass

    def __ensure_folder(self, folder_name):
        try:
            if not os.path.exists(folder_name):
                os.makedirs(folder_name, exist_ok=True)
                self._rm._execution_log("INFO", f"Created folder {folder_name}")
        except:
            self._rm._execution_log("CRITICAL", f"Could not create folder {folder_name}", "ERROR")

    def save_file(self, current_test, data, filename):
        pass

    def copy_file(self, current_test, orig_filename, dest_filename, data):
        pass

    def __startup__(self, selected_tests):
        pass

    def __teardown__(self, end_state):
        mb = self.get_report_manager_base()  # get manager base

        with open(self.fpn, "w") as xml_file:
            xml_file.write(HEADER)
            self._generate_tag_testsuites(mb, xml_file)

    def startPackage(self, package_name):
        pass

    def endPackage(self):
        pass

    def startSuite(self, suite_name, attr=None):
        pass

    def endSuite(self):
        pass

    def startTest(self, attr: Dict, test_name: str = "", usecase: str = "", description: str = ""):
        pass

    def testInfo(self, current_test, info, level, attachment=None):
        pass

    def testStep(self, current_test, state: str, reason_of_state: str = "", description: str = "", take_screenshot: bool = False, qty: int = 1, exc_value: BaseException = None):
        pass

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
        pass

    def _generate_tag_testsuites(self, mb: ReportManager, xml_file):
        # all tests counter
        atc = mb.get_all_test_results()["details"].get_counters()

        # set id
        id = self._rm.get_foldername_runtime()

        # set name
        name = self._rm.get_project_name()

        # set total of tests
        tests = str(atc.get_total())

        # set total of failures
        failures = str(atc[enums_data.STATE_FAILED] + atc[enums_data.STATE_FAILED_KNOWN_BUG])

        # set total of duration
        time = "{:.3f}".format(mb.get_reporter_duration())

        # Log XML tag
        xml_file.write(f"<testsuites {id=} {name=} {tests=} {failures=} {time=}>\n".replace("'", '"'))
        self._generate_tag_testsuite(mb, xml_file)
        xml_file.write("</testsuites>")

    def _generate_tag_testsuite(self, mb: ReportManager, xml_file):
        for pkg_name, pkg_dict in mb.get_package_list().items():
            pkg = pkg_dict['details']

            for suite_name, suite_dict in pkg_dict["suite_list"].items():
                suite = suite_dict['details']
                sc = suite.get_counters()

                # set id
                id = f"{pkg.get_name(True)}{default_config.separator_package_suite_test}{suite.get_name(True)}"

                # set name
                name = suite_name

                # set total of tests
                tests = str(sc.get_total())

                # set total of failures
                failures = str(sc[enums_data.STATE_FAILED] + sc[enums_data.STATE_FAILED_KNOWN_BUG])

                # set total of duration
                time = "{:.3f}".format(suite.get_duration())

                # Log XML tag
                xml_file.write(f" <testsuite {id=} {name=} {tests=} {failures=} {time=}>\n".replace("'", '"'))
                self._generate_tag_testcase(mb, xml_file, suite_dict["test_list"], id)
                xml_file.write(" </testsuite>\n")

    def _generate_tag_testcase(self, mb: ReportManager, xml_file, test_list: dict, suite_id: str):
        for test_name, list_of_test_usecases in test_list.items():
            for current_test in list_of_test_usecases:          # ReporterDetails
                usecase_name = current_test.get_usecase()

                # set id
                id = string_fixer(f"{suite_id}.[{current_test.get_name(True)}] - {usecase_name}")

                # set name
                name = string_fixer(f"{test_name} - {usecase_name}")

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
