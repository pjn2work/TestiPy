import requests

from typing import Dict

from testipy.reporter import ReportManager
from testipy.reporter.report_base import TestDetails
from testipy.helpers import prettify
from testipy.helpers.data_driven_testing import ExecutionToolbox, SafeTry
from testipy.helpers.handle_assertions import ExpectedError
from testipy.helpers.rest import handle_http_response


class Toolbox(ExecutionToolbox):

    def execute(self, rm: ReportManager, current_test: TestDetails, exec_method, usecase: Dict, usecase_name: str, st: SafeTry):
        exec_method = f"self.{usecase['_exec_method_']}(rm=rm, current_test=current_test, usecase=usecase, usecase_name=usecase_name, st=st)"
        eval(exec_method)

    def clear_last_execution(self):
        handle_http_response.body = handle_http_response.raw = ""

    # --- Execution Methods --------------------------------------------------------------------------------------------
    def post_pet(self, rm: ReportManager, current_test: TestDetails, usecase: Dict, usecase_name: str, **kwargs):
        url = f"https://petstore3.swagger.io/api/v3/pet"
        try:
            response = _post_as_dict(url, usecase["param"], **usecase["control"], expected_response=usecase.get("expected_response"))
            rm.test_info(current_test, f"{usecase_name} - POST {url} - received payload:\n" + prettify(response, as_yaml=False))
        except Exception as ex:
            _show_expected_payload_vs_received(rm, current_test, usecase, usecase_name, url, "POST", ex)
            raise

    def get_pet(self, rm: ReportManager, current_test: TestDetails, usecase: Dict, usecase_name: str, **kwargs):
        url = f"https://petstore3.swagger.io/api/v3/pet/" + str(usecase["param"])
        try:
            response = _get_as_dict(url, **usecase["control"], expected_response=usecase.get("expected_response"))
            rm.test_info(current_test, f"{usecase_name} - GET {url} - received payload:\n" + prettify(response, as_yaml=False))
        except Exception as ex:
            _show_expected_payload_vs_received(rm, current_test, usecase, usecase_name, url, "GET", ex)
            raise

    def put_pet(self, rm: ReportManager, current_test: TestDetails, usecase: Dict, usecase_name: str, **kwargs):
        url = f"https://petstore3.swagger.io/api/v3/pet"
        try:
            response = _put_as_dict(url, usecase["param"], **usecase["control"], expected_response=usecase.get("expected_response"))
            rm.test_info(current_test, f"{usecase_name} - PUT {url} - received payload:\n" + prettify(response, as_yaml=False))
        except Exception as ex:
            _show_expected_payload_vs_received(rm, current_test, usecase, usecase_name, url, "PUT", ex)
            raise

    def delete_pet(self, rm: ReportManager, current_test: TestDetails, usecase: Dict, usecase_name: str, **kwargs):
        url = f"https://petstore3.swagger.io/api/v3/pet/" + str(usecase["param"])
        try:
            response = _delete_as_str(url, **usecase["control"], expected_response=usecase.get("expected_response"))
            rm.test_info(current_test, f"{usecase_name} - DELETE {url} - received payload:\n" + prettify(response, as_yaml=False))
        except Exception as ex:
            _show_expected_payload_vs_received(rm, current_test, usecase, usecase_name, url, "DELETE", ex)
            raise

    def buy_pet(self, rm: ReportManager, current_test: TestDetails, usecase: Dict, usecase_name: str, **kwargs):
        url = f"https://petstore3.swagger.io/api/v3/pet/buy/" + str(usecase["param"])
        try:
            response = _get_as_dict(url, **usecase["control"], expected_response=usecase.get("expected_response"))
            rm.test_info(current_test, f"{usecase_name} - GET {url} - received payload:\n" + prettify(response, as_yaml=False))
        except Exception as ex:
            _show_expected_payload_vs_received(rm, current_test, usecase, usecase_name, url, "GET", ex)
            raise


@handle_http_response(expected_type=dict)
def _get_as_dict(url: str = "", timeout: int = 5, expected_status_code: int = 200, ok: int = 200, expected_response=None) -> Dict:
    return requests.get(url, headers={"accept": "application/json"}, timeout=timeout)


@handle_http_response(expected_type=dict)
def _post_as_dict(url: str = "", data: Dict = None, timeout: int = 5, expected_status_code: int = 200, ok: int = 200, expected_response=None) -> Dict:
    return requests.post(url, json=data,
                         headers={"Content-Type": "application/json; charset=utf-8", "accept": "application/json"},
                         timeout=timeout)


@handle_http_response(expected_type=dict)
def _put_as_dict(url: str = "", data: Dict = None, timeout: int = 5, expected_status_code: int = 200, ok: int = 200, expected_response=None) -> Dict:
    return requests.put(url, json=data,
                        headers={"Content-Type": "application/json; charset=utf-8", "accept": "application/json"},
                        timeout=timeout)


@handle_http_response(expected_type=str)
def _delete_as_str(url: str = "", timeout: int = 5, expected_status_code: int = 200, ok: int = 200, expected_response=None) -> Dict:
    return requests.delete(url, headers={"accept": "application/json"}, timeout=timeout)


def _show_expected_payload_vs_received(rm: ReportManager, current_test: TestDetails, usecase: Dict, usecase_name: str, url: str, http_method: str, ex: Exception):
    rm.test_info(current_test,
                 info=f"{usecase_name} - {http_method} {url} - received Error payload:\n" +
                    prettify(handle_http_response.body, as_yaml=False),
                 level="DEBUG" if isinstance(ex, ExpectedError) else "ERROR")
    if expected_response := usecase.get("expected_response"):
        rm.test_info(current_test,
                     info=f"{usecase_name} - expected payload:\n{prettify(expected_response, as_yaml=False)}",
                     level="DEBUG")
