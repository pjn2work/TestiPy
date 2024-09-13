from typing import Dict

from testipy.reporter import ReportManager, SuiteDetails, TestDetails
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

    def test_setup(self, sd: SuiteDetails, rm: ReportManager, **kwargs):
        """
        @LEVEL 1
        @TAG SETUP
        @PRIO 0
        """
        self.ddt = DDTMethods("data.yaml", rm.get_environment_name(), Toolbox())

    def test_autodetect_run_scenario__usecases_as_steps(self, sd: SuiteDetails, rm: ReportManager, ncycles=1, param={}):
        """
        @LEVEL 1
        @PRIO 2
        @ON_SUCCESS 0
        """
        self.ddt.run(sd, rm, tag_name="CASE1", scenario_name="test_2")

    def test_autodetect_run_tag__scenarios_as_tests__usecases_as_steps(self, sd: SuiteDetails, rm: ReportManager, ncycles=1, param={}):
        """
        @LEVEL 1
        @PRIO 4
        @ON_SUCCESS 0
        """
        self.ddt.run(sd, rm, tag_name="CASE2")

    def test_autodetect_run_scenario__usecases_as_tests__positive(self, sd: SuiteDetails, rm: ReportManager, ncycles=1, param={}):
        """
        @LEVEL 1
        @PRIO 6
        @ON_SUCCESS 0
        """
        self.ddt.run(sd, rm, tag_name="CASE3", scenario_name="positive")

    def test_autodetect_run_scenario__usecases_as_tests__negative(self, sd: SuiteDetails, rm: ReportManager, ncycles=1, param={}):
        """
        @LEVEL 1
        @PRIO 7
        @ON_SUCCESS 0
        """
        self.ddt.run(sd, rm, tag_name="CASE3", scenario_name="negative")

    def test_autodetect_run_usecases_as_tests__without_scenario(self, sd: SuiteDetails, rm: ReportManager, ncycles=1, param={}):
        """
        @LEVEL 1
        @PRIO 8
        @ON_SUCCESS 0
        """
        self.ddt.run(sd, rm, tag_name="CASE4")

    def test_run_usecases_under_tag(self, sd: SuiteDetails, rm: ReportManager, ncycles=1, param={}):
        """
        @LEVEL 1
        @PRIO 10
        @ON_SUCCESS 0
        """
        self.ddt.run_tag(sd, rm, tag_name="CASE5")

    def test_run_scenario_as_test__usecases_as_teststeps(self, sd: SuiteDetails, rm: ReportManager, ncycles=1, param={}):
        """
        @LEVEL 1
        @PRIO 11
        @ON_SUCCESS 0
        """
        self.ddt.run_scenario_as_test__usecases_as_teststeps(sd, rm, tag_name="CASE3", scenario_name="positive")

    def test_run_scenario__usecases_as_tests(self, sd: SuiteDetails, rm: ReportManager, ncycles=1, param={}):
        """
        @LEVEL 1
        @PRIO 12
        @ON_SUCCESS 0
        """
        self.ddt.run_scenario__usecases_as_tests(sd, rm, tag_name="CASE1", scenario_name="test_2")

    def test_run_usecases_as_tests__without_scenario(self, sd: SuiteDetails, rm: ReportManager, ncycles=1, param={}):
        """
        @LEVEL 1
        @PRIO 13
        @ON_SUCCESS 0
        """
        self.ddt.run_usecases_as_tests__without_scenario(sd, rm, tag_name="CASE4")

    def test_run_usecases_as_teststeps__without_scenario(self, sd: SuiteDetails, rm: ReportManager, ncycles=1, param={}):
        """
        @LEVEL 1
        @PRIO 13
        @ON_SUCCESS 0
        """
        self.ddt.run_usecases_as_teststeps__without_scenario(sd, rm, tag_name="CASE4")
