from __future__ import annotations

from typing import Dict
from abc import abstractmethod, ABC

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
    def startPackage(self, package_name: str, package_attr: Dict) -> PackageDetails:
        pass

    @abstractmethod
    def endPackage(self, pd: PackageDetails):
        pass

    @abstractmethod
    def startSuite(self, pd: PackageDetails, suite_name: str, suite_attr: Dict) -> SuiteDetails:
        pass

    @abstractmethod
    def endSuite(self, sd: SuiteDetails):
        pass

    @abstractmethod
    def startTest(self, method_attr: Dict, test_name: str = "", usecase: str = "", description: str = ""):
        pass

    @abstractmethod
    def testInfo(self, current_test: TestDetails, info: str, level: str, attachment: Dict=None):
        pass

    @abstractmethod
    def testStep(self, current_test: TestDetails, state: str, reason_of_state: str = "", description: str = "", take_screenshot: bool = False, qty: int = 1, exc_value: BaseException = None):
        pass

    @abstractmethod
    def endTest(self, current_test: TestDetails, state: str, reason_of_state: str, exc_value: BaseException = None):
        pass

    @abstractmethod
    def save_file(self, current_test: TestDetails, data, filename) -> Dict:
        pass

    @abstractmethod
    def copy_file(self, current_test: TestDetails, orig_filename, dest_filename, data) -> Dict:
        pass

    @abstractmethod
    def showStatus(self, message: str):
        pass

    @abstractmethod
    def showAlertMessage(self, message: str):
        pass

    @abstractmethod
    def inputPromptMessage(self, message: str, default_value: str = ""):
        pass
