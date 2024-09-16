from time import sleep

from testipy.helpers.prettify import prettify

from testipy.configs import enums_data
from testipy.helpers.handle_assertions import ExpectedError
from testipy.reporter import ReportManager, SuiteDetails, TestDetails


class SuiteDemo_01:
    """
    @NAME DemoSuite_001
    @TAG DEMO no_run
    @LEVEL 1
    """

    def test_06_will_run(self, sd: SuiteDetails, rm: ReportManager, ncycles=1, param=None):
        current_test = rm.startTest(sd)
        rm.testPassed(current_test, "test without doc tags")

    def test_00_cannot_run(self, sd: SuiteDetails, rm, ncycles=2, param={}):
        """
        @TAG DEMO no_run
        @LEVEL 0
        """
        current_test = rm.startTest(sd)
        rm.testFailed(current_test, "This test cannot run EVER!")

    def test_01_show_internal_counters(self, sd: SuiteDetails, rm, ncycles=2, ntimes=5, param={}):
        """
        @TAG DEMO no_run
        @LEVEL 1
        """
        current_test = rm.startTest(sd)

        for current_ntime in range(1, ntimes + 1):
            sleep(0.01)
            current_test.test_step(enums_data.STATE_SKIPPED, "Skip all")

        attachment={"name": "results.txt",
                    "data": str(current_test.get_test_step_counters()),
                    "mime": "text/plain"}
        rm.test_info(current_test, current_test.get_test_step_counters(), "DEBUG", attachment)

        rm.testSkipped(current_test, "Ran {} times".format(current_ntime))

    # despite the two FOR, it will run only once, error handled outside on engine.execute_tests
    def test_02_division_by_zero(self, sd: SuiteDetails, rm, ncycles=3, ntimes=5, param=dict(stop_at=1)):
        """
        @TAG DEMO no_run
        @LEVEL 2
        @TAG RAISE FAILING
        """
        current_test = rm.startTest(sd)
        for current_ntime in range(1, ntimes + 1):
            if current_ntime > param["stop_at"]:
                a = 1 / 0
        rm.testFailedKnownBug(current_test, "Impossible to pass the second time")

    # it will exit after 3 consecutive fails
    def test_03_exit_after_several_fails(self, sd: SuiteDetails, rm, ncycles=3, ntimes=10, param={}):
        """
        @TAG DEMO no_run FAILING
        @LEVEL 3
        @PRIO 90
        """
        current_test = rm.startTest(sd)
        tc = current_test.get_test_step_counters()

        for current_ntime in range(1, ntimes + 1):
            tc.inc_state(enums_data.STATE_FAILED, reason_of_state="on purpose", description=f"run {current_ntime}")

            if tc.get_last_consecutive_qty(enums_data.STATE_FAILED) >= 3:
                rm.test_info(current_test, tc, "DEBUG")
                rm.testFailed(current_test, "consecutive fails")
                return

        rm.testPassed(current_test, "Impossible to pass")


class SuiteDemo_02:
    """
    @LEVEL 1
    @TAG DEMO
    """

    # just pass the tests with OK reason
    def test_04_simple_pass(self, sd: SuiteDetails, rm, ncycles=4, param={}):
        """
        @NAME sameName
        @TAG DEMO no_run
        @LEVEL 4
        @PRIO 10
        """
        current_test: TestDetails = rm.startTest(sd)
        rm.test_info(current_test, "test dict: " + prettify(current_test.get_attr()), "DEBUG")
        rm.test_info(current_test, "test param: " + str(param), "DEBUG")
        rm.testPassed(current_test, "OK")

    # fail the test outside by raise exception from assert
    def test_05_simple_fail(self, sd: SuiteDetails, rm, ncycles=2, param={}):
        """
        @NAME sameName
        @TAG DEMO no_run RAISE FAILING
        @LEVEL 5
        @PRIO 30
        @DEPENDS 10
        """
        assert 1 == 0, "Why (1 != 0) ?"


class SuiteDemo_03:
    """
    @LEVEL 1
    @TAG DEMO
    """

    def wont_run_test_without_prefix(self, sd: SuiteDetails, rm, ncycles=4, param={}):
        """
        @LEVEL 1
        """
        rm.testFailed(rm.startTest(sd))

    def test_pass_test_with_exception(self, sd: SuiteDetails, rm, ncycles=1, param=None):
        """
        @LEVEL 1
        @TAG RAISE FAILING
        """
        raise ExpectedError("1 can't be equal to 0")

class SuiteDemo_04:
    """
    @LEVEL 1
    @TAG DEPENDENCIES DEMO
    """

    def test_will_pass1(self, sd: SuiteDetails, rm: ReportManager, ncycles=1, param={}):
        """
        @LEVEL 1
        @PRIO 2
        """
        rm.testPassed(rm.startTest(sd))

    def test_will_pass2(self, sd: SuiteDetails, rm: ReportManager, ncycles=1, param={}):
        """
        @LEVEL 1
        @PRIO 3
        """
        rm.testPassed(rm.startTest(sd))

    def test_will_fail(self, sd: SuiteDetails, rm: ReportManager, ncycles=1, param={}):
        """
        @LEVEL 1
        @PRIO 3
        """
        rm.testFailedKnownBug(rm.startTest(sd))

    def test_must_run_on_success(self, sd: SuiteDetails, rm, ncycles=1, param=None):
        """
        @LEVEL 1
        @PRIO 10
        @ON_SUCCESS 2 3
        """
        rm.testPassed(rm.startTest(sd), "both prio 2 and 3 passed")

    def test_must_run_on_failure(self, sd: SuiteDetails, rm, ncycles=1, param=None):
        """
        @LEVEL 1
        @PRIO 11
        @ON_FAILURE 3
        """
        rm.testPassed(rm.startTest(sd), "prio 4 failed")

    def test_will_be_skipped_because_no_failure(self, sd: SuiteDetails, rm, ncycles=1, param=None):
        """
        @LEVEL 1
        @PRIO 12
        @ON_FAILURE 2
        """
        rm.testFailed(rm.startTest(sd), "This test must be skipped!")


class SuiteDemoWeb:
    """
    @LEVEL 3
    @TAG WEB
    """

    def test_search(self, sd: SuiteDetails, rm, ncycles=1, param=None):
        """
        @LEVEL 3
        @PRIO 50
        """
        current_test = rm.startTest(sd)

        rm.get_bm().setup_webdriver("chrome")
        rm.test_step(current_test, enums_data.STATE_PASSED, "setup web browser")

        rm.get_bm().goto("https://search.brave.com/").take_screenshot(current_test)
        rm.test_step(current_test, enums_data.STATE_PASSED, "open browser")

        rm.get_bm().click_and_type("input[id='searchbox']", text_to_send="Pedro Nunes").take_screenshot(current_test, "brave")
        rm.test_step(current_test, enums_data.STATE_PASSED, "search")

        rm.get_bm().new_tab("https://pplware.sapo.pt/", "tab 2").take_screenshot(current_test, "pplware")
        rm.test_step(current_test, enums_data.STATE_PASSED, "open new tab")

        rm.get_bm().close_tab("tab 2")
        rm.test_step(current_test, enums_data.STATE_PASSED, "close tab")

        rm.get_bm().close_page()
        rm.test_step(current_test, enums_data.STATE_PASSED, "close page")

        rm.get_bm().sleep(1).stop()
        rm.test_step(current_test, enums_data.STATE_PASSED, "stop playwright")

        rm.testPassed(current_test, "ok")
