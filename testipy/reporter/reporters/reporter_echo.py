from typing import Dict
from tabulate import tabulate

from testipy.configs import enums_data
from testipy.helpers import format_duration, prettify
from testipy.lib_modules import textdecor
from testipy.lib_modules.start_arguments import StartArguments
from testipy.reporter.reporters import df_manager as dfm
from testipy.reporter import ReportManager, ReportInterface, PackageDetails, SuiteDetails, TestDetails

_line_size = 160


def show_totals(state_counter):
    print(tabulate(state_counter.get_summary_per_state(), headers=("State", "Qty", "%", "RoS"), floatfmt=".2f", tablefmt="simple"))
    print(f"Total: {state_counter.get_total():7}")


class ReporterEcho(ReportInterface):

    def __init__(self, rm: ReportManager, sa: StartArguments):
        super().__init__(self.__class__.__name__)
        self.rm = rm
        self.sa = sa

    def save_file(self, current_test: TestDetails, data, filename: str):
        pass

    def copy_file(self, current_test: TestDetails, orig_filename: str, dest_filename: str, data):
        pass

    def _startup_(self, selected_tests: Dict):
        print("\n"*2)
        print("#"*_line_size)
        print(" Selected tests to run ".center(_line_size, "#"))
        print("#"*_line_size)
        print(tabulate(selected_tests["data"], headers=selected_tests["headers"], tablefmt="simple"))
        print("\n"*2)

    def _teardown_(self, end_state: str):
        # get results DataFrame
        df = self.rm.get_df()

        # exit if nothing to show
        if df.shape[0] == 0:
            return

        summary = f"{self.rm.pm.state_counter.get_state_percentage(enums_data.STATE_PASSED):.2f}% [{self.rm.pm.state_counter}] took {format_duration(self.rm.pm.get_duration())}"

        # show results
        print("\n"*6)
        print("#"*_line_size)
        print(f" Teardown {summary} ".center(_line_size, "#"))
        print("#"*_line_size)

        # show resume tables
        print("")
        print(textdecor.color_line(tabulate(dfm.reduce_datetime(dfm.get_test_ros_summary(df).drop(columns=["End time"])), headers='keys', tablefmt='simple', showindex=False)))
        print("\n", ".  "*int(_line_size/3), "\n")
        print(tabulate(dfm.reduce_datetime(dfm.get_test_dummies(df)), headers='keys', tablefmt='simple', showindex=False))
        print("\n", ".  "*int(_line_size/3), "\n")
        print(textdecor.color_line(tabulate(dfm.reduce_datetime(dfm.get_suite_state_summary(df)), headers='keys', tablefmt='simple', showindex=False)))
        print("#"*_line_size)

    def start_package(self, pd: PackageDetails):
        pass

    def end_package(self, pd: PackageDetails):
        pass

    def start_suite(self, sd: SuiteDetails):
        pass

    def end_suite(self, sd: SuiteDetails):
        pass

    def start_test(self, current_test: TestDetails):
        print("\n"*5)
        print("-"*_line_size)
        print(f"> Starting test: {current_test} <".center(_line_size, "-"))

    def test_info(self, current_test: TestDetails, info: str, level: str, attachment: Dict=None):
        full_name = current_test.get_full_name(with_cycle_number=True)
        usecase = current_test.get_usecase()

        print(f"{level} {full_name}: {prettify(info)}")

    def test_step(self,
                  current_test: TestDetails,
                  state: str,
                  reason_of_state: str = "",
                  description: str = "",
                  take_screenshot: bool = False,
                  qty: int = 1,
                  exc_value: BaseException = None):
        pass

    def end_test(self, current_test: TestDetails, ending_state: str, end_reason: str = "", exc_value: BaseException = None):
        test_full_name = current_test.get_full_name(with_cycle_number=True)
        test_duration = current_test.get_duration()
        end_state = textdecor.color_state(ending_state)

        tc = current_test.get_test_step_counters()
        if len(tc.get_timed_laps()) > 0:
            print("\n" + current_test.get_test_step_counters_tabulate())
            print("\nSteps Summary: " + tc.summary(verbose=False))
        else:
            print("\nTest Summary: " + current_test.get_counters().summary(verbose=False))

        print(f"> {test_full_name} - {end_state} - took {format_duration(test_duration)} - reason: {end_reason} <".center(_line_size + len(end_state) - len(ending_state), "-"))
        print("-"*_line_size)

    def show_status(self, message: str):
        pass

    def show_alert_message(self, message: str):
        pass

    def input_prompt_message(self, message: str, default_value: str = ""):
        pass
