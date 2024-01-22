from typing import Dict

from testipy.lib_modules.start_arguments import StartArguments
from testipy.reporter import ReportManager, ReportInterface, PackageDetails, SuiteDetails, TestDetails


class ReporterTemplate(ReportInterface):

    def __init__(self, rm: ReportManager, sa: StartArguments):
        super().__init__(self.__class__.__name__)
        self.rm = rm
        self.sa = sa

    def get_report_manager_base(self):
        return self.rm.get_report_manager_base()

    def save_file(self, current_test, data, filename):
        pass

    def copy_file(self, current_test, orig_filename, dest_filename, data):
        pass

    def __startup__(self, selected_tests: Dict):
        rmb = self.get_report_manager_base()

    def __teardown__(self, end_state: str):
        rmb = self.get_report_manager_base()

    def startPackage(self, package_name: str, package_attr: Dict):
        rmb = self.get_report_manager_base()

    def endPackage(self, pd: PackageDetails):
        rmb = self.get_report_manager_base()

    def startSuite(self, pd: PackageDetails, suite_name: str, suite_attr: Dict):
        rmb = self.get_report_manager_base()

    def endSuite(self, sd: SuiteDetails):
        rmb = self.get_report_manager_base()

    def startTest(self, method_attr: Dict, test_name: str = "", usecase: str = "", description: str = ""):
        rmb = self.get_report_manager_base()

    def testInfo(self, current_test, info, level, attachment=None):
        rmb = self.get_report_manager_base()

    def testStep(self, current_test, state: str, reason_of_state: str = "", description: str = "", take_screenshot: bool = False, qty: int = 1, exc_value: BaseException = None):
        rmb = self.get_report_manager_base()

    def endTest(self, current_test, ending_state: str, end_reason: str = "", exc_value: BaseException = None):
        rmb = self.get_report_manager_base()

        package_name = rmb.get_package_name()
        package_cycle = rmb.get_package_cycle_number()

        suite_name = rmb.get_suite_name()
        suite_cycle = rmb.get_suite_cycle_number()

        test_name = current_test.get_name()
        test_cycle = current_test.get_cycle()
        test_usecase = current_test.get_usecase()

        test_duration = current_test.get_duration()
        test_start = current_test.get_starttime()
        test_end = current_test.get_endtime()

        test_tags = " ".join(current_test.get_tags())
        test_level = current_test.get_level()
        test_prio = current_test.get_prio()
        test_parameters = str(current_test.get_test_param_parameter())
        test_features = current_test.get_features()
        test_number = current_test.get_test_number()
        test_comment = current_test.get_comment()

    def showStatus(self, message: str):
        pass

    def showAlertMessage(self, message: str):
        pass

    def inputPromptMessage(self, message: str, default_value: str = ""):
        pass
