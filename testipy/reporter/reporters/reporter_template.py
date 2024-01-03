from typing import Dict
from testipy.lib_modules.start_arguments import StartArguments
from testipy.reporter.report_manager import ReportManager, ReportBase
from testipy.configs import enums_data


class ReporterTemplate(ReportBase):

    def __init__(self, rm: ReportManager, sa: StartArguments):
        super().__init__(self.__class__.__name__)
        self._rm = rm
        self._sa = sa

    def save_file(self, current_test, data, filename):
        pass

    def copy_file(self, current_test, orig_filename, dest_filename, data):
        pass

    def __startup__(self, selected_tests):
        mb = self.get_report_manager_base()  # get manager base

    def __teardown__(self, end_state):
        mb = self.get_report_manager_base()  # get manager base

    def startPackage(self, package_name):
        mb = self.get_report_manager_base()  # get manager base

    def endPackage(self):
        mb = self.get_report_manager_base()  # get manager base

    def startSuite(self, suite_name, attr=None):
        mb = self.get_report_manager_base()  # get manager base

    def endSuite(self):
        mb = self.get_report_manager_base()  # get manager base

    def startTest(self, attr: Dict, test_name: str = "", usecase: str = "", description: str = ""):
        mb = self.get_report_manager_base()  # get manager base

    def testInfo(self, current_test, info, level, attachment=None):
        mb = self.get_report_manager_base()  # get manager base

    def testStep(self, current_test, state: str, reason_of_state: str = "", description: str = "", take_screenshot: bool = False, qty: int = 1, exc_value: BaseException = None):
        mb = self.get_report_manager_base()  # get manager base

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
        mb = self.get_report_manager_base()  # get manager base

        package_name = mb.get_package_name()
        package_cycle = mb.get_package_cycle_number()

        suite_name = mb.get_suite_name()
        suite_cycle = mb.get_suite_cycle_number()

        test_name = current_test.get_name()
        test_cycle = current_test.get_cycle()
        test_usecase = current_test.get_usecase()
        test_duration = current_test.get_duration()
