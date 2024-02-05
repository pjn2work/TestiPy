from __future__ import annotations
import os

from typing import Union, List, Dict
from abc import abstractmethod, ABC

from testipy import get_exec_logger
from testipy.configs import default_config
from testipy.lib_modules.args_parser import ArgsParser
from testipy.lib_modules.start_arguments import StartArguments
from testipy.lib_modules.browser_manager import BrowserManager
from testipy.lib_modules import webhook_http_listener as HL
from testipy.reporter.package_manager import PackageDetails, SuiteDetails, TestDetails


_exec_logger = get_exec_logger()


class ReportInterface(ABC):

    def __init__(self, name: str = ""):
        self.name = name

    @abstractmethod
    def _startup_(self, selected_tests: Dict):
        pass

    @abstractmethod
    def _teardown_(self, end_state: str):
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


class ReportManagerAddons:

    def __init__(self, ap: ArgsParser, sa: StartArguments):
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

    def get_results_folder_filename(self, pd_sd_td: Union[PackageDetails, SuiteDetails, TestDetails], filename: str = "") -> str:
        if isinstance(pd_sd_td, PackageDetails):
            package_name = pd_sd_td.get_name()
            folders = package_name.split(default_config.separator_package)
        elif isinstance(pd_sd_td, SuiteDetails):
            package_name = pd_sd_td.package.get_name()
            suite_name = pd_sd_td.get_name()
            folders = package_name.split(default_config.separator_package)
            folders.append(suite_name)
        elif isinstance(pd_sd_td, TestDetails):
            package_name = pd_sd_td.suite.package.get_name()
            suite_name = pd_sd_td.suite.get_name()
            test_name = pd_sd_td.get_name()
            folders = package_name.split(default_config.separator_package)
            folders.append(suite_name)
            folders.append(test_name)
        else:
            raise TypeError(f"Expected PackageDetails or SuiteDetails or TestDetails, but got {type(pd_sd_td)}")

        fn = str(os.path.join(self.get_results_folder_runtime(), *folders, filename))

        return fn

    def generate_filename(self, current_test: TestDetails, filename: str = ".txt") -> str:
        return self.get_results_folder_filename(current_test, f'_{current_test.get_cycle():02}_{filename}')

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
            _exec_logger.error(f"RM Failed {self.get_bm().browser_name}: {ex}")
            self.browser_manager.setup_webdriver()

        return self.browser_manager.get_webdriver()

    def get_webdriver(self):
        return self.get_bm().get_webdriver()

    def close_webdriver(self):
        if self.browser_manager is not None:
            self.browser_manager.stop()
            self.browser_manager = None
    # </editor-fold>
