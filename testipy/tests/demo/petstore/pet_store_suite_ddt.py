from testipy.reporter import ReportManager, SuiteDetails
from testipy.helpers.data_driven_testing import DDTMethods, RunMode

from pet_store_toolbox import Toolbox


class SuitePetStoreDDT:
    """
    @LEVEL 1
    @TAG DDT PETSTORE
    @PRIO 1
    """

    def test_setup(self, sd: SuiteDetails, rm: ReportManager, **kwargs):
        """
        @LEVEL 1
        @TAG SETUP
        @PRIO 0
        """
        self.ddt = DDTMethods("pet_store_data.yaml", env_name=rm.get_environment_name(), exec_toolbox=Toolbox())

    # Same test, two ways of calling it
    def test_pet_story1_1(self, sd: SuiteDetails, rm: ReportManager, ncycles=1, param={}):
        """
        @NAME test_pet_story1
        @LEVEL 3
        @PRIO 5
        @ON_SUCCESS 0
        """
        self.ddt.run_tag(sd, rm, tag_name="STORY1")

    # Same test, two ways of calling it
    def test_pet_story1_2(self, sd: SuiteDetails, rm: ReportManager, ncycles=1, param={}):
        """
        @NAME test_pet_story1
        @LEVEL 3
        @PRIO 7
        @ON_SUCCESS 0
        """
        self.ddt.run(sd, rm, tag_name="STORY1")

    # Same test, two ways of calling it - change run_mode
    def test_pet_story1_3(self, sd: SuiteDetails, rm: ReportManager, ncycles=1, param={}):
        """
        @NAME test_pet_story1
        @LEVEL 3
        @PRIO 9
        @ON_SUCCESS 0
        """
        self.ddt.run(sd, rm, tag_name="STORY1", run_mode=RunMode.SCENARIOS_AS_TESTS__USECASES_AS_TESTSTEPS)

    def test_pet_valid(self, sd: SuiteDetails, rm: ReportManager, ncycles=1, param={}):
        """
        @LEVEL 2
        @PRIO 11
        @ON_SUCCESS 0
        """
        self.ddt.run_scenario__usecases_as_tests(sd=sd, rm=rm, tag_name="SINGLE", scenario_name="valid")

    def test_pet_invalid(self, sd: SuiteDetails, rm: ReportManager, ncycles=1, param={}):
        """
        @LEVEL 1
        @PRIO 13
        @ON_SUCCESS 0
        @TAG FAILING
        """
        self.ddt.run(sd=sd, rm=rm, tag_name="SINGLE", scenario_name="invalid")
