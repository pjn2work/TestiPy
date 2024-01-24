from typing import Dict

from testipy.reporter import ReportManager
from testipy.helpers.data_driven_testing import DDTMethods

from pet_store import Toolbox


class SuitePetStore:
    """
    @LEVEL 1
    @TAG DDT PETSTORE
    @PRIO 1
    """
    def __init__(self):
        self.ddt = DDTMethods("pet_store_data.yaml", "", Toolbox())

    def test_pet_story1(self, ma: Dict, rm: ReportManager, ncycles=1, param=dict()):
        """
        @LEVEL 3
        @PRIO 5
        """
        self.ddt.run_all_scenarios_as_tests_usecases_as_teststeps_under_tag_name(ma, rm, "STORY1")

    def test_pet_valid(self, ma: Dict, rm: ReportManager, ncycles=1, param=dict()):
        """
        @LEVEL 2
        @PRIO 10
        """
        self.ddt.run_all_usecases_as_tests(ma=ma, rm=rm, tag="SINGLE", scenario_name="valid")

    def test_pet_invalid(self, ma: Dict, rm: ReportManager, ncycles=1, param=dict()):
        """
        @LEVEL 1
        @PRIO 15
        """
        self.ddt.run_all_usecases_as_tests(ma=ma, rm=rm, tag="SINGLE", scenario_name="invalid")
