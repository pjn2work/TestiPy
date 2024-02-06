from typing import Dict

from testipy.reporter import ReportManager
from testipy.helpers.data_driven_testing import DDTMethods, RunMode

from pet_store_toolbox import Toolbox


class SuitePetStoreDDT:
    """
    @LEVEL 1
    @TAG DDT PETSTORE
    @PRIO 1
    """

    def test_setup(self, ma: Dict, rm: ReportManager, **kwargs):
        """
        @LEVEL 1
        @TAG SETUP
        @PRIO 0
        """
        self.ddt = DDTMethods("pet_store_data.yaml", env_name=rm.get_environment_name(), exec_toolbox=Toolbox())

    # Same test, two ways of calling it
    def test_pet_story1_1(self, ma: Dict, rm: ReportManager, ncycles=1, param=dict()):
        """
        @NAME test_pet_story1
        @LEVEL 3
        @PRIO 5
        @ON_SUCCESS 0
        """
        self.ddt.run_tag(ma, rm, tag_name="STORY1")

    # Same test, two ways of calling it
    def test_pet_story1_2(self, ma: Dict, rm: ReportManager, ncycles=1, param=dict()):
        """
        @NAME test_pet_story1
        @LEVEL 3
        @PRIO 7
        @ON_SUCCESS 0
        """
        self.ddt.run(ma, rm, tag_name="STORY1")

    # Same test, two ways of calling it - change run_mode
    def test_pet_story1_3(self, ma: Dict, rm: ReportManager, ncycles=1, param=dict()):
        """
        @NAME test_pet_story1
        @LEVEL 3
        @PRIO 9
        @ON_SUCCESS 0
        """
        self.ddt.run(ma, rm, tag_name="STORY1", run_mode=RunMode.SCENARIOS_AS_TESTS__USECASES_AS_TESTSTEPS)

    def test_pet_valid(self, ma: Dict, rm: ReportManager, ncycles=1, param=dict()):
        """
        @LEVEL 2
        @PRIO 11
        @ON_SUCCESS 0
        """
        self.ddt.run_scenario__usecases_as_tests(ma=ma, rm=rm, tag_name="SINGLE", scenario_name="valid")

    def test_pet_invalid(self, ma: Dict, rm: ReportManager, ncycles=1, param=dict()):
        """
        @LEVEL 1
        @PRIO 13
        @ON_SUCCESS 0
        """
        self.ddt.run(ma=ma, rm=rm, tag_name="SINGLE", scenario_name="invalid")
