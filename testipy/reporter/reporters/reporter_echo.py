from typing import Dict
from tabulate import tabulate

from testipy.lib_modules import textdecor
from testipy.lib_modules.common_methods import format_duration, prettify
from testipy.lib_modules.start_arguments import StartArguments
from testipy.reporter.reporters import df_manager as dfm
from testipy.reporter.report_manager import ReportManager, ReportBase
from testipy.configs import enums_data

_line_size = 160


def show_totals(state_counter):
    print(tabulate(state_counter.get_summary_per_state(), headers=("State", "Qty", "%", "RoS"), floatfmt=".2f", tablefmt="simple"))
    print(f"Total: {state_counter.get_total():7}")


class ReporterEcho(ReportBase):

    def __init__(self, rm: ReportManager, sa: StartArguments):
        super().__init__(self.__class__.__name__)

    def save_file(self, current_test, data, filename):
        pass

    def copy_file(self, current_test, orig_filename, dest_filename, data):
        pass

    def __startup__(self, selected_tests):
        print("\n"*2)
        print("#"*_line_size)
        print(" Selected tests to run ".center(_line_size, "#"))
        print("#"*_line_size)
        print(tabulate(selected_tests["data"], headers=selected_tests["headers"], tablefmt="simple"))
        print("\n"*2)

    def __teardown__(self, end_state):
        # get manager base
        mb = self.get_report_manager_base()

        # get results DataFrame
        df = mb.get_df()

        # exit if nothing to show
        if df.shape[0] == 0:
            return

        # show results
        print("\n"*6)
        print("#"*_line_size)
        print(" Teardown {} ".format(mb.get_reporter_details()).center(_line_size, "#"))
        print("#"*_line_size)
        #show_totals(mb.get_reporter_counter())

        # get resume tables
        df = mb.get_df()
        #df = df[df["Package"] == mb.get_package_name(False)]
        #df = df[df["Suite"] == mb.get_suite_name(False)]

        # show resume tables
        print("")
        print(textdecor.color_line(tabulate(dfm.reduce_datetime(dfm.get_test_ros_summary(df).drop(columns=["End time"])), headers='keys', tablefmt='simple', showindex=False)))
        print("\n", ".  "*int(_line_size/3), "\n")
        print(tabulate(dfm.reduce_datetime(dfm.get_test_dummies(df)), headers='keys', tablefmt='simple', showindex=False))
        print("\n", ".  "*int(_line_size/3), "\n")
        print(textdecor.color_line(tabulate(dfm.reduce_datetime(dfm.get_suite_state_summary(df)), headers='keys', tablefmt='simple', showindex=False)))
        print("#"*_line_size)

    def startPackage(self, package_name):
        pass

    def endPackage(self):
        pass

    def startSuite(self, suite_name, attr=None):
        pass

    def endSuite(self):
        pass

    def startTest(self, attr: Dict, test_name: str = "", usecase: str = "", description: str = ""):
        mb = self.get_report_manager_base()
        current_test = mb.get_current_test()

        test_id = current_test.get_test_id()  # attr["test_id"]
        test_prio = str(current_test.get_prio())
        usecase = f" - {usecase}" if usecase else ""

        print("\n"*5)
        print("-"*_line_size)
        print(f"> Starting new test: {current_test} <".center(_line_size, "-"))
        # print("\n".join([f"{k} {str(v).replace('set()', '')}" for k, v in attr.items() if k.startswith("@")]))

    def testInfo(self, current_test, info, level, attachment=None):
        mb = self.get_report_manager_base()
        full_name = mb.get_full_name(current_test, True)
        usecase = current_test.get_usecase()

        print(f"{level} {full_name} - {usecase}: {prettify(info)}")

    def testStep(self, current_test, state: str, reason_of_state: str = "", description: str = "", take_screenshot: bool = False, qty: int = 1, exc_value: BaseException = None):
        pass

    def testSkipped(self, current_test, reason_of_state="", exc_value: BaseException = None):
        self._endTest(current_test, enums_data.STATE_SKIPPED, reason_of_state, exc_value)

    def testPassed(self, current_test, reason_of_state="", exc_value: BaseException = None):
        self._endTest(current_test, enums_data.STATE_PASSED, reason_of_state, exc_value)

    def testFailed(self, current_test, reason_of_state="", exc_value: BaseException = None):
        self._endTest(current_test, enums_data.STATE_FAILED, reason_of_state, exc_value)

    def testFailedKnownBug(self, current_test, reason_of_state="", exc_value: BaseException = None):
        self._endTest(current_test, enums_data.STATE_FAILED_KNOWN_BUG, reason_of_state, exc_value)

    def showStatus(self, message: str):
        pass

    def showAlertMessage(self, message: str):
        pass

    def inputPromptMessage(self, message: str, default_value: str = ""):
        pass

    def _endTest(self, current_test, ending_state, end_reason, exc_value: BaseException = None):
        mb = self.get_report_manager_base()

        full_name = mb.get_full_name(current_test, True)
        duration = current_test.get_duration()
        usecase = current_test.get_usecase()
        ending_state = textdecor.color_status(ending_state)

        self.__log_test_steps(current_test)

        print()
        print(f"> Ending test {full_name} - {ending_state} - took {format_duration(duration)} - {usecase} - reason: {end_reason} <".center(_line_size, "-"))
        print("-"*_line_size)

    def __log_test_steps(self, current_test):
        tc = current_test.get_test_step_counters()
        if len(tc.get_timed_laps()) > 0:
            print("\n" + current_test.get_test_step_counters_tabulate())
            str_res = "\nSteps Summary: " + tc.summary(verbose=False)
        else:
            str_res = "\nTest Summary: " + current_test.get_counters().summary(verbose=False)
        print(str_res)
