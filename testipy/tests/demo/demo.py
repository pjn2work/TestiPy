from time import sleep

from testipy.configs import enums_data


class SuiteDemo_01:
    """
    @NAME DemoSuite_001
    @TAG DEMO no_run
    @LEVEL 1
    @PRIO 50
    """

    def test_00_cannot_run(self, td, rm, ncycles=2, ntimes=5, param=dict()):
        """
        @TAG DEMO no_run
        @LEVEL 0
        """
        current_test = rm.startTest(td)
        rm.testFailed(current_test, "This test cannot run EVER!")

    def test_01_show_internal_counters(self, td, rm, ncycles=2, ntimes=5, param=dict()):
        """
        @TAG DEMO no_run
        @LEVEL 1
        """

        for current_ncycle in range(1, ncycles + 1):
            current_test = rm.startTest(td)

            for current_ntime in range(1, ntimes + 1):
                sleep(0.1)
                current_test.testStep(enums_data.STATE_SKIPPED, "Skip all")

            attachment={"name": "results.txt",
                        "data": str(current_test.get_test_step_counters()),
                        "mime": "text/plain"}
            rm.testInfo(current_test, current_test.get_test_step_counters(), "DEBUG", attachment)

            rm.testSkipped(current_test, "Ran {} times".format(current_ntime))

    # despite the two FOR, it will run only once, error handled outside on engine.execute_tests
    def test_02_division_by_zero(self, td, rm, ncycles=3, ntimes=5, param=dict(stop_at=1)):
        """
        @TAG DEMO no_run
        @LEVEL 2
        """
        current_test = rm.startTest(td)
        for current_ntime in range(1, ntimes + 1):
            if current_ntime > param["stop_at"]:
                a = 1 / 0
        rm.testFailedKnownBug(current_test, "Impossible to pass the second time")

    # it will exit after 3 consecutive fails
    def test_03_exit_after_several_fails(self, td, rm, ncycles=3, ntimes=10, param=dict()):
        """
        @TAG DEMO no_run
        @LEVEL 3
        @PRIO 90
        """
        current_test = rm.startTest(td)
        tc = current_test.get_test_step_counters()

        for current_ntime in range(1, ntimes + 1):
            tc.inc_state(enums_data.STATE_FAILED, reason_of_state="on purpose", description=f"run {current_ntime}")

            if tc.get_last_consecutive_qty(enums_data.STATE_FAILED) >= 3:
                rm.testInfo(current_test, tc, "DEBUG")
                rm.testFailed(current_test, "consecutive fails")
                return

        rm.testPassed(current_test, "Impossible to pass")


class SuiteDemo_02:
    """
    @LEVEL 1
    @TAG DEMO
    @PRIO 80
    """

    # just pass the tests with OK reason
    def test_04_simple_pass(self, td, rm, ncycles=4, ntimes=1, param=dict()):
        """
        @NAME sameName
        @TAG DEMO no_run
        @LEVEL 4
        @PRIO 10
        """
        for current_ncycle in range(1, ncycles + 1):
            current_test = rm.startTest(td)
            rm.testInfo(current_test, "test dict: " + str(td), "DEBUG")
            rm.testInfo(current_test, "test param: " + str(param), "DEBUG")
            rm.testPassed(current_test, "OK" +str(current_ncycle))

    # fail the test outside by raise exception from assert
    def test_05_simple_fail(self, td, rm, ncycles=2, ntimes=1, param=dict()):
        """
        @NAME sameName
        @TAG DEMO no_run
        @LEVEL 5
        @PRIO 30
        """
        for current_ncycle in range(1, ncycles + 1):
            rm.startTest(td)
            assert 1 == 0, "Why (1 != 0) ?"


class SuiteDemo_03:
    """
    @LEVEL 1
    """

    def run_test_without_prefix(self, td, rm, ncycles=4, ntimes=1, param=dict()):
        """
        @LEVEL 1
        """
        rm.testFailed(rm.startTest(td))


class SuiteDemoWeb:
    """
    @LEVEL 3
    @PRIO 90
    @TAG WEB
    """

    def test_search(self, td, rm, ncycles=1, ntimes=1, param=None):
        """
        @LEVEL 3
        @PRIO 50
        """
        current_test = rm.startTest(td)

        rm.get_bm().setup_webdriver("chrome")
        rm.testStep(current_test, enums_data.STATE_PASSED, "setup web browser")

        rm.get_bm().goto("https://search.brave.com/").take_screenshot(current_test)
        rm.testStep(current_test, enums_data.STATE_PASSED, "open browser")

        rm.get_bm().click_and_type("input[class='form-input']", text_to_send="pedro").take_screenshot(current_test)
        rm.testStep(current_test, enums_data.STATE_PASSED, "search")

        rm.get_bm().new_tab("https://pplware.sapo.pt/", "tab 2").take_screenshot(current_test)
        rm.testStep(current_test, enums_data.STATE_PASSED, "open new tab")

        rm.get_bm().sleep(4).close_tab("tab 2")
        rm.testStep(current_test, enums_data.STATE_PASSED, "close tab")

        rm.get_bm().sleep(4).close_page()
        rm.testStep(current_test, enums_data.STATE_PASSED, "close page")

        rm.get_bm().sleep(4).stop()
        rm.testStep(current_test, enums_data.STATE_PASSED, "stop playwright")

        rm.testPassed(current_test, "ok")
