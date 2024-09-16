from __future__ import annotations

import pandas as pd

from typing import Dict, List
from mimetypes import guess_type

from testipy.configs import enums_data, default_config
from testipy.engine.models import PackageAttr, SuiteAttr, TestMethodAttr
from testipy.reporter.report_interfaces import ReportInterface
from testipy.lib_modules.common_methods import get_current_date_time_ns, get_timestamp
from testipy.reporter.package_manager import PackageManager, PackageDetails, SuiteDetails, TestDetails


class ReportBase(ReportInterface):

    _df_columns = ["Package", "P#", "Suite", "S#", "Test", "T#", "Level", "State", "Usecase", "Reason", "Steps", "Duration", "Start time", "End time", "TAGs", "Param", "Prio", "Features", "TestNumber", "Description", "TID"]

    def __init__(self, reporter_name):
        super().__init__(reporter_name)

        self._selected_tests: List[PackageAttr] = None
        self._selected_tests_as_df: pd.DataFrame = None
        self._selected_tests_as_dict: Dict = None
        self.end_state: str = None

        # manage counters for packages/suites/tests
        self.pm = PackageManager()

        # sequencial counter for test_id
        self._test_id_counter = 0

        # results stored in da Pandas Dataframe
        self._df = pd.DataFrame(columns=self._df_columns)

    # <editor-fold desc="--- Gets ---">
    def get_selected_tests(self) -> List[PackageAttr]:
        return self._selected_tests

    def get_selected_tests_as_df(self) -> pd.DataFrame:
        return self._selected_tests_as_df

    def get_selected_tests_as_dict(self) -> Dict[str, List]:
        return self._selected_tests_as_dict

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

    def _startup_(self, selected_tests: List[PackageAttr]):
        self._selected_tests = selected_tests
        self._selected_tests_as_dict = format_test_structure_for_reporters(selected_tests)
        self._selected_tests_as_df = pd.DataFrame(self._selected_tests_as_dict["data"], columns=self._selected_tests_as_dict["headers"])

    def _teardown_(self, end_state):
        totals = self.pm.state_counter
        total_failed = sum([totals[state] for state in default_config.count_as_failed_states])
        self.end_state, _ = (enums_data.STATE_FAILED, "") if total_failed > 0 else totals.get_state_by_severity()

    def startPackage(self, package_attr: PackageAttr, package_name: str) -> PackageDetails:
        if package_attr is None:
            package_attr = PackageAttr(package_name)
        return self.pm.startPackage(package_attr, package_name)

    def start_package(self, pd: PackageDetails):
        pass

    def end_package(self, pd: PackageDetails):
        pd.endPackage()

    def startSuite(self, pd: PackageDetails, suite_attr: SuiteAttr, suite_name: str) -> SuiteDetails:
        if suite_attr is None:
            suite_attr = SuiteAttr(pd.package_attr, "auto.created", suite_name)
        return pd.startSuite(suite_attr, suite_name)

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

    def startTest(self, sd: SuiteDetails, test_method_attr: TestMethodAttr, test_name: str, usecase: str, description: str) -> TestDetails:
        if sd is None:
            raise ValueError("When starting a new test you must have SuiteDetails, received as the first parameter on your test method.")

        test_method_attr = test_method_attr or sd.current_test_method_attr
        if test_method_attr is None:
            test_method_attr = TestMethodAttr(sd.suite_attr, method_name="_none_", name=test_name)
        sd.set_current_test_method_attr(test_method_attr)

        self._test_id_counter += 1

        current_test: TestDetails = sd.startTest(test_name)
        current_test.test_id = self._test_id_counter
        current_test.test_usecase = str(usecase)
        current_test.test_comment = str(description) if description else test_method_attr.comment

        return current_test

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


def format_test_structure_for_reporters(selected_tests: List[PackageAttr]) -> Dict:
    formatted_test_list = []

    for package_attr in selected_tests:
        package_name = package_attr.package_name

        for suite_attr in package_attr.suite_attr_list:
            suite_name = suite_attr.name
            suite_prio = suite_attr.prio

            for test_method in suite_attr.test_method_attr_list:
                method_id = test_method.method_id
                test_name = test_method.name
                test_prio = test_method.prio
                test_level = test_method.level
                test_tags = " ".join(test_method.tags)
                test_features = test_method.features
                test_number = test_method.test_number
                test_comment = test_method.comment

                formatted_test_list.append(
                    [method_id, package_name, suite_prio, suite_name, test_prio, test_name, test_level, test_tags,
                     test_features, test_number, test_comment])

    return dict(
        headers=["meid", "Package", "Sp", "Suite", "Tp", "Test", "Level", "TAGs", "Features", "Number", "Description"],
        data=formatted_test_list
    )
