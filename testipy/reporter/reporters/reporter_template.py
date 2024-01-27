from typing import Dict

from testipy.lib_modules.start_arguments import StartArguments
from testipy.reporter import ReportManager, ReportInterface, PackageDetails, SuiteDetails, TestDetails


class ReporterTemplate(ReportInterface):

    def __init__(self, rm: ReportManager, sa: StartArguments):
        super().__init__(self.__class__.__name__)
        self.rm = rm
        self.sa = sa

    def save_file(self, current_test: TestDetails, data, filename: str):
        pass

    def copy_file(self, current_test: TestDetails, orig_filename: str, dest_filename: str, data):
        pass

    def _startup_(self, selected_tests: Dict):
        pass

    def _teardown_(self, end_state: str):
        pass

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
        package_name = current_test.suite.package.get_name()
        package_cycle = current_test.suite.package.get_cycle()

        suite_name = current_test.get_name()
        suite_cycle = current_test.get_cycle()

        test_method_id = current_test.get_method_id()
        test_id = current_test.get_test_id()

        test_name = current_test.get_name()
        test_cycle = current_test.get_cycle()
        test_usecase = current_test.get_usecase()
        test_full_name = current_test.get_full_name(with_cycle_number=True)

        test_duration = current_test.get_duration()
        test_start = current_test.get_starttime()
        test_end = current_test.get_endtime()
        test_counters = current_test.get_counters()
        test_step_counters = current_test.get_test_step_counters()

        test_tags = " ".join(current_test.get_tags())
        test_level = current_test.get_level()
        test_prio = current_test.get_prio()
        test_parameters = str(current_test.get_test_param_parameter())
        test_features = current_test.get_features()
        test_number = current_test.get_test_number()
        test_comment = current_test.get_comment()

    def show_status(self, message: str):
        pass

    def show_alert_message(self, message: str):
        pass

    def input_prompt_message(self, message: str, default_value: str = ""):
        pass
