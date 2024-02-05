import os
import pandas as pd

from typing import Dict

from testipy import get_exec_logger
from testipy.lib_modules.start_arguments import StartArguments
from testipy.reporter.reporters import df_manager as dfm
from testipy.reporter import ReportManager, ReportInterface, PackageDetails, SuiteDetails, TestDetails


_exec_logger = get_exec_logger()


class ReporterExcel(ReportInterface):

    _columns = ["Package", "P#", "Suite", "S#", "Test", "T#", "Usecase", "Level", "State", "Reason", "TestStep", "Qty", "Duration", "Start time", "End time"]

    def __init__(self, rm: ReportManager, sa: StartArguments):
        super().__init__(self.__class__.__name__)
        self.rm = rm

        # create results folder if doesnt exists
        self.__ensure_folder(sa.full_path_results_folder_runtime)

        # full path name
        self._fpn = os.path.join(sa.full_path_results_folder_runtime, f"report.xlsx")

        # create Excel Writer
        self.writer = pd.ExcelWriter(self._fpn, engine='xlsxwriter', datetime_format='yyyy-mm-dd hh:mm:ss.000')

        # DataFrame for testStepCounters
        self._df_step_counters = pd.DataFrame(columns=self._columns)

    def __ensure_folder(self, folder_name):
        try:
            if not os.path.exists(folder_name):
                os.makedirs(folder_name, exist_ok=True)
                _exec_logger.info(f"Created folder {folder_name}")
        except:
            _exec_logger.critical(f"Could not create folder {folder_name}", "ERROR")

    def _create_summarys(self, df):
        # write summarys
        dfm.get_levels_state_summary(df).to_excel(self.writer, index=False, header=True, sheet_name='#Summary')
        dfm.get_package_dummies(df).to_excel(self.writer, index=False, header=True, sheet_name='#PackageSummary')
        dfm.get_suite_dummies(df).to_excel(self.writer, index=False, header=True, sheet_name='#SuiteSummary')
        dfm.get_test_dummies(df).to_excel(self.writer, index=False, header=True, sheet_name='#TestSummary')
        dfm.get_test_ros_summary(df).to_excel(self.writer, index=False, header=True, sheet_name='#TestROS')
        df.to_excel(self.writer, index=False, header=True, sheet_name='#UsecaseLog')

        # write test steps
        for package_name in self._df_step_counters["Package"].unique():
            sheet_name = package_name[:31] if len(package_name) > 31 else package_name
            df_steps = self._df_step_counters[self._df_step_counters["Package"] == package_name]
            df_steps.to_excel(self.writer, index=False, header=True, sheet_name=sheet_name)

        # format cells
        fmt = self.writer.book.add_format({"font_name": "Calibri", "font_size": 9})
        for (name, sheet) in self.writer.sheets.items():
            sheet.set_column('A:Z', None, fmt)

        # save file
        self.writer.close()

    def save_file(self, current_test: TestDetails, data, filename: str):
        pass

    def copy_file(self, current_test: TestDetails, orig_filename: str, dest_filename: str, data):
        pass

    def _startup_(self, selected_tests: Dict):
        df = self.rm.get_selected_tests_as_df()
        df.to_excel(self.writer, index=False, header=True, sheet_name='#SelectedTests')

    def _teardown_(self, end_state):
        self._create_summarys(self.rm.get_df())

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

    # this will serve the purpose only for testSteps, because for tests is done on teardown

    def end_test(self, current_test: TestDetails, ending_state: str, end_reason: str = "", exc_value: BaseException = None):
        # gather info for DataFrame
        package_name = current_test.suite.package.get_name()
        package_cycle = current_test.suite.package.get_cycle()

        suite_name = current_test.get_name()
        suite_cycle = current_test.get_cycle()

        test_name = current_test.get_name()
        test_cycle = current_test.get_cycle()
        test_usecase = current_test.get_usecase()
        test_level = current_test.get_level()

        # testStep counter
        tc = current_test.get_test_step_counters()
        timed_laps = tc.get_timed_laps()
        step_start = tc.get_begin_time()

        for lap in timed_laps:
            self._df_step_counters.loc[len(self._df_step_counters)] = [
                package_name, package_cycle,
                suite_name, suite_cycle,
                test_name, test_cycle, test_usecase, test_level,
                lap.state, lap.reason_of_state, lap.description, lap.qty,
                lap.total_seconds, step_start, lap.timed_all_end
            ]

    def show_status(self, message: str):
        pass

    def show_alert_message(self, message: str):
        pass

    def input_prompt_message(self, message: str, default_value: str = ""):
        pass
