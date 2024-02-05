import requests

from typing import Dict

from testipy.reporter import ReportManager
from testipy.reporter.report_base import TestDetails
from testipy.helpers.data_driven_testing import ExecutionToolbox, SafeTry, DDTMethods
from testipy.helpers.rest import handle_http_response


class Toolbox(ExecutionToolbox):

    def execute(self, rm: ReportManager, current_test: TestDetails, exec_method, usecase: Dict, usecase_name: str, st: SafeTry):
        exec_method = f"self.{usecase['_exec_method_']}(rm=rm, current_test=current_test, usecase=usecase, usecase_name=usecase_name, st=st)"
        rm.test_info(current_test, f"Executing {exec_method}")
        #eval(exec_method)

    def clear_last_execution(self):
        handle_http_response.body = handle_http_response.raw = ""


class SuiteDDT:
    """
    @LEVEL 1
    @PRIO 0
    """

    def __init__(self):
        self.ddf: DDTMethods = None

    def test_setup(self, ma: Dict, rm: ReportManager, **kwargs):
        """
        @LEVEL 1
        @TAG SETUP
        @PRIO 0
        """
        self.ddt = DDTMethods("data.yaml", rm.get_environment_name(), Toolbox())

    def test_run_scenario__usecases_as_steps(self, ma: Dict, rm: ReportManager, ncycles=1, param=dict()):
        """
        @LEVEL 1
        @PRIO 2
        @ON_SUCCESS 0
        """
        self.ddt.run(ma, rm, tag_name="CASE1", scenario_name="test_2")

    def test_run_tag__scenarios_as_tests__usecases_as_steps(self, ma: Dict, rm: ReportManager, ncycles=1, param=dict()):
        """
        @LEVEL 1
        @PRIO 4
        @ON_SUCCESS 0
        """
        self.ddt.run(ma, rm, tag_name="CASE2")

    def test_run_scenario__usecases_as_tests__positive(self, ma: Dict, rm: ReportManager, ncycles=1, param=dict()):
        """
        @LEVEL 1
        @PRIO 6
        @ON_SUCCESS 0
        """
        self.ddt.run(ma, rm, tag_name="CASE3", scenario_name="positive")

    def test_run_scenario__usecases_as_tests__negative(self, ma: Dict, rm: ReportManager, ncycles=1, param=dict()):
        """
        @LEVEL 1
        @PRIO 7
        @ON_SUCCESS 0
        """
        self.ddt.run(ma, rm, tag_name="CASE3", scenario_name="negative")

    def test_run_usecases_as_tests__without_scenario(self, ma: Dict, rm: ReportManager, ncycles=1, param=dict()):
        """
        @LEVEL 1
        @PRIO 8
        @ON_SUCCESS 0
        """
        self.ddt.run(ma, rm, tag_name="CASE4")

    def test_run_usecases_under_tag(self, ma: Dict, rm: ReportManager, ncycles=1, param=dict()):
        """
        @LEVEL 1
        @PRIO 10
        @ON_SUCCESS 0
        """
        self.ddt.run_tag(ma, rm, tag_name="CASE5")
