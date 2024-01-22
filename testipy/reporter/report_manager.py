#!/usr/bin/env python3
from __future__ import annotations
import os

from typing import List, Dict, Tuple, Any

from testipy.configs import enums_data, default_config
from testipy.helpers import format_duration
from testipy.lib_modules.common_methods import synchronized
from testipy.lib_modules import webhook_http_listener as HL
from testipy.lib_modules.textdecor import color_state
from testipy.lib_modules.args_parser import ArgsParser
from testipy.lib_modules.start_arguments import StartArguments
from testipy.lib_modules.py_inspector import get_class_from_file_with_prefix
from testipy.lib_modules.browser_manager import BrowserManager
from testipy.reporter.report_base import ReportBase, PackageDetails, SuiteDetails, TestDetails


class ReportManager(ReportBase):

    def __init__(self, execution_log, ap: ArgsParser, sa: StartArguments):
        super().__init__("ReportManager")

        self._reporters_list = dict()
        self._execution_log = execution_log
        self._ap = ap
        self._sa = sa

        self.browser_manager: BrowserManager = None

    def add_reporter(self, name, new_reporter_class) -> ReportManager:
        self._execution_log("DEBUG", f"Added reporter {name}")
        self._reporters_list[name] = new_reporter_class
        return self

    def get_report_manager_base(self):
        return super()

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

        package_name = current_test.get_package_name()
        suite_name = current_test.get_suite_name()
        test_name = current_test.get_name()

        folders = package_name.split(default_config.separator_package)
        folders.append(suite_name)
        folders.append(test_name)
        for folder in folders:
            fn = str(os.path.join(fn, folder))

        return fn + str(filename)

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

    def set_default_webdriver(self, default_browser_settings) -> ReportManager:
        if self.browser_manager is None:
            self.browser_manager = BrowserManager(self)

        self.browser_manager.set_default_webdriver(default_browser_settings)
        return self

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

    # <editor-fold desc="--- Common functions starts here ---">
    @synchronized
    def save_file(self, current_test, data, filename):
        filename = self.generate_filename(current_test, filename)

        attachment = super().save_file(current_test, data, filename)
        self.testInfo(current_test, f"Saving file '{filename}'", "DEBUG", attachment=attachment)
        for reporter_name, reporter in self._reporters_list.items():
            reporter.save_file(current_test, data, filename)

        return attachment

    @synchronized
    def copy_file(self, current_test, orig_filename="screenshot.png", dest_filename=None, data=None, delete_source=True):
        if not dest_filename:
            dest_filename = orig_filename
        dest_filename = self.generate_filename(current_test, dest_filename)

        if not data:
            try:
                with open(orig_filename, mode='rb') as file:
                    data = file.read()
            except Exception:
                self._execution_log("DEBUG", f"Failed to open file '{orig_filename}' for copy")

        if data:
            attachment = super().copy_file(current_test, orig_filename, dest_filename, data)
            self.testInfo(current_test, f"Copying file '{orig_filename}' to '{dest_filename}'", "DEBUG",
                          attachment=attachment)
            for reporter_name, reporter in self._reporters_list.items():
                reporter.copy_file(current_test, orig_filename, dest_filename, data)
        else:
            attachment = None

        if delete_source:
            try:
                os.remove(orig_filename)
            except Exception as ex:
                self._execution_log("DEBUG", f"Failed to delete file '{orig_filename}', {ex}")

        return attachment

    def __startup__(self, selected_tests: Dict) -> ReportManager:
        super().__startup__(selected_tests)
        for reporter_name, reporter in self._reporters_list.items():
            try:
                reporter.__startup__(selected_tests)
            except Exception as e:
                self._execution_log("CRITICAL", f"Internal error rm.__startup__ on {reporter_name}: {e}")
                if self.is_debugcode():
                    raise

        return self

    def __teardown__(self, end_state: str) -> ReportManager:
        super().__teardown__(end_state)
        end_state = self.end_state
        for reporter_name, reporter in self._reporters_list.items():
            try:
                reporter.__teardown__(end_state)
            except Exception as e:
                self._execution_log("CRITICAL", f"Internal error rm.__teardown__ on {reporter_name}: {e}")
                if self.is_debugcode():
                    raise

        # close web_browser and opened HTTP ports
        try:
            self.close_webdriver()
            self.close_all_http_ports()
        except:
            pass

        self._execution_log("INFO", f"{color_state(end_state)} All took {format_duration(self.pm.get_duration()):>10} [{self.pm.state_counter}]")
        return self

    def startPackage(self, name: str, package_attr: Dict) -> PackageDetails:
        pd = super().startPackage(name, package_attr)
        for reporter_name, reporter in self._reporters_list.items():
            try:
                reporter.startPackage(name, package_attr)
            except Exception as e:
                self._execution_log("CRITICAL", f"Internal error rm.startPackage on {reporter_name}: {e}")
                if self.is_debugcode():
                    raise

        return pd

    @synchronized
    def startSuite(self, pd: PackageDetails, name: str, suite_attr: Dict) -> SuiteDetails:
        sd = super().startSuite(pd, name, suite_attr)
        for reporter_name, reporter in self._reporters_list.items():
            try:
                reporter.startSuite(pd, name, suite_attr)
            except Exception as e:
                self._execution_log("CRITICAL", f"Internal error rm.startSuite on {reporter_name}: {e}")
                if self.is_debugcode():
                    raise

        return sd

    @synchronized
    def startTest(self, method_attr: Dict, test_name: str = "", usecase: str = "", description: str = "") -> TestDetails:
        current_test = super().startTest(method_attr, test_name, usecase, description)
        for reporter_name, reporter in self._reporters_list.items():
            try:
                reporter.startTest(current_test.get_attributes(), current_test.get_name(), usecase, description)
            except Exception as e:
                self._execution_log("CRITICAL", f"Internal error rm.startTest on {reporter_name}: {e}")
                if self.is_debugcode():
                    raise

        return current_test

    @synchronized
    def testInfo(self, current_test: TestDetails, info: str, level: str = "DEBUG", attachment: Dict = None) -> ReportManager:
        super().testInfo(current_test, info, level, attachment)
        for reporter_name, reporter in self._reporters_list.items():
            try:
                reporter.testInfo(current_test, info, str(level).upper(), attachment)
            except Exception as e:
                self._execution_log("CRITICAL", f"Internal error rm.testInfo on {reporter_name}: {e}")
                if self.is_debugcode():
                    raise

        return self

    @synchronized
    def testStep(self, current_test: TestDetails, state: str, reason_of_state: str = "", description: str = "", take_screenshot: bool = False, qty: int = 1, exc_value: BaseException = None) -> ReportManager:
        super().testStep(current_test, state, reason_of_state=str(reason_of_state), description=str(description), take_screenshot=take_screenshot, qty=qty, exc_value=exc_value)

        if take_screenshot and self.is_browser_setup():
            try:
                self.get_bm().take_screenshot(current_test)
            except Exception as e:
                self._execution_log("CRITICAL", f"Internal error rm.testStep.screenshot on {self.get_bm().name}: {e}")
                if self.is_debugcode():
                    raise

        for reporter_name, reporter in self._reporters_list.items():
            try:
                reporter.testStep(current_test, state, reason_of_state=str(reason_of_state), description=str(description), take_screenshot=take_screenshot, qty=qty, exc_value=exc_value)
            except Exception as e:
                self._execution_log("CRITICAL", f"Internal error rm.testStep on {reporter_name}: {e}")
                if self.is_debugcode():
                    raise

        return self

    def testPassed(self, current_test: TestDetails, reason_of_state="", exc_value: BaseException = None):
        self.endTest(current_test, enums_data.STATE_PASSED, reason_of_state, exc_value)

    def testSkipped(self, current_test: TestDetails, reason_of_state="", exc_value: BaseException = None):
        self.endTest(current_test, enums_data.STATE_SKIPPED, reason_of_state, exc_value)

    def testFailedKnownBug(self, current_test: TestDetails, reason_of_state="", exc_value: BaseException = None):
        self.endTest(current_test, enums_data.STATE_FAILED_KNOWN_BUG, reason_of_state, exc_value)

    def testFailed(self, current_test: TestDetails, reason_of_state="", exc_value: BaseException = None):
        self.endTest(current_test, enums_data.STATE_FAILED, reason_of_state, exc_value)

    @synchronized
    def endTest(self, current_test: TestDetails, state: str = enums_data.STATE_PASSED, reason_of_state="", exc_value: BaseException = None) -> ReportManager:
        super().endTest(current_test, state, reason_of_state, exc_value)
        for reporter_name, reporter in self._reporters_list.items():
            try:
                reporter.endTest(current_test, state, reason_of_state, exc_value)
            except Exception as e:
                self._execution_log("CRITICAL", f"Internal error rm.endTest({state}) on {reporter_name}: {e}")
                if self.is_debugcode():
                    raise

        return self

    @synchronized
    def endSuite(self, sd: SuiteDetails) -> ReportManager:
        super().endSuite(sd)
        for reporter_name, reporter in self._reporters_list.items():
            try:
                reporter.endSuite(sd)
            except Exception as e:
                self._execution_log("CRITICAL", f"Internal error rm.endSuite on {reporter_name}: {e}")
                if self.is_debugcode():
                    raise

        return self

    def endPackage(self, pd: PackageDetails) -> ReportManager:
        super().endPackage(pd)
        for reporter_name, reporter in self._reporters_list.items():
            try:
                reporter.endPackage(pd)
            except Exception as e:
                self._execution_log("CRITICAL", f"Internal error rm.endPackage on {reporter_name}: {e}")
                if self.is_debugcode():
                    raise

        return self

    @synchronized
    def showStatus(self, message: str) -> ReportManager:
        for reporter_name, reporter in self._reporters_list.items():
            try:
                reporter.showStatus(message)
            except Exception as e:
                self._execution_log("CRITICAL", f"Internal error rm.showStatus on {reporter_name}: {e}")
                if self.is_debugcode():
                    raise

        return self

    @synchronized
    def showAlertMessage(self, message: str) -> ReportManager:
        for reporter_name, reporter in self._reporters_list.items():
            try:
                reporter.showAlertMessage(message)
            except Exception as e:
                self._execution_log("CRITICAL", f"Internal error rm.showMessage on {reporter_name}: {e}")
                if self.is_debugcode():
                    raise

        return self

    @synchronized
    def inputPromptMessage(self, message: str, default_value: str = ""):
        result = None
        for reporter_name, reporter in self._reporters_list.items():
            try:
                res = reporter.inputPromptMessage(message, default_value)
                if result is None and res:
                    result = res
            except Exception as e:
                self._execution_log("CRITICAL", f"Internal error rm.inputMessage on {reporter_name}: {e}")
                if self.is_debugcode():
                    raise

        return result

    # </editor-fold>


def build_report_manager_with_reporters(execution_log, ap: ArgsParser, sa: StartArguments):
    # create report manager
    rm = ReportManager(execution_log, ap, sa)

    def _add_reporter(rep_name, rep_class):
        try:
            rep = rep_class(rm, sa)
            rm.add_reporter(rep_name, rep)
        except Exception as ex:
            execution_log("WARNING", f"Internal error on build_report_manager_with_reporters for {rep_name} {ex}")

    for rep_name in sa.valid_reporters:
        reporter_name = f"reporter_{rep_name}.py"
        _, rep_class = _get_report_by_name_from_folder(execution_log, reporter_name)
        if rep_class:
            _add_reporter(rep_name, rep_class)
        else:
            execution_log("WARNING", f"Reporter {reporter_name} not found inside reporters folder!")

    return rm


def _get_report_by_name_from_folder(execution_log, reporter_name: str) -> Tuple[str, Any]:
    reporters_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reporters")

    try:
        for filename in os.listdir(reporters_folder):
            if filename == reporter_name:
                fpn = os.path.join(reporters_folder, filename)
                return get_class_from_file_with_prefix(fpn, "Reporter")
    except Exception as ex:
        execution_log("WARNING", f"Internal error on get_report_by_name_from_folder for {reporter_name} {ex}")

    return "", None
