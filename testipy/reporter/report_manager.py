from __future__ import annotations
import os

from typing import Dict, Tuple, Any

from testipy import get_exec_logger
from testipy.configs import enums_data
from testipy.helpers import format_duration
from testipy.lib_modules.common_methods import synchronized
from testipy.lib_modules.textdecor import color_state
from testipy.lib_modules.args_parser import ArgsParser
from testipy.lib_modules.start_arguments import StartArguments
from testipy.lib_modules.py_inspector import get_class_from_file_with_prefix
from testipy.reporter.report_base import ReportBase, PackageDetails, SuiteDetails, TestDetails
from testipy.reporter.report_interfaces import ReportManagerAddons


_exec_logger = get_exec_logger()


class ReportManager(ReportBase, ReportManagerAddons):

    def __init__(self, ap: ArgsParser, sa: StartArguments):
        ReportBase.__init__(self, "ReportManager")
        ReportManagerAddons.__init__(self, ap, sa)

        self._reporters_list = dict()

    def add_reporter(self, name, new_reporter_class):
        _exec_logger.debug(f"Added reporter {name}")
        self._reporters_list[name] = new_reporter_class

    # <editor-fold desc="--- Common functions starts here ---">
    @synchronized
    def save_file(self, current_test: TestDetails, data, filename: str) -> Dict:
        filename = self.generate_filename(current_test, filename)

        attachment = super().save_file(current_test, data, filename)
        self.test_info(current_test, f"Saving file '{filename}'", "DEBUG", attachment=attachment)
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
                _exec_logger.debug(f"Failed to open file '{orig_filename}' for copy")

        if data:
            attachment = super().copy_file(current_test, orig_filename, dest_filename, data)
            self.test_info(current_test, f"Copying file '{orig_filename}' to '{dest_filename}'", "DEBUG", attachment=attachment)
            for reporter_name, reporter in self._reporters_list.items():
                reporter.copy_file(current_test, orig_filename, dest_filename, data)
        else:
            attachment = None

        if delete_source:
            try:
                os.remove(orig_filename)
            except Exception as ex:
                _exec_logger.debug(f"Failed to delete file '{orig_filename}', {ex}")

        return attachment

    def _startup_(self, selected_tests: Dict):
        super()._startup_(selected_tests)
        for reporter_name, reporter in self._reporters_list.items():
            try:
                reporter._startup_(selected_tests)
            except Exception as e:
                _exec_logger.critical(f"Internal error rm._startup_ on {reporter_name}: {e}")
                if self.is_debugcode():
                    raise

    def _teardown_(self, end_state: str):
        super()._teardown_(end_state)
        end_state = self.end_state
        for reporter_name, reporter in self._reporters_list.items():
            try:
                reporter._teardown_(end_state)
            except Exception as e:
                _exec_logger.critical(f"Internal error rm._teardown_ on {reporter_name}: {e}")
                if self.is_debugcode():
                    raise

        # close web_browser and opened HTTP ports
        try:
            self.close_webdriver()
            self.close_all_http_ports()
        except:
            pass

        _exec_logger.info(f"{color_state(end_state)} All took {format_duration(self.pm.get_duration()):>10} [{self.pm.state_counter}]")

    @synchronized
    def startPackage(self, name: str, package_attr: Dict) -> PackageDetails:
        pd = super().startPackage(name, package_attr)
        self.start_package(pd)
        return pd

    def start_package(self, pd: PackageDetails):
        for reporter_name, reporter in self._reporters_list.items():
            try:
                reporter.start_package(pd)
            except Exception as e:
                _exec_logger.critical(f"Internal error rm.start_package on {reporter_name}: {e}")
                if self.is_debugcode():
                    raise

    @synchronized
    def startSuite(self, pd: PackageDetails, name: str, suite_attr: Dict) -> SuiteDetails:
        sd = super().startSuite(pd, name, suite_attr)
        self.start_suite(sd)
        return sd

    def start_suite(self, sd: SuiteDetails):
        for reporter_name, reporter in self._reporters_list.items():
            try:
                reporter.start_suite(sd)
            except Exception as e:
                _exec_logger.critical(f"Internal error rm.startSuite on {reporter_name}: {e}")
                if self.is_debugcode():
                    raise
        return sd

    @synchronized
    def startTest(self, method_attr: Dict, test_name: str = "", usecase: str = "", description: str = "") -> TestDetails:
        td = super().startTest(method_attr, test_name, usecase, description)
        self.start_test(td)
        return td

    def start_test(self, current_test: TestDetails):
        for reporter_name, reporter in self._reporters_list.items():
            try:
                reporter.start_test(current_test)
            except Exception as e:
                _exec_logger.critical(f"Internal error rm.start_test on {reporter_name}: {e}")
                if self.is_debugcode():
                    raise

    @synchronized
    def test_info(self, current_test: TestDetails, info: str, level: str = "DEBUG", attachment: Dict = None) -> ReportManager:
        super().test_info(current_test, info, level, attachment)
        for reporter_name, reporter in self._reporters_list.items():
            try:
                reporter.test_info(current_test, info, str(level).upper(), attachment)
            except Exception as e:
                _exec_logger.critical(f"Internal error rm.testInfo on {reporter_name}: {e}")
                if self.is_debugcode():
                    raise

        return self

    @synchronized
    def test_step(self, current_test: TestDetails, state: str, reason_of_state: str = "", description: str = "", take_screenshot: bool = False, qty: int = 1, exc_value: BaseException = None) -> ReportManager:
        super().test_step(current_test, state, reason_of_state=str(reason_of_state), description=str(description), take_screenshot=take_screenshot, qty=qty, exc_value=exc_value)

        if take_screenshot and self.is_browser_setup():
            try:
                self.get_bm().take_screenshot(current_test)
            except Exception as e:
                _exec_logger.critical(f"Internal error rm.testStep.screenshot on {self.get_bm().name}: {e}")
                if self.is_debugcode():
                    raise

        for reporter_name, reporter in self._reporters_list.items():
            try:
                reporter.test_step(current_test, state, reason_of_state=str(reason_of_state), description=str(description), take_screenshot=take_screenshot, qty=qty, exc_value=exc_value)
            except Exception as e:
                _exec_logger.critical(f"Internal error rm.testStep on {reporter_name}: {e}")
                if self.is_debugcode():
                    raise

        return self

    def testPassed(self, current_test: TestDetails, reason_of_state="", exc_value: BaseException = None):
        self.end_test(current_test, enums_data.STATE_PASSED, reason_of_state, exc_value)

    def testSkipped(self, current_test: TestDetails, reason_of_state="", exc_value: BaseException = None):
        self.end_test(current_test, enums_data.STATE_SKIPPED, reason_of_state, exc_value)

    def testFailedKnownBug(self, current_test: TestDetails, reason_of_state="", exc_value: BaseException = None):
        self.end_test(current_test, enums_data.STATE_FAILED_KNOWN_BUG, reason_of_state, exc_value)

    def testFailed(self, current_test: TestDetails, reason_of_state="", exc_value: BaseException = None):
        self.end_test(current_test, enums_data.STATE_FAILED, reason_of_state, exc_value)

    @synchronized
    def end_test(self, current_test: TestDetails, state: str = enums_data.STATE_PASSED, reason_of_state="", exc_value: BaseException = None):
        super().end_test(current_test, state, reason_of_state, exc_value)
        for reporter_name, reporter in self._reporters_list.items():
            try:
                reporter.end_test(current_test, state, reason_of_state, exc_value)
            except Exception as e:
                _exec_logger.critical(f"Internal error rm.endTest({state}) on {reporter_name}: {e}")
                if self.is_debugcode():
                    raise

    @synchronized
    def end_suite(self, sd: SuiteDetails):
        super().end_suite(sd)
        for reporter_name, reporter in self._reporters_list.items():
            try:
                reporter.end_suite(sd)
            except Exception as e:
                _exec_logger.critical(f"Internal error rm.endSuite on {reporter_name}: {e}")
                if self.is_debugcode():
                    raise

    @synchronized
    def end_package(self, pd: PackageDetails):
        super().end_package(pd)
        for reporter_name, reporter in self._reporters_list.items():
            try:
                reporter.end_package(pd)
            except Exception as e:
                _exec_logger.critical(f"Internal error rm.endPackage on {reporter_name}: {e}")
                if self.is_debugcode():
                    raise

    @synchronized
    def show_status(self, message: str):
        for reporter_name, reporter in self._reporters_list.items():
            try:
                reporter.show_status(message)
            except Exception as e:
                _exec_logger.critical(f"Internal error rm.showStatus on {reporter_name}: {e}")
                if self.is_debugcode():
                    raise

    @synchronized
    def show_alert_message(self, message: str):
        for reporter_name, reporter in self._reporters_list.items():
            try:
                reporter.show_alert_message(message)
            except Exception as e:
                _exec_logger.critical(f"Internal error rm.showMessage on {reporter_name}: {e}")
                if self.is_debugcode():
                    raise

    @synchronized
    def input_prompt_message(self, message: str, default_value: str = "") -> str:
        result = None
        for reporter_name, reporter in self._reporters_list.items():
            try:
                res = reporter.input_prompt_message(message, default_value)
                if result is None and res:
                    result = res
            except Exception as e:
                _exec_logger.critical(f"Internal error rm.inputMessage on {reporter_name}: {e}")
                if self.is_debugcode():
                    raise

        return result

    # </editor-fold>


def build_report_manager_with_reporters(ap: ArgsParser, sa: StartArguments):
    # create report manager
    rm = ReportManager(ap, sa)

    def _add_reporter(rep_name, rep_class):
        try:
            rep = rep_class(rm, sa)
            rm.add_reporter(rep_name, rep)
        except Exception as ex:
            _exec_logger.warning(f"Internal error on build_report_manager_with_reporters for {rep_name} {ex}")

    for rep_name in sa.valid_reporters:
        reporter_name = f"reporter_{rep_name}.py"
        _, rep_class = _get_report_by_name_from_folder(reporter_name)
        if rep_class:
            _add_reporter(rep_name, rep_class)
        else:
            _exec_logger.warning(f"Reporter {reporter_name} not found inside reporters folder!")

    return rm


def _get_report_by_name_from_folder(reporter_name: str) -> Tuple[str, Any]:
    reporters_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reporters")

    try:
        for filename in os.listdir(reporters_folder):
            if filename == reporter_name:
                fpn = os.path.join(reporters_folder, filename)
                return get_class_from_file_with_prefix(fpn, "Reporter")
    except Exception as ex:
        _exec_logger.warning(f"Internal error on get_report_by_name_from_folder for {reporter_name} {ex}")

    return "", None
