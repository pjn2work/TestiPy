from __future__ import annotations
import os

from typing import List, Dict
from abc import abstractmethod, ABC

from testipy.configs import enums_data, default_config
from testipy.lib_modules.args_parser import ArgsParser
from testipy.lib_modules.start_arguments import StartArguments
from testipy.lib_modules.browser_manager import BrowserManager
from testipy.lib_modules import webhook_http_listener as HL
from testipy.reporter.package_manager import PackageDetails, SuiteDetails, TestDetails


class ReportInterface(ABC):

    def __init__(self, name: str = ""):
        self.name = name

    @abstractmethod
    def __startup__(self, selected_tests: Dict):
        pass

    @abstractmethod
    def __teardown__(self, end_state: str):
        pass

    @abstractmethod
    def start_package(self, pd: PackageDetails):
        pass

    @abstractmethod
    def end_package(self, pd: PackageDetails):
        pass

    @abstractmethod
    def start_suite(self, sd: SuiteDetails):
        pass

    @abstractmethod
    def end_suite(self, sd: SuiteDetails):
        pass

    @abstractmethod
    def start_test(self, current_test: TestDetails):
        pass

    @abstractmethod
    def test_info(self, current_test: TestDetails, info: str, level: str, attachment: Dict=None):
        pass

    @abstractmethod
    def test_step(self, current_test: TestDetails, state: str, reason_of_state: str = "", description: str = "", take_screenshot: bool = False, qty: int = 1, exc_value: BaseException = None):
        pass

    @abstractmethod
    def end_test(self, current_test: TestDetails, state: str, reason_of_state: str, exc_value: BaseException = None):
        pass

    @abstractmethod
    def save_file(self, current_test: TestDetails, data, filename) -> Dict:
        pass

    @abstractmethod
    def copy_file(self, current_test: TestDetails, orig_filename, dest_filename, data) -> Dict:
        pass

    @abstractmethod
    def show_status(self, message: str):
        pass

    @abstractmethod
    def show_alert_message(self, message: str):
        pass

    @abstractmethod
    def input_prompt_message(self, message: str, default_value: str = ""):
        pass


class ReportManagerClient:

    def __init__(self, execution_log, ap: ArgsParser, sa: StartArguments):
        self._execution_log = execution_log
        self._ap = ap
        self._sa = sa

        self.browser_manager: BrowserManager = None

    def get_ap(self) -> ArgsParser:
        return self._ap

    def has_ap_flag(self, key: str) -> bool:
        return self._ap.has_flag_or_option(key)

    def is_debugcode(self):
        return self._sa.debugcode

    def get_project_name(self) -> str:
        return self._sa.project_name

    def get_environment_name(self) -> str:
        return self._sa.environment_name

    def get_foldername_runtime(self) -> str:
        return self._sa.foldername_runtime

    def get_results_folder_runtime(self) -> str:
        return self._sa.full_path_results_folder_runtime

    def get_full_path_tests_scripts_foldername(self) -> str:
        return self._sa.full_path_tests_scripts_foldername

    def get_results_folder_filename(self, current_test: TestDetails, filename: str = "") -> str:
        fn = self.get_results_folder_runtime()

        package_name = current_test.suite.package.get_name()
        suite_name = current_test.suite.get_name()
        test_name = current_test.get_name()

        folders = package_name.split(default_config.separator_package)
        folders.append(suite_name)
        folders.append(test_name)
        for folder in folders:
            fn = str(os.path.join(fn, folder))

        return fn + str(filename)

        # <editor-fold desc="--- HTTP Server ---">

    @staticmethod
    def start_http_servers(tcp_ports_list: List, listeners_list: List = None):
        HL.start_http_servers(tcp_ports_list, listeners_list, blocking=False, verbose=False)

    @staticmethod
    def set_listeners(listeners_list: List, append: bool = False):
        HL.set_listeners(listeners_list, append=append)

    @staticmethod
    def close_all_http_ports():
        HL.close_all_http_ports()

    @staticmethod
    def close_http_port(port: int):
        HL.close_http_port(port)

    @staticmethod
    def is_port_open(port: int) -> bool:
        return HL.close_http_port(port)

    @staticmethod
    def get_last_message_received() -> Dict:
        return HL.get_last_message_received()

    # </editor-fold>

    # <editor-fold desc="--- Browser Manager ---">
    def is_browser_setup(self) -> bool:
        return self.browser_manager is not None and self.browser_manager.is_browser_setup()

    def set_default_webdriver(self, default_browser_settings):
        if self.browser_manager is None:
            self.browser_manager = BrowserManager(self)

        self.browser_manager.set_default_webdriver(default_browser_settings)

    def get_bm(self) -> BrowserManager:
        if self.browser_manager is None:
            self.browser_manager = BrowserManager(self)

        if not self.browser_manager.is_browser_setup():
            return self.browser_manager.setup_webdriver()

        return self.browser_manager

    def setup_webdriver(self,
                        browser_name: str = None,
                        option_arguments: list = [],
                        option_preferences: dict = {},
                        method_args: dict = {},
                        device: dict = {},
                        is_custom: bool = True, **trash):
        if self.browser_manager is None:
            self.browser_manager = BrowserManager(self)

        try:
            self.browser_manager.setup_webdriver(browser_name=browser_name,
                                                 option_arguments=option_arguments,
                                                 option_preferences=option_preferences,
                                                 method_args=method_args,
                                                 device=device,
                                                 is_custom=is_custom)
        except Exception as ex:
            self._execution_log("ERROR", f"RM Failed {self.get_bm().browser_name}: {ex}")
            self.browser_manager.setup_webdriver()

        return self.browser_manager.get_webdriver()

    def get_webdriver(self):
        return self.get_bm().get_webdriver()

    def close_webdriver(self):
        if self.browser_manager is not None:
            self.browser_manager.stop()
            self.browser_manager = None
    # </editor-fold>
