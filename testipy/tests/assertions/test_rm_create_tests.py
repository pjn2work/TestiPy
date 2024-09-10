from testipy.configs import enums_data
from testipy.engine.models import TestMethodAttr
from testipy.helpers import prettify
from testipy.reporter import ReportManager, SuiteDetails, TestDetails


class SuiteRM_CreateTests:
    """
    @LEVEL 1
    @TAG UT
    @TN 9
    @PRIO 9
    """

    def test_create_test_without_attr(self, sd: SuiteDetails, ma: TestMethodAttr, rm: ReportManager, ncycles=1, param=dict()):
        """
        @LEVEL 1
        @TAG FAILING
        """
        expected_error = "When starting a new test, you must pass your MethodAttributes (dict), received as the first parameter on your test method."
        try:
            current_test = rm.startTest(None)
        except ValueError as ve:
            current_test = rm.startTest(sd, ma)
            rm.test_step(current_test=current_test, state=enums_data.STATE_PASSED, reason_of_state="screenshot", take_screenshot=True)
            assert str(ve) == expected_error, f"The error should be '{expected_error}', and not '{ve}'"
            rm.testPassed(current_test, "Failed with expected ValueError")
        except Exception as ex:
            current_test = rm.startTest(sd, ma)
            rm.testFailed(current_test, f"Should have raised a ValueError, not a {type(ex)} - {ex}")
        else:
            rm.testFailed(current_test, f"Should have raised a ValueError!")

    def test_create_test_without_name(self, sd: SuiteDetails, ma: TestMethodAttr, rm: ReportManager, ncycles=1, param=dict()):
        """
        @LEVEL 1
        """
        current_test = rm.startTest(sd, ma)

        expected_test_name = ma.name
        current_test_name = current_test.get_name()

        assert expected_test_name == current_test_name, f"Expected {expected_test_name=}, not {current_test_name}"

        rm.testPassed(current_test, "Test created with default name")

    def test_create_test_with_override_name(self, sd: SuiteDetails, ma: TestMethodAttr, rm: ReportManager, ncycles=2, param=dict()):
        """
        @LEVEL 1
        """
        expected_test_name = param.get("name", "override_test_name")
        current_test = rm.startTest(sd, ma, expected_test_name)
        current_test_name = current_test.get_name()

        rm.test_info(current_test, "Received parameters = " + str(param), level="INFO")

        assert expected_test_name == current_test_name, f"Expected {expected_test_name=}, not {current_test_name}"

        rm.testPassed(current_test, "Test created with override name")

    def test_create_test_with_usecase(self, sd: SuiteDetails, ma: TestMethodAttr, rm: ReportManager, ncycles=1, param=dict()):
        """
        @LEVEL 1
        """
        expected_usecase = "secondary purpose"
        current_test = rm.startTest(sd, ma, usecase=expected_usecase)
        current_usecase = current_test.get_usecase()

        assert expected_usecase == current_usecase, f"Expected {expected_usecase=}, not {current_usecase}"

        rm.testPassed(current_test, "Test created with usecase")

    # This test has a comment
    # with two lines
    def test_has_default_comment(self, sd: SuiteDetails, ma: TestMethodAttr, rm: ReportManager, ncycles=1, param=dict()):
        """
        @LEVEL 1
        """
        current_test = rm.startTest(sd, ma)
        current_comment = current_test.get_comment()
        expected_comment = "This test has a comment\nwith two lines"

        assert expected_comment == current_comment, f"Expected {expected_comment=}, not {current_comment}"

        rm.testPassed(current_test, "Test created with default comment")

    # This is the test comment/description
    def test_create_test_with_override_comment(self, sd: SuiteDetails, ma: TestMethodAttr, rm: ReportManager, ncycles=1, param=dict()):
        """
        @LEVEL 1
        """
        expected_comment = "This will override the test comment"
        current_test = rm.startTest(sd, ma, description=expected_comment)
        current_comment = current_test.get_comment()

        assert expected_comment == current_comment, f"Expected {expected_comment=}, not {current_comment}"

        rm.testPassed(current_test, "Test created with override comment")

    def test_doc_string(self, sd: SuiteDetails, ma: TestMethodAttr, rm: ReportManager, ncycles=1, param=dict()):
        """
        @NAME doc_string_test
        @PRIO 10
        @LEVEL 1
        @FEATURES DOC F2
        @TAG AA1 BB2 CC
        @TN .5
        """
        current_test: TestDetails = rm.startTest(sd, ma)
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

    def test_will_be_auto_created(self, sd: SuiteDetails, ma: TestMethodAttr, rm: ReportManager, ncycles=1, param=dict()):
        """
        @LEVEL 1
        """
        assert 1 == 1
