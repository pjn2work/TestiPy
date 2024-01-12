import pandas as pd

from typing import Dict, List, Any
from abc import abstractmethod, ABC
from mimetypes import guess_type
from tabulate import tabulate

from testipy.configs import enums_data, default_config
from testipy.helpers import format_duration
from testipy.lib_modules.common_methods import get_current_date_time_ns, get_timestamp, get_datetime_now
from testipy.lib_modules.state_counter import StateCounter


class ReportBase(ABC):
    """
    _all_test_results = {
        "reporter_name": string
        "counters": StateCounter()
        "start_time": datetime
        "end_time": datetime
        "duration": int(seconds)
        "details": class ReporterDetails
        "package_list": {
            "my.package.1": {
                "package_name": "my.package.1"
                "counters": StateCounter()
                "start_time": datetime
                "end_time": datetime
                "duration": int(seconds)
                "details": class ReporterDetails
                "suite_list": {
                    "suite001": {
                        "suite_name": "suite001"
                        "counters": StateCounter()
                        "start_time": datetime
                        "end_time": datetime
                        "duration": int(seconds)
                        "test_list": {
                            "test_name": [ClassTestDetails, ClassTestDetails, ...],
                            "Test Logout": [
                                {
                                    "method_name": "test_logout"
                                    "attr": dict()
                                    "info": [(timestamp, currentTime, level, info, attach), ...]
                                    "counters": StateCounter()
                                    "start_time": datetime
                                    "end_time": datetime
                                    "duration": int(seconds)
                                },
                                {...same test name, different usecase or ncycle...}
                            ]
                        } # end test_list
                    },
                    "suite002": {}
                } # end suite_list
            },
            "another.package.2" = {}
        } # end package_list
    }
    """

    _columns = ["Package", "P#", "Suite", "S#", "Test", "T#", "Level", "State", "Usecase", "Reason", "Steps", "Duration", "Start time", "End time", "TAGs", "Param", "Prio", "Features", "TestNumber", "Description", "TID"]

    def __init__(self, reporter_name):
        self._all_test_results = dict()
        self._all_test_results["details"] = ReportDetails(reporter_name)
        self._all_test_results["package_list"] = dict()

        self._selected_tests: pd.DataFrame = None

        self._current_package: Dict = None
        self._current_suite: Dict = None
        self._current_test: Dict = None

        self.end_state: str = None

        # sequencial counter for test_id
        self._test_id_counter = 0

        # common for all reporters
        self._rm_base: ReportBase = None

        # results stored in da Pandas Dataframe
        self._df = pd.DataFrame(columns=self._columns)

    def set_report_manager_base(self, rm):
        self._rm_base = rm.get_report_manager_base()

    def get_report_manager_base(self):
        if not self._rm_base:
            self._rm_base = self
        return self._rm_base

    # <editor-fold desc="--- Gets ---">
    def get_selected_tests_as_df(self) -> pd.DataFrame:
        return self._selected_tests

    def get_df(self) -> pd.DataFrame:
        return self._df.copy()

    def get_all_test_results(self) -> Dict:
        return self._all_test_results

    def get_reporter_name(self) -> str:
        return self._all_test_results["details"].get_name(False)

    def get_package_name(self, with_cycle_number=False):
        return self._current_package["details"].get_name(with_cycle_number)

    def get_suite_name(self, with_cycle_number=False):
        return self._current_suite["details"].get_name(with_cycle_number)

    def get_full_name(self, current_test, with_cycle_number=False):
        return default_config.separator_package_suite_test.join((self.get_package_name(with_cycle_number),
                                                                 self.get_suite_name(with_cycle_number),
                                                                 current_test.get_name(with_cycle_number)))

    def get_reporter_duration(self):
        return self._all_test_results["details"].get_duration()

    def get_package_duration(self):
        return self._current_package["details"].get_duration()

    def get_suite_duration(self):
        return self._current_suite["details"].get_duration()

    def get_package_cycle_number(self):
        return self._current_package["details"].get_cycle()

    def get_suite_cycle_number(self):
        return self._current_suite["details"].get_cycle()

    def get_reporter_counter(self):
        return self._all_test_results["details"].get_counters()

    def get_package_counter(self):
        return self._current_package["details"].get_counters()

    def get_suite_counter(self):
        return self._current_suite["details"].get_counters()

    def get_reporter_details(self):
        return self._all_test_results["details"]

    def get_package_details(self):
        return self._current_package["details"]

    def get_suite_details(self):
        return self._current_suite["details"]

    def get_test_methods_list_for_current_suite(self) -> Dict:
        return self._current_suite["test_list"]

    def get_suite_list(self) -> Dict:
        return self._current_package["suite_list"]

    def get_package_list(self) -> Dict:
        return self._all_test_results["package_list"]

    def get_current_test(self):
        return self._current_test

    def clear_current_test(self):
        self._current_test = None

    @staticmethod
    def create_attachment(filename, data) -> Dict:
        return {"name": filename,
                "data": data,
                "mime": guess_type(filename)[0] or "application/octet-stream"}
    # </editor-fold>

    @abstractmethod
    def save_file(self, current_test, data, filename) -> Dict:
        attachment = self.create_attachment(filename, data)
        self.testInfo(current_test, f"Saved file '{filename}'", "DEBUG", attachment=attachment)
        return attachment

    @abstractmethod
    def copy_file(self, current_test, orig_filename, dest_filename, data) -> Dict:
        attachment = self.create_attachment(dest_filename, data)
        self.testInfo(current_test, f"Copied file '{orig_filename}' to '{dest_filename}'", "DEBUG", attachment=attachment)
        return attachment

    @abstractmethod
    def __startup__(self, selected_tests: Dict):
        self._selected_tests = pd.DataFrame(selected_tests["data"], columns=selected_tests["headers"])
        return self

    @abstractmethod
    def __teardown__(self, end_state):
        self.end_state = end_state
        self._all_test_results["details"].end_timer()
        return self

    @abstractmethod
    def startPackage(self, package_name):
        if package_name in self._all_test_results["package_list"]:
            self._current_package = self._all_test_results["package_list"][package_name]
            self._current_package["details"].inc_cycle()
        else:
            self._current_package = dict()
            self._current_package["details"] = ReportDetails(package_name)
            self._current_package["suite_list"] = dict()

            self._all_test_results["package_list"][package_name] = self._current_package
        return self

    @abstractmethod
    def endPackage(self):
        self._current_package["details"].end_timer()
        return self

    @abstractmethod
    def startSuite(self, suite_name, attr=None):
        if suite_name in self._current_package["suite_list"]:
            self._current_suite = self._current_package["suite_list"][suite_name]
            self._current_suite["details"].inc_cycle()
        else:
            self._current_suite = dict()
            self._current_suite["details"] = ReportDetails(suite_name, attr)
            self._current_suite["test_list"] = dict() # it will be a dict of "test_name": [TestDetails, TestDetails, (current_test), ...]

            self._current_package["suite_list"][suite_name] = self._current_suite
        return self

    @abstractmethod
    def endSuite(self):
        self._current_suite["details"].end_timer()
        return self

    def __create_new_test(self, attr, test_name, usecase, description):
        if attr and isinstance(attr, Dict):
            self._test_id_counter += 1

            attr = dict(attr)
            attr["test_id"] = self._test_id_counter
            attr["test_comment"] = str(description) if description else attr["test_comment"]
            attr["test_usecase"] = usecase

            return TestDetails(test_name, attr)

        raise ValueError("When starting a new test, you must pass your MethodAttributes (dict), received as the first parameter on your test method.")

    @abstractmethod
    def startTest(self, method_attr: Dict, test_name: str = "", usecase: str = "", description: str = ""):
        self._current_test = current_test = self.__create_new_test(method_attr, test_name, usecase, description)
        test_name = current_test.get_name()

        if test_name in self._current_suite["test_list"]:
            self._current_suite["test_list"][test_name].append(current_test)
            current_test.set_cycle(len(self._current_suite["test_list"][test_name]))
        else:
            self._current_suite["test_list"][test_name] = [current_test]

        return current_test

    @abstractmethod
    def testInfo(self, current_test, info, level, attachment=None):
        current_test.add_info(get_timestamp(), get_current_date_time_ns(), level, info, attachment)
        return self

    @abstractmethod
    def testStep(self, current_test, state: str, reason_of_state: str = "", description: str = "", take_screenshot: bool = False, qty: int = 1, exc_value: BaseException = None):
        current_test.testStep(state, reason_of_state=reason_of_state, description=description, qty=qty, exc_value=exc_value)

    @abstractmethod
    def testSkipped(self, current_test, reason_of_state="", exc_value: BaseException = None):
        return self.__endTest(current_test, enums_data.STATE_SKIPPED, reason_of_state, exc_value)

    @abstractmethod
    def testPassed(self, current_test, reason_of_state="", exc_value: BaseException = None):
        return self.__endTest(current_test, enums_data.STATE_PASSED, reason_of_state, exc_value)

    @abstractmethod
    def testFailed(self, current_test, reason_of_state="", exc_value: BaseException = None):
        return self.__endTest(current_test, enums_data.STATE_FAILED, reason_of_state, exc_value)

    @abstractmethod
    def testFailedKnownBug(self, current_test, reason_of_state="", exc_value: BaseException = None):
        return self.__endTest(current_test, enums_data.STATE_FAILED_KNOWN_BUG, reason_of_state, exc_value)

    @abstractmethod
    def showStatus(self, message: str):
        pass

    @abstractmethod
    def showAlertMessage(self, message: str):
        pass

    @abstractmethod
    def inputPromptMessage(self, message: str, default_value: str = ""):
        pass

    def __endTest(self, current_test, state, reason_of_state, exc_value: BaseException = None):
        # finish current test
        current_test.end_timer()
        current_test.counters.inc_state(state, reason_of_state=reason_of_state, description="end test", qty=1, exc_value=exc_value)

        # update package and suite
        self.__update_package_suite_test_counters(state, reason_of_state)

        # gather info for DataFrame
        package_name = self.get_package_name(False)
        package_cycle = self.get_package_cycle_number()
        suite_name = self.get_suite_name(False)
        suite_cycle = self.get_suite_cycle_number()
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

        # append DataFrame
        self._df.loc[test_id] = [package_name, package_cycle, suite_name, suite_cycle, test_name, test_cycle,
                                       test_level, test_state, test_usecase, test_end_reason, test_number_test_steps,
                                       test_duration, test_start, test_end, test_tags, test_parameters,
                                       test_prio, test_features, test_number, test_comment, test_id]

        return self

    def __update_package_suite_test_counters(self, state, reason_of_state):
        self._current_suite["details"].counters.inc_state(state, reason_of_state=reason_of_state, description="update suite counters", qty=1)
        self._current_package["details"].counters.inc_state(state, reason_of_state=reason_of_state, description="update package counters", qty=1)
        self._all_test_results["details"].counters.inc_state(state, reason_of_state=reason_of_state, description="update global counters", qty=1)


class ReportDetails:

    def __init__(self, name: str, attr: Dict[str, Any] = None):
        self.attr = attr or {enums_data.TAG_NAME: name}
        self.attr["cycle_number"] = 1
        self.name = name or attr[enums_data.TAG_NAME]
        self.counters = StateCounter()
        self.start_time = get_datetime_now()
        self.end_time = None

    def get_attributes(self) -> Dict:
        return self.attr

    def get_cycle(self) -> int:
        return self.attr["cycle_number"]

    def set_cycle(self, current_cycle: int):
        self.attr["cycle_number"] = current_cycle
        return self

    def inc_cycle(self):
        self.attr["cycle_number"] += 1
        self.end_time = None
        return self

    def end_timer(self):
        self.end_time = get_datetime_now()
        return self

    def get_name(self, with_cycle_number=False) -> str:
        return f"{self.name}{default_config.separator_cycle}{self.get_cycle()}" if with_cycle_number else self.name

    def get_counters(self) -> StateCounter:
        return self.counters

    def get_starttime(self):
        return self.start_time

    def get_endtime(self):
        return self.end_time

    def get_duration(self) -> int:
        return self.duration

    @property
    def duration(self):
        if not self.end_time:
            return None
        return (self.end_time - self.start_time).total_seconds()

    # ex: suiteCertificates#21 ["PASSED":12, "FAILED": 2, "SKIPPED": 0, "Total": 14] took
    def __str__(self):
        sname = self.get_name(True)

        if self.duration:
            return "{} {:.2f}% [{}] took {}".format(sname, self.counters.get_state_percentage(enums_data.STATE_PASSED), self.counters, format_duration(self.duration))

        return sname


class TestDetails(ReportDetails):

    def __init__(self, test_name: str, attr: Dict[str, Any]):
        super().__init__(test_name, attr)
        self.attr["test_name"] = self.name
        self._info = list()
        self._test_step = StateCounter()

    def get_method_id(self) -> int:
        return self.attr["method_id"]

    def get_test_id(self) -> int:
        return self.attr["test_id"]

    def get_tags(self) -> List:
        return list(self.attr[enums_data.TAG_TAG])

    def get_level(self) -> int:
        return self.attr[enums_data.TAG_LEVEL]

    def get_prio(self) -> int:
        return self.attr[enums_data.TAG_PRIO]

    def get_features(self) -> str:
        return self.attr[enums_data.TAG_FEATURES]

    def get_comment(self) -> str:
        return self.attr.get("test_comment", "") or ""

    def get_test_number(self) -> str:
        return self.attr[enums_data.TAG_TESTNUMBER]

    def get_test_param_parameter(self) -> Dict:
        return self.attr["param"]

    def get_test_name(self, with_cycle_number=False) -> str:
        return self.attr["test_name"]

    def get_usecase(self) -> str:
        return self.attr["test_usecase"]

    def add_info(self, ts, current_time, level, info, attachment):
        self._info.append((ts, current_time, str(level).upper(), info, attachment))
        return self

    def get_info(self) -> List:
        return list(self._info)

    def get_number_test_steps(self) -> int:
        return self._test_step.get_total()

    def testStep(self, state: str, reason_of_state: str = "", description: str = "", qty: int = 1, exc_value: BaseException = None):
        self._test_step.inc_state(state, reason_of_state=reason_of_state, description=description, qty=qty, exc_value=exc_value)
        return self

    def get_new_state_counter(self) -> StateCounter:
        return StateCounter()

    def get_test_step_counters(self) -> StateCounter:
        return self._test_step

    def get_test_step_counters_tabulate(self, tablefmt="simple") -> str:
        # reverse timed_laps row order, with timestamp being the first column
        tl = [(str(lap.timed_all_end)[:23], lap.state, lap.qty, lap.total_seconds, lap.reason_of_state, lap.description) for lap in self.get_test_step_counters().get_timed_laps()]

        return tabulate(tl, headers=("Timestamp", "State", "Qty", "Elapsed", "Reason of State", "Step"),
                 floatfmt=".4f", tablefmt=tablefmt)

    def set_next_step_starting_from_now(self):
        self._test_step.set_state_starting_from_now()
        return self

    def get_state(self):
        return super().get_counters().get_last_state() or self._test_step.get_last_state()

    def is_passed(self):
        return self.get_state() == enums_data.STATE_PASSED

    def is_failed(self):
        return self.get_state() in [enums_data.STATE_FAILED, enums_data.STATE_FAILED_KNOWN_BUG]

    def is_skipped(self):
        return self.get_state() == enums_data.STATE_SKIPPED

    def __str__(self):
        res = f"meid={self.get_method_id()} | teid={self.get_test_id()} | prio={self.get_prio()} | {self.get_name(True)}"
        if usecase := self.get_usecase():
            res += f" | {usecase}"
        if state := self.get_state():
            res += f" | {state=}"
        return res

    def __repr__(self):
        return f"{self.__class__.__module__}.{self.__class__.__name__}(meid={self.get_method_id()}, teid={self.get_test_id()}, prio={self.get_prio()}, {self.get_name(True)}, status={self.get_state()})"
