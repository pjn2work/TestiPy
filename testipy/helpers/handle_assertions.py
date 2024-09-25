from typing import List, Dict, Any


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


def assert_status_code(expected_status_code, received_status_code):
    if expected_status_code != received_status_code:
        raise UnexpectedValueError(f"Unexpected status_code {received_status_code}, expected {expected_status_code}")


def assert_equal_complex_object(
    expected: Any,
    received: Any,
    expected_name: str = "expected",
    received_name: str = "received",
) -> None:
    if isinstance(expected, dict) and isinstance(received, dict):
        assert_equal_dicts(
            expected, received, expected_name=expected_name, received_name=received_name
        )
    elif isinstance(expected, (list, tuple, set)) and isinstance(
        received, (list, tuple, set)
    ):
        assert_equal_lists(
            expected, received, expected_name=expected_name, received_name=received_name
        )
    else:
        assert (
            expected == received
        ), f"{expected_name} = '{expected}' not equal to {received_name} = '{received}'"


def assert_equal_dicts(
    expected: Any,
    received: Any,
    expected_name: str = "expected",
    received_name: str = "received",
) -> None:
    for key in expected:
        assert key in received, f"{expected_name}.{key} is not in dict {received_name}"
        assert_equal_complex_object(
            expected[key],
            received[key],
            expected_name=f"{expected_name}.{key}",
            received_name=f"{received_name}.{key}",
        )


def assert_equal_lists(
    expected: Any,
    received: Any,
    expected_name: str = "expected",
    received_name: str = "received",
    same_len: bool = True,
) -> None:
    if same_len:
        assert (
            len(expected) == len(received)
        ), f"{expected_name} has {len(expected)} elements != {received_name} has {len(received)} elements"

    list2 = list(received)
    for i1, v1 in enumerate(expected):
        for i2, v2 in enumerate(list2):
            try:
                assert_equal_complex_object(
                    v1,
                    v2,
                    expected_name=f"{expected_name}[{i1}]",
                    received_name=f"{received_name}[{i2}]",
                )
            except AssertionError:
                pass
            else:
                list2.remove(v2)
                break
        else:
            raise AssertionError(
                f"{expected_name}[{i1}] '{v1}' is not inside {received_name}"
            )
