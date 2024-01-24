import os

from typing import Dict
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from testipy.configs import enums_data
from testipy.helpers import Timer
from testipy.lib_modules.common_methods import get_app_version
from testipy.lib_modules.start_arguments import StartArguments
from testipy.reporter import ReportManager, ReportInterface

SLACK_API_TOKEN = os.getenv("TESTIPY_SLACK_API_TOKEN")
DEFAULT_CHANNEL = "C06BQ1UP6KG"
NOTIFY_USERS: dict[str, str] = dict()  # {"John Doe": "D067TJE96NM"}
RATE_WAIT_SEC = 0.45


emojis = {
    enums_data.STATE_PASSED: ":large_green_circle:",
    enums_data.STATE_FAILED: ":red_circle:",
    enums_data.STATE_FAILED_KNOWN_BUG: ":negative_squared_cross_mark:",
    enums_data.STATE_SKIPPED: ":arrow_right_hook:"
}


class ReporterSlack(ReportInterface):

    def __init__(self, rm: ReportManager, sa: StartArguments):
        super().__init__(self.__class__.__name__)
        self.client = WebClient(token=SLACK_API_TOKEN)
        self.rm = rm
        self.sa = sa
        self.TS = None
        self.build = sa.tests_scripts_build.get("build", "")
        self.timer = Timer()

    def get_report_manager_base(self):
        return self.rm.get_report_manager_base()

    def _send_message(self, channel=DEFAULT_CHANNEL, threadts=True, reply_broadcast=False, **message):
        thread_ts = self.TS if threadts else None
        retry = 3
        while retry > 0:
            retry -= 1
            try:
                self.timer.sleep_until_over().set_timer_for(RATE_WAIT_SEC)
                return self.client.chat_postMessage(channel=channel, thread_ts=thread_ts, reply_broadcast=reply_broadcast, **message)
            except SlackApiError as e:
                self.timer.set_timer_for(RATE_WAIT_SEC)
                if retry == 0:
                    self.rm._execution_log("ERROR", f"ReporterSlack: {e}")

    def save_file(self, current_test, data, filename):
        pass

    def copy_file(self, current_test, orig_filename, dest_filename, data):
        pass

    def __startup__(self, selected_tests: Dict):
        __app__, __version__, _ = get_app_version()
        response = self._send_message(threadts=False, text=f":arrow_forward: {__app__} {__version__}b{self.build} Starting tests for {self.rm.get_foldername_runtime()} (env={self.rm.get_environment_name()}, user={self.sa.user}, host={self.sa.hostname})")
        self.TS = response.get("ts") if response else None

    def __teardown__(self, end_state):
        # get manager base
        rmb =self.get_report_manager_base()

        flag = emojis.get(end_state, f":{end_state}:")

        self._send_message(reply_broadcast=True, text=f"{flag} {rmb.get_reporter_details()}")
        for name, user in NOTIFY_USERS.items():
            self._send_message(channel=user, threadts=False, text=f"{flag} {self.rm.get_foldername_runtime()} (env={self.rm.get_environment_name()}, user={self.sa.user}, host={self.sa.hostname})\n{rmb.get_reporter_details()}")

    def start_package(self, package_name: str, package_attr: Dict):
        rmb =self.get_report_manager_base()
        # self._send_message(text=":open_file_folder: Starting package {} ".format(rmb.get_package_details()))

    def end_package(self, package_name: str, package_attr: Dict):
        rmb =self.get_report_manager_base()
        self._send_message(text=":file_folder: Ending package {} ".format(rmb.get_package_details()))

    def start_suite(self, suite_name: str, suite_attr: Dict):
        rmb =self.get_report_manager_base()
        # self._send_message(text=":scroll: Starting suite {} ".format(rmb.get_suite_details()))

    def end_suite(self, suite_name: str, suite_attr: Dict):
        rmb = self.get_report_manager_base()
        self._send_message(text=":scroll: Ending suite {} ".format(rmb.get_suite_details()))

    def startTest(self, method_attr: Dict, test_name: str = "", usecase: str = "", description: str = ""):
        pass

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
        test_name = current_test.get_name()
        duration = current_test.get_duration()
        usecase = current_test.get_usecase()
        emoji = emojis.get(ending_state, f":{ending_state}:")

        self._send_message(text=f"{emoji} {test_name}:{usecase} {ending_state} {duration:.2f}sec - {end_reason}")
