import functools
import inspect
from requests import Response


from testipy.helpers.handle_assertions import assert_status_code, ExpectedError


def get_response():
    return handle_response.body


def get_raw_response() -> Response:
    return handle_response.raw


def get_status_code():
    return handle_response.raw.status_code


def get_headers():
    return handle_response.raw.headers


def handle_response(_func=None, *, expected_type=None):
    handle_response.raw = None
    handle_response.body = None

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            handle_response.raw = response = func(*args, **kwargs)

            # get default parameters from func and update them
            default_kwargs = dict(inspect.signature(func).parameters)
            default_kwargs = {parameter.name: parameter.default for name, parameter in default_kwargs.items() if parameter.default is not inspect._empty and str(parameter.kind) in ["POSITIONAL_OR_KEYWORD", "KEYWORD_ONLY"]}
            default_kwargs.update(kwargs)

            # handle response
            assert_status_code(default_kwargs.get("expected_status_code"), response.status_code)
            if default_kwargs.get("expected_status_code") == default_kwargs.get("ok"):
                if expected_type is None:
                    return None
                handle_response.body = response = response.text if expected_type == str else response.json()
                assert isinstance(response, expected_type), f"must receive a {type(expected_type)} not a {type(response)}"
                return response
            else:
                if response.status_code == 204:
                    assert response.text == "", "response should be empty!"

                if expected_type and expected_type != str:
                    try:
                        handle_response.body = response.json()
                    except:
                        raise AssertionError("error message response, not a JSON!")
                raise ExpectedError(f"designed to fail with {response.status_code}")

        return wrapper

    if _func is None:
        return decorator    # under a class instance
    else:
        return decorator(_func)
