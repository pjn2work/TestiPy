from __future__ import annotations

import copy

from typing import Union, Dict, List
from abc import abstractmethod, ABC
from collections import OrderedDict

from testipy.configs import enums_data
from testipy.reporter.report_base import TestDetails
from testipy.reporter.report_manager import ReportManager
from testipy.helpers import get_traceback_tabulate, load_config, left_update_dict, prettify
from testipy.helpers.handle_assertions import ExpectedError, SkipTestError


class ExecutionToolbox(ABC):
    @abstractmethod
    def execute(self, rm: ReportManager, exec_method, usecase: Dict, usecase_name: str, current_test: TestDetails, st: SafeTry):
        pass

    @abstractmethod
    def clear_last_execution(self):
        pass

    @abstractmethod
    def log_example(self, rm: ReportManager, current_test: TestDetails, forced: bool = True, text: str = ""):
        pass

    @abstractmethod
    def log_error(self, rm: ReportManager, current_test: TestDetails, exc_val, save_to_file: bool = False, text: str = ""):
        pass

    @abstractmethod
    def validate_expected_error(self, rm: ReportManager, current_test: TestDetails, usecase: Dict, usecase_name: str):
        pass


class DataReader:

    def __init__(self, data: Union[str, Dict], env_name: str):
        self.env_name = env_name
        self.data = self._compile_data(data)

    def get_scenarios_or_usecases(self, tag_name: str, scenario_name: str = "") -> Dict:
        if tag_name not in self.data:
            raise AttributeError(f"{tag_name=} not found on data file")
        res = self.data[tag_name]

        if scenario_name:
            if scenario_name not in res:
                raise AttributeError(f"{scenario_name=} not found under {tag_name=}")
            res = res[scenario_name]

        return res

    def _compile_data(self, data: Union[str, Dict]) -> Dict:
        if isinstance(data, str):
            data = load_config(data)

        result = OrderedDict()
        for tag_name, tag_data in data.items():
            result[tag_name] = self._compile_tag_data(tag_data)
        return result

    # Keywords = [env_first: bool, allow_override: bool, env: Dict, no_env: Dict, scenarios: Dict, usecases: Dict, based_on: str]
    def _compile_tag_data(self, base: Dict) -> Dict:
        """
        my_TAG_NAME:

          env_first: false
          allow_override: true

          no_env:
            scenarios:

              my_scenario_1:

                my_usecase_1:
                  exec_method: create_user
                  save_name: my_var_1
                  params:
                    data:
                      name: John
                      age: 41

                my_usecase_2:
                  exec_method: create_user
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

              my_scenario_2:

                my_usecase_3:
                  exec_method: create_user
                  save_name: my_var_1
                  params:
                    data:
                      name: John
                      age: 41


            env:
                qa:
                  scenarios:

                    my_scenario_1:

                        my_usecase_1:
                          exec_method: create_user
                          save_name: my_var_1
                          params:
                            data:
                              name: John
                              age: 41


        """

        result = OrderedDict()

        env_first = base.get("env_first", False)
        allow_override = base.get("allow_override", True)

        # extract env or no_env
        if "env" in base or "no_env" in base:
            res_env = base["env"].get(self.env_name) if "env" in base else None
            res_no_env = base.get("no_env")
        else:
            res_env = None
            res_no_env = base

        # make sure the first dict has data and prio by "env_first"
        if env_first and res_env:
            res_1, res_2 = res_env, res_no_env
        else:
            res_1, res_2 = res_no_env, res_env

        # no data to extract? this never happens (just a safeguard)
        if not res_1:
            return base

        # extract scenarios (and usecases)
        if isinstance(res_1, dict) and "scenarios" in res_1:
            res_1 = res_1["scenarios"]
            res_2 = res_2["scenarios"] if res_2 else None

            # update result with all usecases from res_1
            result.update(res_1)

            # check if scenarios collide and update them
            if res_2:
                for scenario_name in res_2:
                    if scenario_name not in result:
                        result[scenario_name] = OrderedDict()

                    for usecase_name, usecase in res_2[scenario_name].items():
                        if not allow_override and usecase_name in result[scenario_name]:
                            raise NameError(f"In your scenario/usecase {scenario_name}/{usecase_name}, conflict with env {self.env_name}")
                        result[scenario_name][usecase_name] = usecase

            # update useCases, from all scenarios, upon based_on option
            for scenario in result.values():
                for usecase_name, usecase in scenario.items():
                    usecase.update(get_usecase_fields_based_on_another_usecase(result, usecase))

            return result

        # extract only usecases
        if isinstance(res_1, dict) and "usecases" in res_1:
            res_1 = res_1["usecases"]
            res_2 = res_2["usecases"] if res_2 else None

            result.update(res_1)

            # check if usecases collide and update them
            if res_2:
                for usecase_name, usecase in res_2.items():
                    if not allow_override and usecase_name in result:
                        raise NameError(f"In your usecase {usecase_name}, conflict with env {self.env_name}")
                    result[usecase_name] = usecase

            # update useCases upon based_on option
            for usecase_name, usecase in result.items():
                usecase.update(get_usecase_fields_based_on_another_usecase(result, usecase))

            return result

        return res_1


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
                 log_text: str = "",
                 log_response: bool = False,
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
        self.log_text = log_text

        self.log_output = log_response
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
        self.rm.showStatus(step_description)
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

        self.rm.testStep(self.current_test, status, self.ros.lstrip(), self.step_description, take_screenshot=self.take_screenshot, exc_value=exc_val)

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
        if self.log_output:
            self._toolbox.clear_last_execution()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._end_last_step(exc_val)

        if exc_val is None or isinstance(exc_val, (ExpectedError, SkipTestError)):
            if self.log_output:
                self._toolbox.log_example(self.rm, self.current_test, forced=True, text=self.log_text)
        else:
            if self.log_output:
                self._toolbox.log_error(self.rm, self.current_test, exc_val, save_to_file=False, text=self.log_text)
            else:
                if self.rm.is_debugcode():
                    raise exc_val
                self.rm.testInfo(self.current_test, get_traceback_tabulate(exc_val), "ERROR")

        return self


class DDTMethods(DataReader):

    def __init__(self, data: Union[str, Dict], env_name: str, exec_toolbox: ExecutionToolbox):
        super(DDTMethods, self).__init__(data, env_name)

        self.response_from_usecases = OrderedDict()
        self.exec_toolbox = exec_toolbox

    """
    usecase testdata keywords:
        description: string with test description
        exec_method: method name to be executed
        bug: 
          bug_issue: JIRA-XXXX
          bug_message: Division by zero
        no_skip: boolean (used for auto_call_usecases)
        skip_all: str = reason of skipping this test
    """

    # under that tag, run all scenarios as a test, and the usesCases are testSteps
    def run_all_scenarios_as_tests_usecases_as_teststeps_under_tag_name(self, td: Dict, rm: ReportManager,
                                                                        tag_name: str):
        for scenario_name in self.get_scenarios_or_usecases(tag_name=tag_name):
            self.run_single_scenario_as_test_usecases_as_teststeps(td, rm, tag_name=tag_name, scenario_name=scenario_name, add_test_usecase=True)

    # create a single test for that scenario, so the usesCases will be testSteps
    def run_single_scenario_as_test_usecases_as_teststeps(self, td: Dict, rm: ReportManager,
                                                          tag_name: str,
                                                          scenario_name: str,
                                                          bug: Union[str, Dict, List] = "",
                                                          description: str = "",
                                                          add_test_usecase: bool = True):

        usecase_name = scenario_name if add_test_usecase else ""
        current_test = rm.startTest(td, usecase=usecase_name, description=description)
        if rm.has_ap_flag("--norun"):
            rm.testSkipped(current_test, "--norun")
        else:
            usecases = self.get_scenarios_or_usecases(tag_name=tag_name, scenario_name=scenario_name)

            rm.testInfo(current_test, f"TEST_STEPS {tag_name=} {scenario_name=}:\n{prettify(usecases, as_yaml=True)}", "DEBUG")

            _, failed_usecase = self._run_all_usecases_as_teststeps(rm, current_test, usecases)

            endTest(rm, current_test, bug=bug)

    # create a test for each useCase under a scenario
    def run_all_usecases_as_tests(self, td: Dict, rm: ReportManager,
                                  tag: str,
                                  scenario_name: str):
        for usecase_name, usecase in self.get_scenarios_or_usecases(tag_name=tag, scenario_name=scenario_name).items():
            current_test = rm.startTest(td, usecase=usecase_name, description=usecase.get("description"))

            end_reason = ""
            if rm.has_ap_flag("--norun"):
                rm.testSkipped(current_test, "--norun")
            else:
                rm.testInfo(current_test, f"TEST_USECASE {tag=} {scenario_name=} {usecase_name=}:\n{prettify(usecase, as_yaml=True)}", "DEBUG")

                if usecase.get("skip_all"):
                    rm.testStep(current_test, enums_data.STATE_SKIPPED, usecase.get("skip_all"), usecase_name)
                    break
                else:
                    # execute the test and assert valid response
                    with SafeTry(self.exec_toolbox, rm, current_test, step_description="load usecase test data", log_response=True) as st:
                        self.response_from_usecases[usecase_name] = self.exec_toolbox.execute(
                            rm,
                            usecase['exec_method'],
                            usecase=usecase,
                            usecase_name=usecase_name,
                            current_test=current_test,
                            st=st)
                    end_reason = st.get_ros() if st.is_success() else ""

                    # log expected response
                    if usecase.get("expected_response"):
                        rm.testInfo(current_test, f"Expected response:\n{prettify(usecase['expected_response'])}", "INFO")

                    # validate error response
                    if st.is_expected_error():
                        with SafeTry(self.exec_toolbox, rm, current_test, step_description="assert expected error", log_response=False) as ve:
                            self.exec_toolbox.validate_expected_error(rm, current_test, usecase, usecase_name)
                            end_reason = st.get_ros()

                endTest(rm, current_test, end_reason=end_reason, bug=usecase.get("bug", ""))

    def _run_all_usecases_as_teststeps(self, rm, current_test, usecases: Dict):
        failed_usecase = ""
        for usecase_name, usecase in usecases.items():
            if usecase.get("skip_all"):
                rm.testStep(current_test, enums_data.STATE_SKIPPED, usecase.get("skip_all"), usecase_name)
                break
            else:
                if failed_usecase == "" or usecase.get("no_skip"):
                    with SafeTry(self.exec_toolbox, rm, current_test, step_description=usecase_name, ros_failure=f"In usecase {usecase_name},", bug=usecase.get("bug", ""), log_response=True, take_screenshot=False, log_text=f"Express {usecase_name=}") as st:
                        try:
                            self.response_from_usecases[usecase_name] = self.exec_toolbox.execute(
                                rm,
                                usecase['exec_method'],
                                usecase=usecase,
                                usecase_name=usecase_name,
                                current_test=current_test,
                                st=st)
                        except ExpectedError:
                            self.exec_toolbox.validate_expected_error(rm, current_test, usecase, usecase_name)
                            raise

                    # log expected response
                    if usecase.get("expected_response"):
                        rm.testInfo(current_test, f"Express {usecase_name=} expected response:\n{prettify(usecase['expected_response'])}", "DEBUG")

                    if st.is_failed() and not failed_usecase:
                        failed_usecase = usecase_name
                else:
                    rm.testStep(current_test, enums_data.STATE_SKIPPED, f"Because usecase {failed_usecase} failed", usecase_name)

        return self.response_from_usecases, failed_usecase


def get_usecase_fields_based_on_another_usecase(usecases: Dict, current_usecase: Union[Dict, str]) -> Dict:
    # in case it's the name of the useCase, find it first.
    if isinstance(current_usecase, str):
        curr_uc = usecases
        for name in current_usecase.split("/"):
            curr_uc = curr_uc[name]
        current_usecase = curr_uc

    # this useCase is not based on any other, so nothing to update
    if "based_on" not in current_usecase:
        return dict()

    bo_usecase_name, field_names = current_usecase["based_on"]

    # get the useCase that is based_on
    based_on = usecases
    for name in bo_usecase_name.split("/"):
        if name not in based_on:
            raise KeyError(f"based_on {bo_usecase_name} - {name} not found in {based_on.keys()}")
        based_on = based_on[name]

    # maybe this one as based_on as well
    based_on_data = copy.deepcopy(based_on)
    based_on_data.update(get_usecase_fields_based_on_another_usecase(usecases, based_on_data))

    # copy all fields from other if not contained already in current
    return {field_name: left_update_dict(based_on_data[field_name], current_usecase.get(field_name, dict())) if isinstance(based_on_data[field_name], dict) else based_on_data[field_name] for field_name in field_names}


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
            rm.testPassed(current_test, ros, exc_value)
        elif tc[enums_data.STATE_FAILED] > 0:
            ros, exc_value, fer = get_end_reason(enums_data.STATE_FAILED)
            if ros == fer:
                rm.testFailed(current_test, ros, exc_value)
            else:
                rm.testFailedKnownBug(current_test, ros, exc_value)
        elif tc[enums_data.STATE_FAILED_KNOWN_BUG] > 0:
            ros, exc_value, fer = get_end_reason(enums_data.STATE_FAILED_KNOWN_BUG)
            rm.testFailedKnownBug(current_test, ros, exc_value)
        elif tc[enums_data.STATE_SKIPPED] > 0:
            ros, exc_value, fer = get_end_reason(enums_data.STATE_SKIPPED)
            rm.testSkipped(current_test, ros, exc_value)
    else:
        ros, exc_value, _ = get_end_reason(enums_data.STATE_PASSED)
        rm.testPassed(current_test, ros, exc_value)

