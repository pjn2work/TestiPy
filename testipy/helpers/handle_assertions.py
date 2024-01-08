from typing import List, Dict


class HandledError(AssertionError):
    pass


class ExpectedError(HandledError):
    """Raised when found an expected error and PASS the test that was designed to fail"""
    pass


class SkipTestError(HandledError):
    """Raised when want to skip tests"""
    pass


class UnexpectedTypeError(HandledError):
    """Raised when expected type doesn't match the received"""
    pass


class UnexpectedValueError(HandledError):
    """Raised when expected value doesn't match the received"""
    pass


class ExpectedFieldMissingError(HandledError):
    """Raised when didn't receive the expected field"""
    pass


def assert_same_len(expected_len, received_len, where: str = "response"):
    if not isinstance(expected_len, int):
        expected_len = len(expected_len)

    if not isinstance(received_len, int):
        received_len = len(received_len)

    if received_len != expected_len:
        raise HandledError(f"Different size for {where}={received_len}, expected {expected_len}")


def assert_expected_type(received, expected_type, where: str = "response"):
    if not isinstance(expected_type, list):
        expected_type = [expected_type]

    if received is None and None not in expected_type:
        raise UnexpectedTypeError(f"'Null' not allowed in {where}, only {expected_type}")
    else:
        if None in expected_type:
            expected_type.remove(None)
        if not isinstance(received, tuple(expected_type)):
            raise UnexpectedTypeError(f"Expected {where} to be a {expected_type}, not {type(received)}")


def assert_expected_value(expected, received, where: str = "response"):
    if received != expected:
        raise UnexpectedValueError(f"Expected {where}='{expected}', not '{received}'")


# It only works if there is no duplicated data inside lists. lst1=expected, lst2=received
def assert_equal_unique_lists(lst1: List, lst2: List, name_list1: str = "list1", name_list2: str = "list2", strict=True, **kwargs):
    assert_expected_type(lst1, (list, tuple, set), where=name_list1)
    assert_expected_type(lst2, (list, tuple, set), where=name_list2)
    if strict:
        assert_same_len(lst1, lst2, where=f"{name_list1} vs {name_list2}")

    for x in lst1:
        if isinstance(x, (list, tuple, set, dict)):
            for z in lst2:      # iterate every element z from list2 and compare if equal to element x from list1
                if isinstance(z, type(x)):
                    try:
                        if isinstance(x, dict):
                            assert_data(x, z, where=name_list1)
                        else:
                            assert_equal_unique_lists(x, z, name_list1=name_list1, name_list2=name_list2)
                    except:
                        pass    # so this z is not equal, continue to next z
                    else:
                        break   # found z == x, continue with next x on lst1
            else:
                raise AssertionError(f"{type(x)} from {name_list1} not found in {name_list2}. {x}")
        else:
            if x not in lst2:
                raise UnexpectedValueError(f"Value '{x}' from {name_list1} not in {name_list2}")


# It only works if there is no duplicated data inside lists
def assert_data(expected_values: Dict, response: Dict, where="", strict: bool = False, **kwargs):
    if isinstance(expected_values, dict):
        if strict and len(expected_values) != len(response):
            raise ExpectedFieldMissingError(f"Not same amount of keys: {expected_values.keys()=} not {response.keys()=}")

        for field, value in expected_values.items():
            if field not in response:
                raise ExpectedFieldMissingError(f"{field=} not in {where}")
            if isinstance(value, (list, tuple, set)):
                assert_expected_type(response[field], type(value), where=f"{where}.{field}")
                assert_equal_unique_lists(value, response[field], f"{where}/{field}[expected]", f"{where}/{field}[response]")
            elif isinstance(value, dict):
                assert_expected_type(response[field], dict, where=f"{where}.{field}")
                assert_data(value, response[field], where=f"{where}/{field}")
            else:
                assert_expected_value(value, response[field], where=f"{where}.{field}")
    elif isinstance(expected_values, list):
        assert_equal_unique_lists(expected_values, response, name_list1="expected", name_list2="received", strict=strict)
    elif isinstance(expected_values, str):
        assert expected_values == response, f"{where} Expected value does not meet received."
    else:
        if strict:
            assert expected_values == response, f"{where} Expected value does not meet received."
        else:
            assert expected_values in response, f"{where} Expected value not part of received."


def assert_status_code(expected_status_code, received_status_code):
    if expected_status_code != received_status_code:
        raise UnexpectedValueError(f"Unexpected status_code {received_status_code}, expected {expected_status_code}")
