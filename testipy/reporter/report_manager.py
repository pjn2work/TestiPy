#!/usr/bin/env python3

import os

from typing import List, Dict, Tuple, Any

from testipy.configs import enums_data, default_config
from testipy.lib_modules import webhook_http_listener as HL
from testipy.lib_modules.textdecor import color_status
from testipy.lib_modules.common_methods import format_duration
from testipy.lib_modules.args_parser import ArgsParser
from testipy.lib_modules.start_arguments import StartArguments
from testipy.lib_modules.py_inspector import get_class_from_file_with_prefix
from testipy.lib_modules.browser_manager import BrowserManager
from testipy.reporter.report_base import ReportBase, TestDetails


class ReportManager(ReportBase):

    def __init__(self, execution_log, selected_tests, ap: ArgsParser, sa: StartArguments):
        super().__init__("ReportManager")

        self._reporters_list = dict()
        self._test_running_list = dict()
        self._execution_log = execution_log
        self._selected_tests = selected_tests
        self._ap = ap
        self._sa = sa

        self.browser_manager: BrowserManager = None

    def _add_reporter(self, name, new_reporter_class):
        self._execution_log("DEBUG", f"Added reporter {name}")
        new_reporter_class.set_report_manager_base(self)  # Add myself as the ReportManager on this new_reporter_class
        self._reporters_list[name] = new_reporter_class
        return self

    def get_selected_tests(self) -> List:
        return self._selected_tests

    def get_ap(self) -> ArgsParser:
        return self._ap

    def has_ap_flag(self, key: str) -> bool:
        return self._ap.has_flag_or_option(key)

    def get_project_name(self) -> str:
        return self._sa.project_name

    def get_environment_name(self) -> str:
        return self._sa.environment_name

    def get_foldername_runtime(self) -> str:
        return self._sa.foldername_runtime

    def get_results_folder_runtime(self) -> str:
        return self._sa.results_folder_runtime

    def _get_full_path_tests_scripts_foldername_deprecated(self) -> str:
        return self._sa.full_path_tests_scripts_foldername

    def _get_full_path_package_foldername_deprecated(self, package_name) -> str:
        return os.path.join(self._get_full_path_tests_scripts_foldername_deprecated(),
                            package_name.replace(default_config.separator_package, os.sep))

    def get_results_folder_filename(self, current_test: TestDetails = None, filename: str = "") -> str:
        fn = self.get_results_folder_runtime()

        package_name = super().get_package_name()
        suite_name = super().get_suite_name()
        test_name = current_test.get_test_name() if current_test else ""

        folders = package_name.split(default_config.separator_package)
        folders.append(suite_name)
        folders.append(test_name)
        for folder in folders:
            fn = str(os.path.join(fn, folder))

        return fn + str(filename)

    def generate_filename(self, current_test, filename=".txt") -> str:
        return self.get_results_folder_filename(current_test, f'_{current_test.get_cycle():02}_{filename}')

    # <editor-fold desc="--- Engine ---">
    def get_test_running_list(self, meid):
        if meid in self._test_running_list:
            return self._test_running_list[meid]
        return []

    def add_test_running(self, current_test):
        meid = current_test.get_method_id()
        if meid not in self._test_running_list:
            self._test_running_list[meid] = list()
        self._test_running_list[meid].append(current_test)
        return self

    def remove_test_running(self, current_test):
        meid = current_test.get_method_id()
        if meid in self._test_running_list and current_test in self._test_running_list[meid]:
            self._test_running_list[meid].remove(current_test)
        return self

    def get_test_list_by_method_id(self, meid: int):
        result_tests_list = list()
        for test_name, test_list in super().get_test_list().items():
            for current_test in test_list:
                if current_test.get_method_id() == meid:
                    result_tests_list.append(current_test)
        return result_tests_list
    # </editor-fold>

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
    def get_report_manager_base(self):
        return super()

    def save_file(self, current_test, data, filename):
        filename = self.generate_filename(current_test, filename)

        attachment = super().save_file(current_test, data, filename)
        for reporter_name, reporter in self._reporters_list.items():
            reporter.save_file(current_test, data, filename)

        return attachment

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
            for reporter_name, reporter in self._reporters_list.items():
                reporter.copy_file(current_test, orig_filename, dest_filename, data)
        else:
            attachment = None

        if delete_source:
            try:
                os.remove(orig_filename)
            except Exception:
                self._execution_log("DEBUG", f"Failed to delete file '{orig_filename}'")

        return attachment

    def is_debugcode(self):
        return self._sa.debugcode

    @staticmethod
    def __format_test_structure(selected_tests: List) -> Dict:
        formatted_test_list = []
        for package in selected_tests:
            package_name = package["package_name"]

            for suite in sorted(package["suite_list"], key=lambda x: (x[enums_data.TAG_PRIO], x[enums_data.TAG_NAME]), reverse=True):
                suite_name = suite[enums_data.TAG_NAME]
                suite_prio = suite[enums_data.TAG_PRIO]

                # for test in sorted(suite["test_list"], key=lambda x: x[TAG_PRIO], reverse=True):
                for test in suite["test_list"]:
                    method_id = test["method_id"]
                    test_name = test[enums_data.TAG_NAME]
                    test_prio = test[enums_data.TAG_PRIO]
                    test_level = test[enums_data.TAG_LEVEL]
                    test_tags = " ".join(test[enums_data.TAG_TAG])
                    test_features = test[enums_data.TAG_FEATURES]
                    test_number = test[enums_data.TAG_TESTNUMBER]
                    test_comment = test["test_comment"]  # if test["test_comment"] else ""

                    formatted_test_list.append([method_id, package_name, suite_prio, suite_name, test_prio, test_name, test_level, test_tags, test_features, test_number, test_comment])

        return dict(headers=["meid", "Package", "Sp", "Suite", "Tp", "Test", "Level", "TAGs", "Features", "Number", "Description"],
                    data=formatted_test_list)

    def __startup__(self, selected_tests):
        fts_selected_tests = self.__format_test_structure(selected_tests)
        super().__startup__(fts_selected_tests)
        for reporter_name, reporter in self._reporters_list.items():
            try:
                reporter.__startup__(fts_selected_tests)
            except Exception as e:
                if self.is_debugcode():
                    raise
                self._execution_log("CRITICAL", f"Internal error rm.__startup__ on {reporter_name}: {e}")

        return self

    def __teardown__(self, end_state):
        totals = super().get_reporter_counter()
        total_failed = sum([totals[state] for state in default_config.count_as_failed_states])
        end_state = enums_data.STATE_FAILED if total_failed > 0 else enums_data.STATE_PASSED

        super().__teardown__(end_state)
        for reporter_name, reporter in self._reporters_list.items():
            try:
                reporter.__teardown__(end_state)
            except Exception as e:
                if self.is_debugcode():
                    raise
                self._execution_log("CRITICAL", f"Internal error rm.__teardown__ on {reporter_name}: {e}")

        # close web_browser and opened HTTP ports
        try:
            self.close_webdriver()
            self.close_all_http_ports()
        except:
            pass

        self._execution_log("INFO", f"{color_status(end_state)} Tests took {format_duration(super().get_reporter_duration())} [{totals}]")
        return self

    def startPackage(self, name):
        super().startPackage(name)
        for reporter_name, reporter in self._reporters_list.items():
            try:
                reporter.startPackage(name)
            except Exception as e:
                if self.is_debugcode():
                    raise
                self._execution_log("CRITICAL", f"Internal error rm.startPackage on {reporter_name}: {e}")

        return self

    def startSuite(self, name, attr=None):
        super().startSuite(name, attr)
        for reporter_name, reporter in self._reporters_list.items():
            try:
                reporter.startSuite(name, attr)
            except Exception as e:
                if self.is_debugcode():
                    raise
                self._execution_log("CRITICAL", f"Internal error rm.startSuite on {reporter_name}: {e}")

        return self

    def startTest(self, attr: Dict, test_name: str = "", usecase: str = "", description: str = "") -> TestDetails:
        current_test = super().startTest(attr, test_name, usecase, description)
        self.add_test_running(current_test)
        for reporter_name, reporter in self._reporters_list.items():
            try:
                reporter.startTest(current_test.get_attributes(), current_test.get_name(), usecase, description)
            except Exception as e:
                if self.is_debugcode():
                    raise
                self._execution_log("CRITICAL", f"Internal error rm.startTest on {reporter_name}: {e}")

        return current_test

    def testInfo(self, current_test, info, level="DEBUG", attachment=None):
        super().testInfo(current_test, info, level, attachment)
        for reporter_name, reporter in self._reporters_list.items():
            try:
                reporter.testInfo(current_test, info, str(level).upper(), attachment)
            except Exception as e:
                if self.is_debugcode():
                    raise
                self._execution_log("CRITICAL", f"Internal error rm.testInfo on {reporter_name}: {e}")

        return self

    def testStep(self, current_test, state: str, reason_of_state: str = "", description: str = "", take_screenshot: bool = False, qty: int = 1, exc_value: BaseException = None):
        super().testStep(current_test, state, reason_of_state=str(reason_of_state), description=str(description), take_screenshot=take_screenshot, qty=qty, exc_value=exc_value)

        if take_screenshot and self.is_browser_setup():
            try:
                self.get_bm().take_screenshot(current_test)
            except Exception as e:
                if self.is_debugcode():
                    raise
                self._execution_log("CRITICAL", f"Internal error rm.testStep.screenshot on {self.get_bm().name}: {e}")

        for reporter_name, reporter in self._reporters_list.items():
            try:
                reporter.testStep(current_test, state, reason_of_state=str(reason_of_state), description=str(description), take_screenshot=take_screenshot, qty=qty, exc_value=exc_value)
            except Exception as e:
                if self.is_debugcode():
                    raise
                self._execution_log("CRITICAL", f"Internal error rm.testStep on {reporter_name}: {e}")

        return self

    def testSkipped(self, current_test, reason_of_state="", exc_value: BaseException = None):
        super().testSkipped(current_test, reason_of_state, exc_value)
        self.remove_test_running(current_test)
        for reporter_name, reporter in self._reporters_list.items():
            try:
                reporter.testSkipped(current_test, reason_of_state, exc_value)
            except Exception as e:
                if self.is_debugcode():
                    raise
                self._execution_log("CRITICAL", f"Internal error rm.testSkipped on {reporter_name}: {e}")

        return self

    def testPassed(self, current_test, reason_of_state="", exc_value: BaseException = None):
        super().testPassed(current_test, reason_of_state, exc_value)
        self.remove_test_running(current_test)
        for reporter_name, reporter in self._reporters_list.items():
            try:
                reporter.testPassed(current_test, reason_of_state, exc_value)
            except Exception as e:
                if self.is_debugcode():
                    raise
                self._execution_log("CRITICAL", f"Internal error rm.testPassed on {reporter_name}: {e}")

        return self

    def testFailed(self, current_test, reason_of_state="", exc_value: BaseException = None):
        super().testFailed(current_test, reason_of_state, exc_value)
        self.remove_test_running(current_test)
        for reporter_name, reporter in self._reporters_list.items():
            try:
                reporter.testFailed(current_test, reason_of_state, exc_value)
            except Exception as e:
                if self.is_debugcode():
                    raise
                self._execution_log("CRITICAL", f"Internal error rm.testFailed on {reporter_name}: {e}")

        return self

    def testFailedKnownBug(self, current_test, reason_of_state="", exc_value: BaseException = None):
        super().testFailedKnownBug(current_test, reason_of_state, exc_value)
        self.remove_test_running(current_test)
        for reporter_name, reporter in self._reporters_list.items():
            try:
                reporter.testFailedKnownBug(current_test, reason_of_state, exc_value)
            except Exception as e:
                if self.is_debugcode():
                    raise
                self._execution_log("CRITICAL", f"Internal error rm.testFailedKnownBug on {reporter_name}: {e}")

        return self

    def testEndAs(self, current_test, state: str = enums_data.STATE_PASSED, reason_of_state="", exc_value: BaseException = None):
        if state == enums_data.STATE_PASSED:
            self.testPassed(current_test, reason_of_state, exc_value)
        elif state == enums_data.STATE_SKIPPED:
            self.testSkipped(current_test, reason_of_state, exc_value)
        elif state == enums_data.STATE_FAILED_KNOWN_BUG:
            self.testFailedKnownBug(current_test, reason_of_state, exc_value)
        else:
            self.testFailed(current_test, reason_of_state, exc_value)
        return self

    def endSuite(self):
        super().endSuite()
        for reporter_name, reporter in self._reporters_list.items():
            try:
                reporter.endSuite()
            except Exception as e:
                if self.is_debugcode():
                    raise
                self._execution_log("CRITICAL", f"Internal error rm.endSuite on {reporter_name}: {e}")

        return self

    def endPackage(self):
        super().endPackage()
        for reporter_name, reporter in self._reporters_list.items():
            try:
                reporter.endPackage()
            except Exception as e:
                if self.is_debugcode():
                    raise
                self._execution_log("CRITICAL", f"Internal error rm.endPackage on {reporter_name}: {e}")

        return self

    def showStatus(self, message: str):
        for reporter_name, reporter in self._reporters_list.items():
            try:
                reporter.showStatus(message)
            except Exception as e:
                if self.is_debugcode():
                    raise
                self._execution_log("CRITICAL", f"Internal error rm.showStatus on {reporter_name}: {e}")

        return self

    def showAlertMessage(self, message: str):
        for reporter_name, reporter in self._reporters_list.items():
            try:
                reporter.showAlertMessage(message)
            except Exception as e:
                if self.is_debugcode():
                    raise
                self._execution_log("CRITICAL", f"Internal error rm.showMessage on {reporter_name}: {e}")

        return self

    def inputPromptMessage(self, message: str, default_value: str = ""):
        result = None
        for reporter_name, reporter in self._reporters_list.items():
            try:
                res = reporter.inputPromptMessage(message, default_value)
                if result is None and res:
                    result = res
            except Exception as e:
                if self.is_debugcode():
                    raise
                self._execution_log("CRITICAL", f"Internal error rm.inputMessage on {reporter_name}: {e}")

        return result

    # </editor-fold>


def build_report_manager_with_reporters(execution_log, selected_tests, ap: ArgsParser, sa: StartArguments):
    # create report manager
    rm = ReportManager(execution_log, selected_tests, ap, sa)

    def _add_reporter(rep_name, rep_class):
        try:
            rep = rep_class(rm, sa)
            rm._add_reporter(rep_name, rep)
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
