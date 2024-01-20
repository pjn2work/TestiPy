from __future__ import annotations

from typing import Dict
from abc import abstractmethod, ABC


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
    def startPackage(self, package_name: str, package_attr: Dict):
        pass

    @abstractmethod
    def endPackage(self, package_name: str, package_attr: Dict):
        pass

    @abstractmethod
    def startSuite(self, suite_name: str, suite_attr: Dict):
        pass

    @abstractmethod
    def endSuite(self, suite_name: str, suite_attr: Dict):
        pass

    @abstractmethod
    def startTest(self, method_attr: Dict, test_name: str = "", usecase: str = "", description: str = ""):
        pass

    @abstractmethod
    def testInfo(self, current_test, info, level, attachment=None):
        pass

    @abstractmethod
    def testStep(self, current_test, state: str, reason_of_state: str = "", description: str = "", take_screenshot: bool = False, qty: int = 1, exc_value: BaseException = None):
        pass

    @abstractmethod
    def endTest(self, current_test, state: str, reason_of_state: str, exc_value: BaseException = None):
        pass

    @abstractmethod
    def save_file(self, current_test, data, filename) -> Dict:
        pass

    @abstractmethod
    def copy_file(self, current_test, orig_filename, dest_filename, data) -> Dict:
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
