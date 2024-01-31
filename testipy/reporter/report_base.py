from __future__ import annotations

import pandas as pd

from typing import Dict
from mimetypes import guess_type

from testipy.configs import enums_data, default_config
from testipy.reporter.report_interfaces import ReportInterface
from testipy.lib_modules.common_methods import get_current_date_time_ns, get_timestamp
from testipy.reporter.package_manager import PackageManager, PackageDetails, SuiteDetails, TestDetails


class ReportBase(ReportInterface):

    _df_columns = ["Package", "P#", "Suite", "S#", "Test", "T#", "Level", "State", "Usecase", "Reason", "Steps", "Duration", "Start time", "End time", "TAGs", "Param", "Prio", "Features", "TestNumber", "Description", "TID"]

    def __init__(self, reporter_name):
        super().__init__(reporter_name)

        self._selected_tests: pd.DataFrame = None
        self.end_state: str = None

        # manage counters for packages/suites/tests
        self.pm = PackageManager()

        # sequencial counter for test_id
        self._test_id_counter = 0

        # results stored in da Pandas Dataframe
        self._df = pd.DataFrame(columns=self._df_columns)

    # <editor-fold desc="--- Gets ---">
    def get_selected_tests_as_df(self) -> pd.DataFrame:
        return self._selected_tests

    def get_df(self) -> pd.DataFrame:
        return self._df.copy()

    @staticmethod
    def create_attachment(filename, data) -> Dict:
        return {"name": filename,
                "data": data,
                "mime": guess_type(filename)[0] or "application/octet-stream"}
    # </editor-fold>

    # <editor-fold desc="--- Common functions starts here ---">

    def save_file(self, current_test: TestDetails, data, filename: str) -> Dict:
        return self.create_attachment(filename, data)

    def copy_file(self, current_test: TestDetails, orig_filename: str, dest_filename: str, data) -> Dict:
        return self.create_attachment(dest_filename, data)

    def _startup_(self, selected_tests: Dict):
        self._selected_tests = pd.DataFrame(selected_tests["data"], columns=selected_tests["headers"])

    def _teardown_(self, end_state):
        totals = self.pm.state_counter
        total_failed = sum([totals[state] for state in default_config.count_as_failed_states])
        self.end_state, _ = (enums_data.STATE_FAILED, "") if total_failed > 0 else totals.get_state_by_severity()

    def startPackage(self, package_name: str, package_attr: Dict) -> PackageDetails:
        return self.pm.startPackage(package_name, package_attr)

    def start_package(self, pd: PackageDetails):
        pass

    def end_package(self, pd: PackageDetails):
        pd.endPackage()

    def startSuite(self, pd: PackageDetails, suite_name: str, suite_attr: Dict) -> SuiteDetails:
        return pd.startSuite(suite_name, suite_attr)

    def start_suite(self, sd: SuiteDetails):
        pass

    def end_suite(self, sd: SuiteDetails):
        sd.endSuite()

        # update DataFrame with all ended tests for this suite
        df_size = self._df.shape[0]
        new_rows = pd.DataFrame(sd.rb_test_result_rows,
                                columns=self._df_columns,
                                index=range(df_size, df_size + len(sd.rb_test_result_rows)))
        self._df = new_rows if df_size == 0 else pd.concat(
            [self._df, new_rows], axis=0, join="outer", ignore_index=True, verify_integrity=False, copy=False)

        # clear list since they were added to DataFrame
        sd.rb_test_result_rows.clear()

    def startTest(self, method_attr: Dict, test_name: str = "", usecase: str = "", description: str = "") -> TestDetails:
        if method_attr and isinstance(method_attr, Dict):
            self._test_id_counter += 1

            test_attr = dict(method_attr)
            test_attr["test_id"] = self._test_id_counter
            test_attr["test_name"] = test_name or test_attr["@NAME"]
            test_attr["test_comment"] = str(description) if description else test_attr.get("test_comment", "")
            test_attr["test_usecase"] = str(usecase)

            sd: SuiteDetails = test_attr.get("suite_details")
            if sd is None:
                raise ValueError("When starting a new test, you must have in your MethodAttributes (dict) 'suite_details'." + str(test_attr))

            del test_attr["suite_details"]
            return sd.startTest(test_name, test_attr)

        raise ValueError("When starting a new test, you must pass your MethodAttributes (dict), received as the first parameter on your test method.")

    def start_test(self, current_test: TestDetails):
        pass

    def test_info(self, current_test, info, level, attachment=None):
        current_test.add_info(get_timestamp(), get_current_date_time_ns(), level, info, attachment)

    def test_step(self, current_test, state: str, reason_of_state: str = "", description: str = "", take_screenshot: bool = False, qty: int = 1, exc_value: BaseException = None):
        current_test.test_step(state, reason_of_state=reason_of_state, description=description, qty=qty, exc_value=exc_value)

    def end_test(self, current_test: TestDetails, state: str, reason_of_state: str, exc_value: BaseException = None):
        # finish current test
        current_test.endTest(state, reason_of_state, exc_value)

        # gather info for DataFrame
        package_name = current_test.suite.package.get_name(False)
        package_cycle = current_test.suite.package.get_cycle()
        suite_name = current_test.suite.get_name(False)
        suite_cycle = current_test.suite.get_cycle()
        test_name = current_test.get_name()
        test_cycle = current_test.get_cycle()
        test_usecase = current_test.get_usecase()
        test_number_test_steps = current_test.get_number_test_steps()

        test_state = current_test.get_counters().get_last_state()
        test_end_reason = current_test.get_counters().get_last_reason_of_state()

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
        test_id = current_test.get_test_id()

        # new row to append to DataFrame
        row = [package_name, package_cycle, suite_name, suite_cycle, test_name, test_cycle,
               test_level, test_state, test_usecase, test_end_reason, test_number_test_steps,
               test_duration, test_start, test_end, test_tags, test_parameters,
               test_prio, test_features, test_number, test_comment, test_id]

        # row will be appended once the suite ends
        current_test.suite.rb_test_result_rows.append(row)

    def show_status(self, message: str):
        pass

    def show_alert_message(self, message: str):
        pass

    def input_prompt_message(self, message: str, default_value: str = ""):
        pass

    # </editor-fold>
