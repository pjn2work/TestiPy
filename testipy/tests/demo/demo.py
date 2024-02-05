from time import sleep

from testipy.configs import enums_data
from testipy.helpers.handle_assertions import ExpectedError
from testipy.reporter import ReportManager


class SuiteDemo_01:
    """
    @NAME DemoSuite_001
    @TAG DEMO no_run
    @LEVEL 1
    """

    def test_06_will_run(self, ma, rm: ReportManager, ncycles=1, param=None):
        current_test = rm.startTest(ma)
        rm.testPassed(current_test, "test without doc tags")

    def test_00_cannot_run(self, ma, rm, ncycles=2, param=dict()):
        """
        @TAG DEMO no_run
        @LEVEL 0
        """
        current_test = rm.startTest(ma)
        rm.testFailed(current_test, "This test cannot run EVER!")

    def test_01_show_internal_counters(self, ma, rm, ncycles=2, ntimes=5, param=dict()):
        """
        @TAG DEMO no_run
        @LEVEL 1
        """
        current_test = rm.startTest(ma)

        for current_ntime in range(1, ntimes + 1):
            sleep(0.01)
            current_test.test_step(enums_data.STATE_SKIPPED, "Skip all")

        attachment={"name": "results.txt",
                    "data": str(current_test.get_test_step_counters()),
                    "mime": "text/plain"}
        rm.test_info(current_test, current_test.get_test_step_counters(), "DEBUG", attachment)

        rm.testSkipped(current_test, "Ran {} times".format(current_ntime))

    # despite the two FOR, it will run only once, error handled outside on engine.execute_tests
    def test_02_division_by_zero(self, ma, rm, ncycles=3, ntimes=5, param=dict(stop_at=1)):
        """
        @TAG DEMO no_run
        @LEVEL 2
        """
        current_test = rm.startTest(ma)
        for current_ntime in range(1, ntimes + 1):
            if current_ntime > param["stop_at"]:
                a = 1 / 0
        rm.testFailedKnownBug(current_test, "Impossible to pass the second time")

    # it will exit after 3 consecutive fails
    def test_03_exit_after_several_fails(self, ma, rm, ncycles=3, ntimes=10, param=dict()):
        """
        @TAG DEMO no_run
        @LEVEL 3
        @PRIO 90
        """
        current_test = rm.startTest(ma)
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
    def test_04_simple_pass(self, ma, rm, ncycles=4, param=dict()):
        """
        @NAME sameName
        @TAG DEMO no_run
        @LEVEL 4
        @PRIO 10
        """
        current_test = rm.startTest(ma)
        rm.test_info(current_test, "test dict: " + str(ma), "DEBUG")
        rm.test_info(current_test, "test param: " + str(param), "DEBUG")
        rm.testPassed(current_test, "OK")

    # fail the test outside by raise exception from assert
    def test_05_simple_fail(self, ma, rm, ncycles=2, param=dict()):
        """
        @NAME sameName
        @TAG DEMO no_run
        @LEVEL 5
        @PRIO 30
        """
        rm.startTest(ma)
        assert 1 == 0, "Why (1 != 0) ?"


class SuiteDemo_03:
    """
    @LEVEL 1
    @TAG DEMO
    """

    def wont_run_test_without_prefix(self, ma, rm, ncycles=4, param=dict()):
        """
        @LEVEL 1
        """
        rm.testFailed(rm.startTest(ma))

    def test_pass_test_with_exception(self, ma, rm, ncycles=1, param=None):
        """
        @LEVEL 1
        """
        raise ExpectedError("1 can't be equal to 0")

class SuiteDemo_04:
    """
    @LEVEL 1
    @TAG DEPENDENCIES DEMO
    """

    def test_will_pass1(self, ma: dict, rm: ReportManager, ncycles=1, param=dict()):
        """
        @LEVEL 1
        @PRIO 2
        """
        rm.testPassed(rm.startTest(ma))

    def test_will_pass2(self, ma: dict, rm: ReportManager, ncycles=1, param=dict()):
        """
        @LEVEL 1
        @PRIO 3
        """
        rm.testPassed(rm.startTest(ma))

    def test_will_fail(self, ma: dict, rm: ReportManager, ncycles=1, param=dict()):
        """
        @LEVEL 1
        @PRIO 3
        """
        rm.testFailedKnownBug(rm.startTest(ma))

    def test_must_run_on_success(self, ma, rm, ncycles=1, param=None):
        """
        @LEVEL 1
        @PRIO 10
        @ON_SUCCESS 2 3
        """
        rm.testPassed(rm.startTest(ma), "both prio 2 and 3 passed")

    def test_must_run_on_failure(self, ma, rm, ncycles=1, param=None):
        """
        @LEVEL 1
        @PRIO 11
        @ON_FAILURE 3
        """
        rm.testPassed(rm.startTest(ma), "prio 4 failed")

    def test_will_be_skipped_because_no_failure(self, ma, rm, ncycles=1, param=None):
        """
        @LEVEL 1
        @PRIO 12
        @ON_FAILURE 2
        """
        rm.testFailed(rm.startTest(ma), "This test must be skipped!")


class SuiteDemoWeb:
    """
    @LEVEL 3
    @TAG WEB
    """

    def test_search(self, ma, rm, ncycles=1, param=None):
        """
        @LEVEL 3
        @PRIO 50
        """
        current_test = rm.startTest(ma)

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
