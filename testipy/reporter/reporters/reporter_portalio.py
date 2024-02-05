import os
import traceback
import json

from time import time
from typing import Dict
from reportportal_client import create_client, ClientType

from testipy import get_exec_logger
from testipy.configs import enums_data
from testipy.lib_modules.common_methods import dict_without_keys
from testipy.lib_modules.start_arguments import StartArguments
from testipy.helpers import load_config
from testipy.reporter import ReportManager, ReportInterface, PackageDetails, SuiteDetails, TestDetails


# to show or not stacktrace
DEBUGCODE = False
SETTINGS_FILE = "reporter_portalio.yaml"

_exec_logger = get_exec_logger()


def get_credentials(project_name, env_name):
    settings = load_config(SETTINGS_FILE, __file__)
    settings = settings[env_name] if env_name in settings else settings["default"]

    launch_name = project_name if project_name else settings["default_project_name"]

    return settings["url"], settings["rp_proj"], launch_name, settings["token"]


def timestamp():
    return str(int(time() * 1000))


def my_error_handler(exc_info):
    _exec_logger.error(str(exc_info[1]))
    if DEBUGCODE:
        _exec_logger.error(str(exc_info))
        #print(f">> ReportPortalIO Error: {exc_info[1]}")
        #traceback.print_exception(*exc_info)


class ReporterPortalIO(ReportInterface):

    def __init__(self, rm: ReportManager, sa: StartArguments):
        super().__init__(self.__class__.__name__)

        global DEBUGCODE; DEBUGCODE = rm.is_debugcode()

        endpoint, rp_project, launch_name, api_key = get_credentials(rm.get_project_name(), rm.get_environment_name())
        description = dict_without_keys(sa.as_dict(), ("ap", "results_folder_base", "foldername_runtime"))
        description["valid_reporters"] = list(sa.valid_reporters)
        #description.update(param["ap"].get_dict())
        description = json.dumps(description, indent=2, sort_keys=False)

        # start ReportPortal
        self._service = create_client(
            client_type=ClientType.ASYNC,
            endpoint=endpoint,
            project=rp_project,
            api_key=api_key,
            error_handler=my_error_handler)

        # launch Tests on ReportPortal
        self._launch_id = self._service.start_launch(
            name=launch_name,
            start_time=timestamp(),
            description=str(description))

        self.rm = rm
        self._all_parent_tests_by_name = dict()

    def save_file(self, current_test: TestDetails, data, filename: str):
        pass

    def copy_file(self, current_test: TestDetails, orig_filename: str, dest_filename: str, data):
        pass

    def _startup_(self, selected_tests: Dict):
        pass

    def _teardown_(self, end_state: str):
        self._service.finish_launch(end_time=timestamp(), status=enums_data.STATE_PASSED)
        self._service.terminate()

    def start_package(self, pd: PackageDetails):
        pd.reportportal_package_id = self._service.start_test_item(
            name=pd.get_name(), description="Package", start_time=timestamp(), item_type="SUITE")

    def end_package(self, pd: PackageDetails):
        self._service.finish_test_item(end_time=timestamp(), status=None, item_id=pd.reportportal_package_id)

    def start_suite(self, sd: SuiteDetails):
        attr = sd.get_attr()
        tags = {"TAG": " ".join(attr[enums_data.TAG_TAG]), "LEVEL": attr[enums_data.TAG_LEVEL]}
        sd.reportportal_suite_id = self._service.start_test_item(
            name=sd.get_name(),
            description="Suite",
            start_time=timestamp(),
            item_type="STORY",
            attributes=tags,
            parent_item_id=sd.package.reportportal_package_id)
        self._all_parent_tests_by_name = dict()

    def end_suite(self, sd: SuiteDetails):
        self.__close_parent_tests(sd)
        self._service.finish_test_item(end_time=timestamp(), status=None, item_id=sd.reportportal_suite_id)

    def start_test(self, current_test: TestDetails):
        test_name = current_test.get_name()
        if test_name in self._all_parent_tests_by_name:
            self._all_parent_tests_by_name[test_name]["tests"].append(current_test)
        else:
            if current_test.get_usecase():
                tags = {"TAG": " ".join(current_test.get_attr()[enums_data.TAG_TAG]), "LEVEL": current_test.get_attr()[
                    enums_data.TAG_LEVEL]}
                tags = {k: v for k, v in tags.items() if v}
                parameters = current_test.get_attr()["param"] if isinstance(current_test.get_attr()["param"], dict) and len(current_test.get_attr()["param"]) > 0 else {"param": str(current_test.get_attr()["param"])}
                start_time = str(int(current_test.get_starttime().timestamp() * 1000))

                parent_item_id = self._service.start_test_item(
                    name=test_name,
                    start_time=start_time,
                    item_type="TEST",
                    description="Test",
                    attributes=tags,
                    parameters=parameters,
                    parent_item_id=self._suite_id)

                self._all_parent_tests_by_name[test_name] = {"parent_item_id": parent_item_id, "tests": [current_test], "end_state": enums_data.STATE_PASSED}

    def test_info(self, current_test, info, level, attachment=None):
        pass

    def test_step(self, current_test, state: str, reason_of_state: str = "", description: str = "", take_screenshot: bool = False, qty: int = 1, exc_value: BaseException = None):
        pass

    def show_status(self, message: str):
        pass

    def show_alert_message(self, message: str):
        pass

    def input_prompt_message(self, message: str, default_value: str = ""):
        pass

    def end_test(self, current_test, ending_state, end_reason, exc_value: BaseException = None):
        test_name = current_test.get_name(False)

        # Get parent test or suite
        if test_name in self._all_parent_tests_by_name:
            parent_item_id = self._all_parent_tests_by_name[test_name]["parent_item_id"]
            usecase = current_test.get_usecase() or "NO_USECASE"

            if ending_state != enums_data.STATE_PASSED and self._all_parent_tests_by_name[test_name]["end_state"] != enums_data.STATE_FAILED:
                self._all_parent_tests_by_name[test_name]["end_state"] = ending_state
        else:
            parent_item_id = self._suite_id
            usecase = test_name

        # Create data to send to ReportPortalIO
        tags = {"TAG": " ".join(current_test.get_attr()[enums_data.TAG_TAG]), "LEVEL": current_test.get_attr()[
            enums_data.TAG_LEVEL]}
        tags = {k: v for k, v in tags.items() if v}
        parameters = current_test.get_attr()["param"] if isinstance(current_test.get_attr()["param"], dict) and len(current_test.get_attr()["param"]) > 0 else {"param": str(current_test.get_attr()["param"])}
        start_time = str(int(current_test.get_starttime().timestamp() * 1000))
        end_time = str(int(current_test.get_endtime().timestamp() * 1000))

        # Start test usecase
        usecase_id = self._service.start_test_item(name=usecase,
                                                   start_time=start_time,
                                                   item_type="SCENARIO",
                                                   description=end_reason,
                                                   attributes=tags,
                                                   parameters=parameters,
                                                   parent_item_id=parent_item_id)

        # Log all testInfo and testStep
        self.__log_infos(current_test, usecase_id)
        self.__log_test_steps(current_test, usecase_id)

        # issue_type allowable values: "pb***", "ab***", "si***", "ti***", "nd001". Where *** is locator id
        if ending_state == enums_data.STATE_FAILED_KNOWN_BUG:
            ending_state = enums_data.STATE_FAILED
            issue = {"issue_type": f"pb_1jy24u89zwx81"}
        elif ending_state == enums_data.STATE_FAILED:
            issue = {"issue_type": f"pb001"}
        else:
            issue = None

        # Close test usecase
        self._service.finish_test_item(end_time=end_time, status=ending_state, item_id=usecase_id, issue=issue)

    def __log_infos(self, current_test, item_id):
        for ts, _, level, info, attachment in current_test.get_info():
            if isinstance(attachment, dict):
                attachment["name"] = os.path.basename(attachment["name"])
            else:
                attachment = None
            self._service.log(time=str(ts), message=str(info), level=level, attachment=attachment, item_id=item_id)

    def __log_test_steps(self, current_test, item_id):
        tc = current_test.get_test_step_counters()
        if len(tc.get_timed_laps()) > 0:
            self._service.log(time=timestamp(), message=current_test.get_test_step_counters_tabulate(), level="DEBUG", attachment=None, item_id=item_id)
            str_res = "Steps Summary:\n" + tc.summary()
        else:
            str_res = "Test Summary:\n" + current_test.get_counters().summary(verbose=False)
        self._service.log(time=timestamp(), message=str_res, level="INFO", attachment=None, item_id=item_id)

    def __close_parent_tests(self):
        # This will close all tests that have a usecase under it (that usecase item is already closed, now the parent)
        ex = None

        for test_name, parent_test in self._all_parent_tests_by_name.items():
            try:
                end_time = str(int(parent_test["tests"][-1].get_endtime().timestamp() * 1000))
                self._service.finish_test_item(end_time=end_time,
                                               status=enums_data.STATE_PASSED if parent_test["end_state"] == enums_data.STATE_FAILED_KNOWN_BUG else parent_test["end_state"],
                                               item_id=parent_test["parent_item_id"])
            except Exception as e:
                ex = e

        if ex:
            raise ex
