from __future__ import annotations

from abc import abstractmethod, ABC
from collections import OrderedDict
from enum import Enum
from typing import Union, Dict, List, Tuple

from testipy.configs import enums_data
from testipy.reporter.report_base import TestDetails
from testipy.reporter.report_manager import ReportManager
from testipy.helpers import get_traceback_tabulate, load_config, left_update_dict, prettify
from testipy.helpers.handle_assertions import ExpectedError, SkipTestError


class RunMode(Enum):
    SCENARIOS_AS_TESTS__USECASES_AS_TESTSTEPS = 1
    SCENARIO__USECASES_AS_TESTS = 2
    USECASES_AS_TESTS = 3

    @staticmethod
    def decode(value: Union[int, str, RunMode]) -> RunMode:
        if isinstance(value, RunMode):
            return value
        if isinstance(value, int):
            return RunMode(value)
        if isinstance(value, str):
            return RunMode[value]
        raise TypeError(f"Unknown RunMode: {type(value)} - {value}")


class ExecutionToolbox(ABC):
    @abstractmethod
    def execute(self, rm: ReportManager, current_test: TestDetails, exec_method, usecase: Dict, usecase_name: str, st: SafeTry):
        pass

    @abstractmethod
    def clear_last_execution(self):
        pass


class DataReader:
    """
    TAG_NAME_1:

        _usecases_:

            my_test_1:
              _exec_method_: create_user
              _description_: Enter my test description here
              save_name: my_var_1
              params:
                data:
                  name: John
                  age: 41

            my_test_2:
              _exec_method_: create_user
              _description_: Enter my test description here
              save_name: my_var_2
              params:
                data:
                  name: Peter
                  age: Ten
              control:
                expected_status_code: 400
              expected_response:
                error: Invalid age
                code: 100

    TAG_NAME_2:
        _run_mode_: 1  #SCENARIOS_AS_TESTS__USECASES_AS_TESTSTEPS

        _no_env_:
            _scenarios_:

                my_test_1:
                    _description_: Enter my test description here

                    my_test_step_1:
                      _exec_method_: create_user
                      save_name: my_var_1
                      params:
                        data:
                          name: John
                          age: 41

                    my_test_step_2:
                      _exec_method_: get_user
                      save_name: my_var_2
                      params:
                        data:
                          name: Peter
                          age: Ten
                      control:
                        expected_status_code: 400
                      expected_response:
                        error: Invalid age
                        code: 100


                my_test_2:
                    _description_: Enter my test description here - will be overridden when env = qa

                    my_test_step_1:
                      _exec_method_: create_user
                      save_name: my_var_1
                      params:
                        data:
                          name: John
                          age: 41

                    my_test_step_2:
                      _exec_method_: create_user
                      save_name: my_var_2
                      params:
                        data:
                          name: Peter
                          age: 42


        _env_:
            qa:
                _scenarios_:

                    my_test_1:
                        _description_: my_test_1 will be skipped when env = qa

                        my_test_step_1:
                          _skip_all_: true


                    my_test_2:
                        _description_: Enter my test description here - will override the _no_env_ description

                        my_test_step_1:
                          _exec_method_: create_user
                          _description_: will override this whole step but keep the step 2 from no_env
                          save_name: my_var_1
                          params:
                            data:
                              name: Will Override Name in _no_env_ Same Scenario
                              age: 41
                          _known_bug_:
                            bug_issue: JIRA-1234
                            bug_message: User already exists


    """

    def __init__(self, data: Union[str, Dict], env_name: str):
        self.env_name = env_name
        self.__data: Dict[str, Tuple[RunMode, Dict]] = self._compile_data(data)

    def get_scenarios_or_usecases(self, tag_name: str, scenario_name: str = "") -> Tuple[RunMode, Dict]:
        if tag_name not in self.__data:
            raise AttributeError(f"{tag_name=} not found on data file")
        res = self.__data[tag_name]

        if scenario_name:
            run_mode, scenarios = res
            if scenario_name not in scenarios:
                raise AttributeError(f"{scenario_name=} not found under {tag_name=}")
            res = run_mode, scenarios[scenario_name]

        return res

    def _compile_data(self, data: Union[str, Dict]) -> Dict[str, Tuple[RunMode, Dict]]:
        if isinstance(data, str):
            data = load_config(data)

        result = OrderedDict()
        for tag_name, tag_data in data.items():
            result[tag_name] = self._compile_tag_data(tag_data)
        return result

    # Keywords = [_env_: Dict, _no_env_: Dict, _scenarios_: Dict, _usecases_: Dict, _based_on_: str]
    def _compile_tag_data(self, base: Dict) -> Tuple[RunMode, Dict]:
        result = OrderedDict()

        # get run_mode if defined at the tag level
        run_mode = RunMode.decode(base.get("_run_mode_", RunMode.SCENARIOS_AS_TESTS__USECASES_AS_TESTSTEPS))

        # extract env or no_env
        if "_env_" in base or "_no_env_" in base:
            res_env = base["_env_"].get(self.env_name) if "_env_" in base else None
            res_no_env = base.get("_no_env_")
        else:
            res_env = None
            res_no_env = base

        # make sure that either dict has data
        if res_env:
            if res_no_env:
                res_1, res_2 = res_no_env, res_env
            else:
                res_1, res_2 = res_env, None
        else:
            if res_no_env:
                res_1, res_2 = res_no_env, None
            else:
                return 0, base

        # scenarios are tests
        # use-cases are test-steps
        if isinstance(res_1, dict) and "_scenarios_" in res_1:
            res_1 = res_1["_scenarios_"]
            res_2 = res_2["_scenarios_"] if res_2 else None

            # update result with all scenarios from res_1
            result.update(res_1)

            # check for scenarios with same name under no_env and env and merge them
            if res_2:
                for scenario_name in res_2:
                    if scenario_name not in result:
                        result[scenario_name] = OrderedDict()

                    # check for useCases with same name under no_env and env under same scenario and replace them
                    for usecase_name, usecase in res_2[scenario_name].items():
                        result[scenario_name][usecase_name] = usecase

            # update useCases, from all scenarios, upon _based_on_ option
            for scenario in result.values():
                for usecase_name, usecase in scenario.items():
                    if usecase_name != "_description_":
                        usecase.update(get_usecase_fields_based_on_another_usecase(result, usecase))

            return run_mode, result

        # use-cases are tests -> no test-steps
        if isinstance(res_1, dict) and "_usecases_" in res_1:
            run_mode = RunMode.USECASES_AS_TESTS

            res_1 = res_1["_usecases_"]
            res_2 = res_2["_usecases_"] if res_2 else None

            result.update(res_1)

            # check for useCases with same name under no_env and env and merge them
            if res_2:
                for usecase_name, usecase in res_2.items():
                    result[usecase_name] = usecase

            # update useCases upon _based_on_ option
            for usecase_name, usecase in result.items():
                if usecase_name != "_description_":
                    usecase.update(get_usecase_fields_based_on_another_usecase(result, usecase))

            return run_mode, result

        return 0, res_1


class SafeTry:

    def __init__(self,
                 toolbox,
                 rm,
                 current_test,
                 step_description: str = "",
                 ros_success: str = "ok",
                 ros_failure: str = "",
                 ros_expected_failure: str = "",
                 bug: str = "",
                 take_screenshot: bool = False):
        self._toolbox = toolbox
        self.rm = rm
        self.current_test = current_test

        self.step_description = step_description
        self.ros_success = ros_success
        self.ros_expected_failure = ros_expected_failure
        self.ros_failure = ros_failure
        self.bug = bug
        self.ros = ""

        self.take_screenshot = take_screenshot

        self.exc_val = None
        self.set_step_text(step_description)

    def is_success(self) -> bool:
        return self.exc_val is None

    def is_skipped(self) -> bool:
        return isinstance(self.exc_val, SkipTestError)

    def is_expected_error(self) -> bool:
        return isinstance(self.exc_val, ExpectedError)

    def is_failed(self) -> bool:
        return not self.is_success() and not self.is_expected_error()

    def get_ros(self) -> str:
        return self.ros

    def set_step_text(self, step_description: str):
        self.step_description = step_description
        self.rm.show_status(step_description)
        return self

    def set_ros_success(self, ros_success: str):
        self.ros_success = ros_success
        return self

    def set_ros_failure(self, ros_failure: str):
        self.ros_failure = ros_failure
        return self

    def set_ros_expected_failure(self, ros_expected_failure: str):
        self.ros_expected_failure = ros_expected_failure
        return self

    def _end_last_step(self, exc_val):
        self.exc_val = exc_val

        if exc_val is None:
            status = enums_data.STATE_PASSED
            self.ros = self.ros_success
        else:
            if isinstance(exc_val, SkipTestError):
                status = enums_data.STATE_SKIPPED
                self.ros = f"{exc_val}"
            elif isinstance(exc_val, ExpectedError):
                status = enums_data.STATE_PASSED
                self.ros = f"{self.ros_expected_failure} {exc_val}"
            else:
                end_reason = f"{self.ros_failure} {exc_val}"
                jira_issue = get_known_bug_failure_issue(self.bug, end_reason)
                status = enums_data.STATE_FAILED_KNOWN_BUG if jira_issue else enums_data.STATE_FAILED
                self.ros = f"{jira_issue} {end_reason}".lstrip()

        self.rm.test_step(self.current_test, status, self.ros.lstrip(), self.step_description, take_screenshot=self.take_screenshot, exc_value=exc_val)

    def new_step(self, step_description, ros_success: str = None, ros_failure: str = None, ros_expected_failure: str = None, take_screenshot: bool = None):
        self._end_last_step(None)
        self.set_step_text(step_description)

        if take_screenshot is not None:
            self.take_screenshot = take_screenshot
        if ros_success is not None:
            self.ros_success = ros_success
        if ros_failure is not None:
            self.ros_failure = ros_failure
        if ros_expected_failure is not None:
            self.ros_expected_failure = ros_expected_failure

        return self

    def skip_test(self, reason: str = "Skipped"):
        raise SkipTestError(reason)

    def __enter__(self):
        self.exc_val = None
        self._toolbox.clear_last_execution()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._end_last_step(exc_val)

        if exc_val is None or isinstance(exc_val, (ExpectedError, SkipTestError)):
            pass
        else:
            self.rm.test_info(self.current_test, get_traceback_tabulate(exc_val), "ERROR")
            if self.rm.is_debugcode():
                raise exc_val

        return self


class DDTMethods(DataReader):

    def __init__(self, data: Union[str, Dict], env_name: str, exec_toolbox: ExecutionToolbox):
        super(DDTMethods, self).__init__(data, env_name)

        self.response_from_usecases = OrderedDict()
        self.exec_toolbox = exec_toolbox

    """
    tag keywords:
        _run_mode_: int     = 1 (default) SCENARIOS_AS_TESTS__USECASES_AS_TESTSTEPS or 2 USECASES_AS_TESTS
        _no_env_: dict      = _scenarios_ or _usecases_
        _env_: dict         = env_name: dict (example, dev: qa:)
    scenario keywords:
        _description_: str  = if _run_mode_ == 1
    usecase keywords:
        _no_skip_: bool     = execute useCase even if previous failed (used for _run_all_usecases_as_teststeps)
        _skip_all_: str     = reason of skipping all useCases
        _description_: str  = string with test or teststep description
        _exec_method_: str  = method name to be executed
        _known_bug_: 
          bug_issue: str    = JIRA-XXXX
          bug_message: str  = Division by zero
    """

    # generic call with auto-detect run_mode
    def run(self, ma: Dict, rm: ReportManager, tag_name: str, scenario_name: str = "", run_mode: RunMode = None):
        if scenario_name:
            if run_mode is None:
                run_mode, _ = self.get_scenarios_or_usecases(tag_name=tag_name)

            if run_mode is RunMode.SCENARIOS_AS_TESTS__USECASES_AS_TESTSTEPS:
                self.run_scenario_as_test__usecases_as_teststeps(ma, rm, tag_name=tag_name, scenario_name=scenario_name, add_test_usecase=True)
            elif run_mode is RunMode.SCENARIO__USECASES_AS_TESTS:
                self.run_scenario__usecases_as_tests(ma=ma, rm=rm, tag_name=tag_name, scenario_name=scenario_name)
            else:
                raise ValueError(f"{run_mode=} invalid for {tag_name=} {scenario_name=}")
        else:
            if (run_mode is None or
                    run_mode is RunMode.SCENARIOS_AS_TESTS__USECASES_AS_TESTSTEPS or
                    run_mode is RunMode.USECASES_AS_TESTS):
                self.run_tag(ma=ma, rm=rm, tag_name=tag_name, run_mode=run_mode)
            else:
                raise ValueError(f"{run_mode=} invalid for {tag_name=}! Missing scenario_name")

    # under that tag, run all scenarios as a test, and the usesCases are testSteps
    def run_tag(self, ma: Dict, rm: ReportManager, tag_name: str, run_mode: RunMode = None):
        _run_mode, scenarios = self.get_scenarios_or_usecases(tag_name=tag_name)
        _run_mode = run_mode or _run_mode
        if _run_mode is RunMode.USECASES_AS_TESTS:
            self.run_usecases_as_tests__without_scenario(ma=ma, rm=rm, tag_name=tag_name)
        else:
            for scenario_name in scenarios:
                if _run_mode is RunMode.SCENARIOS_AS_TESTS__USECASES_AS_TESTSTEPS:
                    self.run_scenario_as_test__usecases_as_teststeps(ma, rm, tag_name=tag_name, scenario_name=scenario_name, add_test_usecase=True)
                elif _run_mode is RunMode.SCENARIO__USECASES_AS_TESTS:
                    self.run_scenario__usecases_as_tests(ma, rm, tag_name=tag_name, scenario_name=scenario_name)
                else:
                    raise ValueError(f"{_run_mode=} invalid for {tag_name=} {scenario_name=}")

    # create a single test for that scenario, so the usesCases will be testSteps
    def run_scenario_as_test__usecases_as_teststeps(self, ma: Dict, rm: ReportManager,
                                                    tag_name: str,
                                                    scenario_name: str,
                                                    bug: Union[str, Dict, List] = "",
                                                    description: str = "",
                                                    add_test_usecase: bool = True):

        usecase_name = scenario_name if add_test_usecase else ""
        _, usecases = self.get_scenarios_or_usecases(tag_name=tag_name, scenario_name=scenario_name)
        description = description or usecases.get("_description_", "")
        current_test = rm.startTest(ma, usecase=usecase_name, description=description)
        
        if rm.has_ap_flag("--norun"):
            rm.testSkipped(current_test, "--norun")
        else:
            rm.test_info(current_test, f"{tag_name=} {scenario_name=} TEST_STEPS:\n{prettify(usecases, as_yaml=True)}", "DEBUG")

            _, failed_usecase = self._run_usecases_as_teststeps(rm, current_test, usecases)
            endTest(rm, current_test, bug=bug)

    # create a test for each useCase under a scenario
    def run_scenario__usecases_as_tests(self, ma: Dict, rm: ReportManager,
                                        tag_name: str,
                                        scenario_name: str):
        _, usecases = self.get_scenarios_or_usecases(tag_name=tag_name, scenario_name=scenario_name)
        for usecase_name, usecase in usecases.items():
            # just as safeguard
            if usecase_name == "_description_":
                continue

            current_test = rm.startTest(ma, usecase=usecase_name, description=usecase.get("_description_", ""))

            end_reason = ""
            if rm.has_ap_flag("--norun"):
                rm.testSkipped(current_test, "--norun")
            else:
                rm.test_info(current_test, f"{tag_name=} {scenario_name=} {usecase_name=} USECASE_DATA:\n{prettify(usecase, as_yaml=True)}", "DEBUG")

                if usecase.get("_skip_all_"):
                    rm.test_step(current_test, enums_data.STATE_SKIPPED, usecase.get("_skip_all_"), usecase_name)
                    break
                else:
                    with SafeTry(self.exec_toolbox, rm, current_test, step_description=usecase_name) as st:
                        # Execute the useCase
                        self.response_from_usecases[usecase_name] = self.exec_toolbox.execute(
                            rm=rm,
                            current_test=current_test,
                            exec_method=usecase["_exec_method_"],
                            usecase=usecase,
                            usecase_name=usecase_name,
                            st=st)
                    end_reason = st.get_ros() if st.is_success() else ""

                endTest(rm, current_test, end_reason=end_reason, bug=usecase.get("_known_bug_", ""))

    def _run_usecases_as_teststeps(self, rm, current_test, usecases: Dict):
        failed_usecase = ""
        for usecase_name, usecase in usecases.items():
            # the scenario (test) may have as description
            if usecase_name == "_description_":
                continue

            if skip_all_reason := usecase.get("_skip_all_"):
                rm.test_step(current_test, enums_data.STATE_SKIPPED, skip_all_reason, usecase_name)
                break
            else:
                if failed_usecase == "" or usecase.get("_no_skip_"):
                    with SafeTry(self.exec_toolbox, rm, current_test, step_description=usecase_name, ros_failure=f"In usecase {usecase_name},", bug=usecase.get("_known_bug_", ""), take_screenshot=False) as st:
                        # Execute the useCase
                        self.response_from_usecases[usecase_name] = self.exec_toolbox.execute(
                            rm=rm,
                            current_test=current_test,
                            exec_method=usecase["_exec_method_"],
                            usecase=usecase,
                            usecase_name=usecase_name,
                            st=st)

                    if st.is_failed() and not failed_usecase:
                        failed_usecase = usecase_name
                else:
                    rm.test_step(current_test, enums_data.STATE_SKIPPED, f"Because usecase {failed_usecase} failed", usecase_name)

        return self.response_from_usecases, failed_usecase

    def run_usecases_as_tests__without_scenario(self, ma: Dict, rm: ReportManager, tag_name: str):
        _, usecases = self.get_scenarios_or_usecases(tag_name=tag_name)

        for usecase_name, usecase in usecases.items():
            # the use-case (test) may have as description
            current_test = rm.startTest(ma, usecase=usecase_name, description=usecase.get("_description_", ""))

            if rm.has_ap_flag("--norun"):
                rm.testSkipped(current_test, "--norun")
            else:
                rm.test_info(current_test, f"{tag_name=} {usecase_name=} USECASE_DATA:\n{prettify(usecase, as_yaml=True)}", "DEBUG")

                with SafeTry(self.exec_toolbox, rm, current_test) as st:
                    # Execute the useCase
                    self.response_from_usecases[usecase_name] = self.exec_toolbox.execute(
                        rm=rm,
                        current_test=current_test,
                        exec_method=usecase["_exec_method_"],
                        usecase=usecase,
                        usecase_name=usecase_name,
                        st=st)
                end_reason = st.get_ros() if st.is_success() else ""
                endTest(rm, current_test, end_reason=end_reason, bug=usecase.get("_known_bug_", ""))


def get_usecase_fields_based_on_another_usecase(usecases: Dict, current_usecase: Union[Dict, str]) -> Dict:
    # in case it's the name of the useCase, find it first.
    if isinstance(current_usecase, str):
        curr_uc = usecases
        for name in current_usecase.split("/"):
            curr_uc = curr_uc[name]
        current_usecase = curr_uc

    # this useCase is not based on any other, so nothing to update
    if "_based_on_" not in current_usecase:
        return dict()

    bo_usecase_name, field_names = current_usecase["_based_on_"]

    # get the useCase that is _based_on_
    based_on = usecases
    for name in bo_usecase_name.split("/"):
        if name not in based_on:
            raise KeyError(f"based_on {bo_usecase_name} - {name} not found in {based_on.keys()}")
        based_on = based_on[name]

    # maybe this one as based_on as well
    based_on_data = based_on.copy()
    based_on_data.update(get_usecase_fields_based_on_another_usecase(usecases, based_on_data))

    # copy all fields from other if not contained already in current
    try:
        return {field_name: left_update_dict(based_on_data[field_name], current_usecase.get(field_name, dict())) if isinstance(based_on_data[field_name], dict) else based_on_data[field_name] for field_name in field_names}
    except Exception as ex:
        raise KeyError(f"Key {ex} not found in {bo_usecase_name}, only {based_on_data.keys()}")


def get_known_bug_failure_issue(bug: Union[str, Dict, List], end_reason: str = "") -> str:
    if isinstance(bug, str):
        return bug

    if isinstance(bug, list):
        for current_bug in bug:
            bug_issue = current_bug.get("bug_issue", "")
            bug_message = current_bug.get("bug_message", "")
            if bug_message == end_reason:
                return bug_issue
    elif isinstance(bug, dict):
        bug_issue = bug.get("bug_issue", "")
        bug_message = bug.get("bug_message", "")
        if bug_message == end_reason:
            return bug_issue

    return ""


def endTest(rm: ReportManager,
            current_test: TestDetails,
            min_passed_percentage: float = 100.0,
            end_reason: str = "",
            bug: Union[str, Dict, List] = "",
            exc_val: BaseException = None):
    def get_end_reason(state):
        laps = tc.get_timed_laps(state)
        if laps:
            lap = laps[0] if state in [enums_data.STATE_FAILED, enums_data.STATE_FAILED_KNOWN_BUG] else laps[-1]
            ros, exc_value = str(lap.reason_of_state).strip(), lap.exc_value
        else:
            ros, exc_value = "", None

        final_end_reason = end_reason or ros or "ok"
        jira_issue = get_known_bug_failure_issue(bug, final_end_reason)
        return f"{jira_issue} {final_end_reason}".strip(), exc_val or exc_value, final_end_reason

    tc = current_test.get_test_step_counters()
    if tc.get_total() > 0:
        if tc.get_state_percentage(enums_data.STATE_PASSED) >= min_passed_percentage:
            ros, exc_value, _ = get_end_reason(enums_data.STATE_PASSED)
            rm.testPassed(current_test, reason_of_state=ros, exc_value=exc_value)
        elif tc[enums_data.STATE_FAILED] > 0:
            ros, exc_value, fer = get_end_reason(enums_data.STATE_FAILED)
            if ros == fer:
                rm.testFailed(current_test, reason_of_state=ros, exc_value=exc_value)
            else:
                rm.testFailedKnownBug(current_test, reason_of_state=ros, exc_value=exc_value)
        elif tc[enums_data.STATE_FAILED_KNOWN_BUG] > 0:
            ros, exc_value, fer = get_end_reason(enums_data.STATE_FAILED_KNOWN_BUG)
            rm.testFailedKnownBug(current_test, reason_of_state=ros, exc_value=exc_value)
        elif tc[enums_data.STATE_SKIPPED] > 0:
            ros, exc_value, fer = get_end_reason(enums_data.STATE_SKIPPED)
            rm.testSkipped(current_test, reason_of_state=ros, exc_value=exc_value)
    else:
        ros, exc_value, _ = get_end_reason(enums_data.STATE_PASSED)
        rm.testPassed(current_test, reason_of_state=ros, exc_value=exc_value)

