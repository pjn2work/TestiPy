from testipy.helpers.handle_assertions import (
    HandledError,
    ExpectedError,
    SkipTestError,
    UnexpectedTypeError,
    UnexpectedValueError,
    ExpectedFieldMissingError,
)

from testipy.configs import enums_data
from testipy.helpers import prettify
from testipy.reporter import ReportManager, SuiteDetails, TestDetails


class SuiteRM_CreateTests:
    """
    @LEVEL 1
    @TAG UT
    @TN 9
    @PRIO 9
    """

    def test_create_test_without_attr(self, sd: SuiteDetails, rm: ReportManager, ncycles=2, param={}):
        """
        @LEVEL 1
        @TAG FAILING
        """
        expected_error = "When starting a new test you must have SuiteDetails, received as the first parameter on your test method."
        try:
            current_test = rm.startTest(None)
        except ValueError as ve:
            current_test = rm.startTest(sd)
            rm.test_step(current_test=current_test, state=enums_data.STATE_PASSED, reason_of_state="screenshot", take_screenshot=True)
            assert str(ve) == expected_error, f"The error should be '{expected_error}', and not '{ve}'"
            rm.testPassed(current_test, "Failed with expected ValueError")
        except Exception as ex:
            current_test = rm.startTest(sd)
            rm.testFailed(current_test, f"Should have raised a ValueError, not a {type(ex)} - {ex}")
        else:
            rm.testFailed(current_test, f"Should have raised a ValueError!")

    def test_create_test_without_name(self, sd: SuiteDetails, rm: ReportManager, ncycles=2, param={}):
        """
        @LEVEL 1
        """
        current_test = rm.startTest(sd)

        expected_test_name = current_test.name
        current_test_name = current_test.get_name()

        assert expected_test_name == current_test_name, f"Expected {expected_test_name=}, not {current_test_name}"

        rm.testPassed(current_test, "Test created with default name")

    def test_create_test_with_override_name(self, sd: SuiteDetails, rm: ReportManager, ncycles=2, param={}):
        """
        @LEVEL 1
        """
        expected_test_name = param.get("name", "override_test_name")
        current_test = rm.startTest(sd, test_name=expected_test_name)
        current_test_name = current_test.get_name()

        rm.test_info(current_test, "Received parameters = " + str(param), level="INFO")

        assert expected_test_name == current_test_name, f"Expected {expected_test_name=}, not {current_test_name}"

        rm.testPassed(current_test, "Test created with override name")

    def test_create_test_with_usecase(self, sd: SuiteDetails, rm: ReportManager, ncycles=2, param={}):
        """
        @LEVEL 1
        """
        expected_usecase = "secondary purpose"
        current_test = rm.startTest(sd, usecase=expected_usecase)
        current_usecase = current_test.get_usecase()

        assert expected_usecase == current_usecase, f"Expected {expected_usecase=}, not {current_usecase}"

        rm.testPassed(current_test, "Test created with usecase")

    # This test has a comment
    # with two lines
    def test_has_default_comment(self, sd: SuiteDetails, rm: ReportManager, ncycles=2, param={}):
        """
        @LEVEL 1
        """
        current_test = rm.startTest(sd)
        current_comment = current_test.get_comment()
        expected_comment = "This test has a comment\nwith two lines"

        assert expected_comment == current_comment, f"Expected {expected_comment=}, not {current_comment}"

        rm.testPassed(current_test, "Test created with default comment")

    # This is the test comment/description
    def test_create_test_with_override_comment(self, sd: SuiteDetails, rm: ReportManager, ncycles=2, param={}):
        """
        @LEVEL 1
        """
        expected_comment = "This will override the test comment"
        current_test = rm.startTest(sd, description=expected_comment)
        current_comment = current_test.get_comment()

        assert expected_comment == current_comment, f"Expected {expected_comment=}, not {current_comment}"

        rm.testPassed(current_test, "Test created with override comment")

    def test_doc_string(self, sd: SuiteDetails, rm: ReportManager, ncycles=2, param={}):
        """
        @NAME doc_string_test
        @PRIO 10
        @LEVEL 1
        @FEATURES DOC F2
        @TAG AA1 BB2 CC
        @TN .5
        """
        current_test: TestDetails = rm.startTest(sd)
        current_attributes = dict(
            NAME=current_test.get_name(),
            TAG=current_test.get_tags(),
            LEVEL=current_test.get_level(),
            PRIO=current_test.get_prio(),
            FEATURES=current_test.get_features(),
            TN=current_test.get_test_number(),
        )
        expected_attributes = {
            'NAME': 'doc_string_test',
            'TAG': {'BB2', 'CC', 'AA1'},
            'LEVEL': 1,
            'PRIO': 10,
            'FEATURES': 'DOC F2',
            'TN': '9.5'
        }

        rm.test_info(current_test, "Test Attributes:\n" + prettify(current_attributes))
        rm.test_info(current_test, "Expected Attributes:\n" + prettify(expected_attributes))

        for k, v in expected_attributes.items():
            assert current_attributes.get(k) == v, f"The attributes {k} differ! {current_attributes.get(k)} != {v}"

        rm.testPassed(current_test, "Test has expected doc string")

    def test_raise_handled_exceptions(self, sd: SuiteDetails, rm: ReportManager, ncycles=6, param={}):
        """
        @LEVEL 1
        @PRIO 90
        @TAG FAILING
        """
        errors = {
            1: HandledError("Raised on purpose"),
            2: ExpectedError("Raised on purpose"),
            3: SkipTestError("Raised on purpose"),
            4: UnexpectedTypeError("Raised on purpose"),
            5: UnexpectedValueError("Raised on purpose"),
            6: ExpectedFieldMissingError("Raised on purpose"),
        }
        td = rm.startTest(sd)
        cycle = td.get_cycle()
        raise errors[cycle]

    def test_will_be_auto_created1(self, sd: SuiteDetails, rm: ReportManager, ncycles=2, param={}):
        """
        @LEVEL 1
        @PRIO 91
        """
        assert 1 == 1

    def test_will_be_auto_created_but_fail1(self, sd: SuiteDetails, rm: ReportManager, ncycles=2, param={}):
        """
        @LEVEL 1
        @PRIO 92
        @TAG FAILING
        """
        assert 1 == 0

    def test_will_be_auto_created2(self, sd: SuiteDetails, rm: ReportManager, ncycles=2, param={}):
        """
        @LEVEL 1
        @PRIO 93
        """
        assert 1 == 1

    def test_will_be_auto_created_but_fail2(self, sd: SuiteDetails, rm: ReportManager, ncycles=2, param={}):
        """
        @LEVEL 1
        @PRIO 94
        @TAG FAILING
        """
        assert 1 == 0
