from typing import Dict

from testipy.helpers.handle_assertions import ExpectedError
from testipy.reporter import ReportManager

from pet_store_toolbox import Toolbox


_new_pet = {
                "id": 1,
                "name": "Sissi",
                "category": {
                    "id": 1,
                    "name": "Dogs"
                },
                "photoUrls": [""],
                "tags": [
                    {
                        "id": 0,
                        "name": "Schnauzer"
                    },
                    {
                        "id": 0,
                        "name": "mini"
                    }
                ],
                "status": "available"
            }


class SuitePetStore:
    """
    @LEVEL 1
    @TAG PETSTORE
    @PRIO 2
    """

    def __init__(self):
        self.toolbox = Toolbox()

    # Create a new pet
    def test_create_pet_valid(self, ma: Dict, rm: ReportManager, ncycles=1, param=None):
        """
        @LEVEL 3
        @PRIO 5
        """
        current_test = rm.startTest(ma)

        data = {
            "control": {"expected_status_code": 200},
            "param": _new_pet,
            "expected_response": _new_pet
        }

        try:
            self.toolbox.post_pet(rm, current_test, data, "create_pet")
        except Exception as ex:
            rm.testFailed(current_test, reason_of_state=str(ex), exc_value=ex)
        else:
            rm.testPassed(current_test, reason_of_state="pet created")

    # Get the pet created before
    def test_get_pet_valid(self, ma: Dict, rm: ReportManager, ncycles=1, param=None):
        """
        @LEVEL 3
        @PRIO 10
        @ON_SUCCESS 5
        """
        current_test = rm.startTest(ma)

        data = {
            "control": {"expected_status_code": 200},
            "param": _new_pet["id"],
            "expected_response": _new_pet
        }

        try:
            self.toolbox.get_pet(rm, current_test, data, "get_pet")
        except Exception as ex:
            rm.testFailed(current_test, reason_of_state=str(ex), exc_value=ex)
        else:
            rm.testPassed(current_test, reason_of_state="pet fetched")

    # Create a new pet without ID
    def test_create_pet_invalid(self, ma: Dict, rm: ReportManager, ncycles=1, param=None):
        """
        @LEVEL 3
        @PRIO 15
        """
        current_test = rm.startTest(ma)

        data = {
            "control": {"expected_status_code": 500},
            "param": dict_without_keys(_new_pet, ["id"]),
            "expected_response": None
        }

        try:
            self.toolbox.post_pet(rm, current_test, data, "create_pet_invalid")
        except ExpectedError as ex:
            rm.testPassed(current_test, reason_of_state=str(ex))
        except Exception as ex:
            rm.testFailed(current_test, reason_of_state=str(ex), exc_value=ex)
        else:
            rm.testFailed(current_test, reason_of_state="this should never pass!")

    # Buy an invalid pet
    def test_buy_pet_invalid(self, ma: Dict, rm: ReportManager, ncycles=1, param=None):
        """
        @LEVEL 3
        @PRIO 20
        """
        current_test = rm.startTest(ma)

        data = {
            "control": {"expected_status_code": 204},
            "param": _new_pet["id"],
            "expected_response": None
        }

        try:
            self.toolbox.buy_pet(rm, current_test, data, "buy_pet")
        except Exception as ex:
            rm.testFailedKnownBug(current_test, reason_of_state=str(ex), exc_value=ex)
        else:
            rm.testPassed(current_test, reason_of_state="buy pet")


def dict_without_keys(_dict: Dict, keys_to_remove) -> Dict:
    if not isinstance(keys_to_remove, (list, tuple, set)):
        keys_to_remove = [keys_to_remove]
    return {k: v for k, v in _dict.items() if k not in keys_to_remove}
