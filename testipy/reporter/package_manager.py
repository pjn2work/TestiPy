from __future__ import annotations

from typing import Dict, List, Set
from tabulate import tabulate

from testipy.configs import enums_data, default_config
from testipy.lib_modules.common_methods import get_datetime_now
from testipy.lib_modules.state_counter import StateCounter


class CommonDetails:
    def __init__(self, name: str, attr: Dict):
        self.name: str = name
        self.attr: Dict = attr

        self.cycle_number: int = 1
        self.state_counter = StateCounter()
        self.start_time = get_datetime_now()
        self.end_time = None

    def get_cycle(self) -> int:
        return self.cycle_number

    def get_starttime(self):
        return self.start_time

    def get_endtime(self):
        return self.end_time

    def get_duration(self) -> float:
        if not self.end_time:
            self.end_time = get_datetime_now()
        return (self.end_time - self.start_time).total_seconds()

    def get_name(self, with_cycle_number=False) -> str:
        return f"{self.name}{default_config.separator_cycle}{self.get_cycle()}" if with_cycle_number else self.name

    def get_attr(self):
        return self.attr

    def get_counters(self) -> StateCounter:
        return self.state_counter


class PackageDetails(CommonDetails):
    def __init__(self, parent: PackageManager, package_name: str, package_attr: Dict):
        super(PackageDetails, self).__init__(package_name or package_attr["@NAME"], package_attr)

        self.parent = parent
        self.suite_manager: SuiteManager = SuiteManager(self)

    def endPackage(self):
        self.parent.end_time = self.end_time = get_datetime_now()

    def startSuite(self, suite_name: str, suite_attr: Dict) -> SuiteDetails:
        return self.suite_manager.startSuite(suite_name, suite_attr)

    def update_package_suite_counters(self, state: str, reason_of_state: str):
        self.state_counter.inc_state(state, reason_of_state=reason_of_state, description="update package counters")
        self.parent.update_package_suite_counters(state, reason_of_state)


class SuiteDetails(CommonDetails):
    def __init__(self, parent: PackageDetails, suite_name: str, suite_attr: Dict):
        super(SuiteDetails, self).__init__(suite_name or suite_attr["@NAME"], suite_attr)

        self.package = parent
        self.test_state_by_prio: Dict[int, Set] = dict()  # {2: {"PASS", "SKIP"}, 10: ...
        self.test_manager: TestManager = TestManager(self)

    def endSuite(self):
        self.end_time = get_datetime_now()

    def startTest(self, test_name: str, test_attr: Dict) -> TestDetails:
        current_test = self.test_manager.startTest(test_name, test_attr)
        self.package.parent.add_test_by_id(current_test)
        return current_test

    def update_package_suite_counters(self, prio: int, state: str, reason_of_state: str):
        if prio not in self.test_state_by_prio:
            self.test_state_by_prio[prio] = set()
        self.test_state_by_prio[prio].add(state)

        self.state_counter.inc_state(state, reason_of_state=reason_of_state, description="update suite counters")
        self.package.update_package_suite_counters(state, reason_of_state)

    def get_test_state_by_prio(self, prio: int) -> Set[str]:
        return self.test_state_by_prio.get(prio, {})

    def get_tests_by_meid(self, test_method_id: int) -> List[TestDetails]:
        return self.test_manager.get_tests_by_meid(test_method_id)

    def get_tests_running_by_meid(self, test_method_id: int) -> List[TestDetails]:
        return self.test_manager.get_tests_running_by_meid(test_method_id)


class TestDetails(CommonDetails):
    def __init__(self, parent: SuiteDetails, test_name: str, test_attr: Dict):
        super(TestDetails, self).__init__(test_name or test_attr["test_name"], test_attr)

        self.suite = parent
        self._info = list()
        self._test_step = StateCounter()

    def endTest(self, state: str, reason_of_state: str, exc_value: BaseException = None):
        self.end_time = get_datetime_now()
        self.state_counter.inc_state(state, reason_of_state=reason_of_state, description="end test", exc_value=exc_value)

        self.suite.update_package_suite_counters(self.get_prio(), state, reason_of_state)
        self.suite.test_manager.remove_test_running(self)

    def get_usecase(self) -> str:
        return self.attr["test_usecase"]

    def get_method_id(self) -> int:
        return self.attr["method_id"]

    def get_test_id(self) -> int:
        return self.attr["test_id"]

    def get_comment(self) -> str:
        return self.attr.get("test_comment", "")

    def get_test_param_parameter(self):
        return self.attr.get("param")

    def get_test_number(self) -> str:
        return self.attr.get(enums_data.TAG_TESTNUMBER, "")

    def get_tags(self) -> List:
        if enums_data.TAG_TAG not in self.attr:
            return []
        return list(self.attr[enums_data.TAG_TAG])

    def get_level(self) -> int:
        return self.attr.get(enums_data.TAG_LEVEL, 0)

    def get_prio(self) -> int:
        return self.attr.get(enums_data.TAG_PRIO, 999)

    def get_features(self) -> str:
        return self.attr.get(enums_data.TAG_FEATURES, "")

    def add_info(self, ts: int, current_time: str, level: str, info: str, attachment: Dict):
        self._info.append((ts, current_time, str(level).upper(), info, attachment))
        return self

    def get_attributes(self) -> Dict:
        return self.attr

    def get_info(self) -> List:
        return list(self._info)

    def get_number_test_steps(self) -> int:
        return self._test_step.get_total()

    def testStep(self, state: str, reason_of_state: str = "", description: str = "", qty: int = 1, exc_value: BaseException = None):
        self._test_step.inc_state(state, reason_of_state=reason_of_state, description=description, qty=qty, exc_value=exc_value)

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
        return self.state_counter.get_last_state() or self._test_step.get_last_state()

    def is_passed(self):
        return self.get_state() == enums_data.STATE_PASSED

    def is_failed(self):
        return self.get_state() in [enums_data.STATE_FAILED, enums_data.STATE_FAILED_KNOWN_BUG]

    def is_skipped(self):
        return self.get_state() == enums_data.STATE_SKIPPED

    def get_package(self) -> PackageDetails:
        return self.suite.package

    def get_suite(self) -> SuiteDetails:
        return self.suite

    def __str__(self):
        res = f"meid={self.get_method_id()} | teid={self.get_test_id()} | prio={self.get_prio()} | {self.get_name()}"
        if usecase := self.get_usecase():
            res += f" | {usecase}"
        if state := self.get_state():
            res += f" | {state=}"
        return res

    def __repr__(self):
        return f"{self.__class__.__module__}.{self.__class__.__name__}(meid={self.get_method_id()}, teid={self.get_test_id()}, prio={self.get_prio()}, {self.get_name(True)}, status={self.get_state()})"


class PackageManager:
    def __init__(self):
        self._package_by_name: Dict[str, PackageDetails] = dict()
        self.state_counter = StateCounter()
        self.start_time = None
        self.end_time = None
        self._test_by_id: Dict[int, TestDetails] = dict()

    def startPackage(self, package_name: str, package_attr: Dict) -> PackageDetails:
        if self.start_time is None:
            self.start_time = get_datetime_now()

        package_name = package_name if package_name else package_attr["package_name"]
        if package_name in self._package_by_name:
            self._package_by_name[package_name].cycle_number += 1
        else:
            self._package_by_name[package_name] = PackageDetails(self, package_name, package_attr)
        return self._package_by_name[package_name]

    def update_package_suite_counters(self, state: str, reason_of_state: str):
        self.state_counter.inc_state(state, reason_of_state=reason_of_state, description="update global counters")

    def get_duration(self) -> float:
        if not self.end_time:
            self.end_time = get_datetime_now()
        return (self.end_time - self.start_time).total_seconds()

    def get_package_by_name(self, package_name: str = "", package_attr: Dict = "") -> PackageDetails:
        package_name = package_name if package_name else package_attr["package_name"]
        return self._package_by_name.get(package_name)

    def add_test_by_id(self, td: TestDetails):
        self._test_by_id[td.get_test_id()] = td

    def get_test_by_id(self, tid: int) -> TestDetails:
        return self._test_by_id[tid]


class SuiteManager:
    def __init__(self, parent: PackageDetails):
        self.parent = parent
        self._suite_by_id: Dict[int, SuiteDetails] = dict()

    def startSuite(self, suite_name: str, suite_attr: Dict) -> SuiteDetails:
        suite_id = suite_attr["suite_id"]
        if suite_id in self._suite_by_id:
            self._suite_by_id[suite_id].cycle_number += 1
            # clear for new re-run
            self._suite_by_id[suite_id].test_state_by_prio.clear()
            self._suite_by_id[suite_id].test_manager._tests_by_meid.clear()
        else:
            self._suite_by_id[suite_id] = SuiteDetails(self.parent, suite_name, suite_attr)

        return self._suite_by_id[suite_id]

    def get_suite_by_id(self, _id: int) -> SuiteDetails:
        return self._suite_by_id.get(_id)


class TestManager:
    def __init__(self, parent: SuiteDetails):
        self.parent = parent
        self._qty_test_by_name: Dict[str, int] = dict()
        self._tests_by_meid: Dict[int, List[TestDetails]] = dict()
        self._tests_running_by_meid: Dict[int, List[TestDetails]] = dict()

    def startTest(self, test_name: str, test_attr: Dict):
        test_name = test_name if test_name else test_attr["test_name"]
        current_test = TestDetails(self.parent, test_name, test_attr)

        if test_name in self._qty_test_by_name:
            self._qty_test_by_name[test_name] += 1
            current_test.cycle_number = self._qty_test_by_name[test_name]
        else:
            self._qty_test_by_name[test_name] = 1

        meid = current_test.get_method_id()

        if meid in self._tests_by_meid:
            self._tests_by_meid[meid].append(current_test)
            self._tests_running_by_meid[meid].append(current_test)
        else:
            self._tests_by_meid[meid] = [current_test]
            self._tests_running_by_meid[meid] = [current_test]

        return current_test

    def remove_test_running(self, current_test: TestDetails):
        meid = current_test.get_method_id()
        self._tests_running_by_meid[meid].remove(current_test)

    def get_tests_by_meid(self, test_method_id: int) -> List[TestDetails]:
        return self._tests_by_meid.get(test_method_id, [])

    def get_tests_running_by_meid(self, test_method_id: int) -> List[TestDetails]:
        return self._tests_running_by_meid.get(test_method_id, [])
