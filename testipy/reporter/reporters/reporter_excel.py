import os
import pandas as pd

from typing import Dict

from testipy.lib_modules.start_arguments import StartArguments
from testipy.reporter.reporters import df_manager as dfm
from testipy.reporter import ReportManager, ReportInterface
from testipy.configs import enums_data


class ReporterExcel(ReportInterface):

    _columns = ["Package", "P#", "Suite", "S#", "Test", "T#", "Usecase", "Level", "State", "Reason", "Qty", "Duration", "Start time", "TestStep", "Timestamp"]

    def __init__(self, rm: ReportManager, sa: StartArguments):
        super().__init__(self.__class__.__name__)
        self.rm = rm

        # create results folder if doesnt exists
        self.__ensure_folder(sa.full_path_results_folder_runtime)

        # full path name
        self._fpn = os.path.join(sa.full_path_results_folder_runtime, f"{sa.project_name}.xlsx")

        # create Excel Writer
        self.writer = pd.ExcelWriter(self._fpn, engine='xlsxwriter', datetime_format='yyyy-mm-dd hh:mm:ss.000')

        # DataFrame for testStepCounters
        self._df_step_counters = pd.DataFrame(columns=self._columns)

    def get_report_manager_base(self):
        return self.rm.get_report_manager_base()

    def __ensure_folder(self, folder_name):
        try:
            if not os.path.exists(folder_name):
                os.makedirs(folder_name, exist_ok=True)
                self.rm._execution_log("INFO", f"Created folder {folder_name}")
        except:
            self.rm._execution_log("CRITICAL", f"Could not create folder {folder_name}", "ERROR")

    def create_summarys(self, df):
        # write summarys
        dfm.get_levels_state_summary(df).to_excel(self.writer, index=False, header=True, sheet_name='#Summary')
        dfm.get_package_dummies(df).to_excel(self.writer, index=False, header=True, sheet_name='#PackageSummary')
        dfm.get_suite_dummies(df).to_excel(self.writer, index=False, header=True, sheet_name='#SuiteSummary')
        dfm.get_test_dummies(df).to_excel(self.writer, index=False, header=True, sheet_name='#TestSummary')
        dfm.get_test_ros_summary(df).to_excel(self.writer, index=False, header=True, sheet_name='#TestROS')
        df.to_excel(self.writer, index=False, header=True, sheet_name='#UsecaseLog')

        # write test steps
        for package_name in self._df_step_counters["Package"].unique():
            sheet_name = package_name[-31] if len(package_name) > 31 else package_name
            df_steps = self._df_step_counters[self._df_step_counters["Package"] == package_name]
            df_steps.to_excel(self.writer, index=False, header=True, sheet_name=sheet_name)

        # format cells
        fmt = self.writer.book.add_format({"font_name": "Calibri", "font_size": 9})
        for (name, sheet) in self.writer.sheets.items():
            sheet.set_column('A:Z', None, fmt)

        # save file
        self.writer.close()

    def save_file(self, current_test, data, filename):
        pass

    def copy_file(self, current_test, orig_filename, dest_filename, data):
        pass

    def __startup__(self, selected_tests: Dict):
        mb = self.get_report_manager_base()
        df = mb.get_selected_tests_as_df()
        df.to_excel(self.writer, index=False, header=True, sheet_name='#SelectedTests')

    def __teardown__(self, end_state):
        self.create_summarys(self.get_report_manager_base().get_df())

    def startPackage(self, package_name: str, package_attr: Dict):
        pass

    def endPackage(self, package_name: str, package_attr: Dict):
        pass

    def startSuite(self, suite_name: str, suite_attr: Dict):
        pass

    def endSuite(self, suite_name: str, suite_attr: Dict):
        pass

    def startTest(self, method_attr: Dict, test_name: str = "", usecase: str = "", description: str = ""):
        pass

    def testInfo(self, current_test, info, level, attachment=None):
        pass

    def testStep(self, current_test, state: str, reason_of_state: str = "", description: str = "", take_screenshot: bool = False, qty: int = 1, exc_value: BaseException = None):
        pass

    def testSkipped(self, current_test, reason_of_state="", exc_value: BaseException = None):
        self.endTest(current_test, enums_data.STATE_SKIPPED, reason_of_state, exc_value)

    def testPassed(self, current_test, reason_of_state="", exc_value: BaseException = None):
        self.endTest(current_test, enums_data.STATE_PASSED, reason_of_state, exc_value)

    def testFailed(self, current_test, reason_of_state="", exc_value: BaseException = None):
        self.endTest(current_test, enums_data.STATE_FAILED, reason_of_state, exc_value)

    def testFailedKnownBug(self, current_test, reason_of_state="", exc_value: BaseException = None):
        self.endTest(current_test, enums_data.STATE_FAILED_KNOWN_BUG, reason_of_state, exc_value)

    def showStatus(self, message: str):
        pass

    def showAlertMessage(self, message: str):
        pass

    def inputPromptMessage(self, message: str, default_value: str = ""):
        pass

    # this will serve the purpose only for testSteps, because for tests is done on teardown
    def endTest(self, current_test, ending_state, end_reason, exc_value: BaseException = None):
        mb = self.get_report_manager_base()

        # gather info for DataFrame
        package_name = mb.get_package_name(False)
        package_cycle = mb.get_package_cycle_number()
        suite_name = mb.get_suite_name(False)
        suite_cycle = mb.get_suite_cycle_number()
        test_name = current_test.get_name()
        test_usecase = current_test.get_usecase()
        test_cycle = current_test.get_cycle()
        test_level = current_test.get_level()

        # testStep counter
        tc = current_test.get_test_step_counters()
        step_start = tc.get_begin_time()

        for (state, qty, etime, ros, test_step, exc_value, time_stamp) in tc.get_timed_laps():
            self._df_step_counters.loc[len(self._df_step_counters)] = [package_name, package_cycle,
                                                                       suite_name, suite_cycle,
                                                                       test_name, test_cycle, test_usecase, test_level,
                                                                       state, ros, qty, etime, step_start,
                                                                       test_step, time_stamp]


"""
        # test ReporterDetails
        mb = self.get_report_manager_base()

        trd = mb.get_test_list()
        
        for test_name in trd:
            tc = StateCounter()
            for test in trd[test_name]:
                tc.inc_states(test.get_counters())

            package_name = mb.get_package_name(False)
            package_cycle = mb.get_package_cycle_number()
            suite_name = mb.get_suite_name(False)
            suite_cycle = mb.get_suite_cycle_number()

            test_total = tc.get_total()
            test_passed_percent = tc.get_state_percentage(STATE_PASSED)
            test_states_qty = tc.get_dict()
            test_ros = tc.get_reason_of_states()

            test_begin = tc.get_begin_time()
            test_end = tc.get_end_time()
            test_duration = tc.get_sum_time_laps()
"""
