from typing import Dict

from testipy.reporter import ReportManager
from testipy.helpers.data_driven_testing import DDTMethods

from testipy.tests.demo.ddt.pet_store import Toolbox


class SuitePetStore:
    """
    @LEVEL 1
    @TAG DDT PETSTORE
    """
    def __init__(self):
        self.ddt = DDTMethods("pet_store_data.yaml", "", Toolbox())

    def test_pet_story1(self, td: Dict, rm: ReportManager, ncycles=1, param=dict()):
        """
        @LEVEL 3
        @PRIO 5
        """
        self.ddt.run_all_scenarios_as_tests_usecases_as_teststeps_under_tag_name(td, rm, "STORY1")

    def test_pet_valid(self, td: Dict, rm: ReportManager, ncycles=1, param=dict()):
        """
        @LEVEL 2
        @PRIO 10
        """
        self.ddt.run_all_usecases_as_tests(td=td, rm=rm, tag="SINGLE", scenario_name="valid")

    def test_pet_invalid(self, td: Dict, rm: ReportManager, ncycles=1, param=dict()):
        """
        @LEVEL 1
        @PRIO 15
        """
        self.ddt.run_all_usecases_as_tests(td=td, rm=rm, tag="SINGLE", scenario_name="invalid")
