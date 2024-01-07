#!/usr/bin/env python3

import os
import sys
import cProfile, pstats

from tabulate import tabulate

# allow root folder to be available for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from testipy.configs import default_config
from testipy.engine import read_tests, execute_tests
from testipy.helpers import get_traceback_list, format_duration, prettify
from testipy.lib_modules.args_parser import ArgsParser
from testipy.lib_modules.common_methods import get_app_version
from testipy.lib_modules.execution_logger import ExecutionLogger
from testipy.lib_modules.start_arguments import ParseStartArguments, StartArguments
from testipy.reporter.report_manager import build_report_manager_with_reporters


__app__, __version__, __app_full__ = get_app_version()


# <editor-fold desc="--- Just for fun ---">
def show_intro():
    try:
        from pyfiglet import Figlet
        print()
        print(Figlet(font="slant").renderText(f"{__app__} {__version__}"))
        print(sys.version)
    except:
        print("WARNING", "no fun if no pyfiglet installed.\nuse: pip3 install pyfiglet", file=sys.stderr)

    print(f"{__app_full__} - {__version__}")
    print("="*160, "\n")
# </editor-fold>


class Runner:
    def __init__(self, ap: ArgsParser, sa: StartArguments, execution_log):
        # configurations and logging
        self.ap = ap
        self.sa = sa
        self.execution_log = execution_log

        # Log running parameters
        p = tabulate([(k, v) for k, v in self.sa.as_dict().items()], headers=("Parameter", "Value"), tablefmt="simple")
        self.execution_log("DEBUG", "Runtime Parameters:\n" + p)

        # Change working directory to tests directory and added to sys.path
        os.chdir(self.sa.full_path_tests_scripts_foldername)
        sys.path.insert(1, self.sa.full_path_tests_scripts_foldername)

        # Select tests to run based on args filters
        self.selected_tests = read_tests.run(execution_log,
                                             ap,
                                             sa.storyboard,
                                             sa.full_path_tests_scripts_foldername,
                                             verbose=self.sa.dryrun or ap.has_flag_or_option("--debug-testipy"))
        if len(self.selected_tests) == 0:
            raise FileNotFoundError(f"Found no tests under {sa.full_path_tests_scripts_foldername}")

        # Reporter Manager, with all reporters
        self.report_manager = build_report_manager_with_reporters(execution_log, self.selected_tests, ap, sa)

    # Execute Tests
    def run(self) -> int:
        total_fails = 0

        for rep in range(1, self.sa.repetitions + 1):
            self.execution_log("INFO", f"--- Execution #{rep} ---")
            try:
                total_fails += execute_tests.run(self.execution_log, self.sa, self.selected_tests, self.report_manager)
            except Exception as ex:
                total_fails += 1
                self.execution_log("ERROR", f"Execution #{rep} - {ex}")

                if self.ap.has_flag_or_option("--debug-testipy"):
                    raise ex

        return total_fails

    def __enter__(self):
        self.report_manager.__startup__(self.selected_tests)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.report_manager.__teardown__(None)

        if exc_val and self.ap.has_flag_or_option("--debug-testipy"):
            print(prettify(get_traceback_list(exc_val)))

        return self

    @property
    def duration(self) -> str:
        return format_duration(self.report_manager.get_reporter_duration())


def save_stats(folder: str, prof):
    stats = pstats.Stats(prof)
    stats.sort_stats(pstats.SortKey.TIME)

    filename = os.path.join(folder or os.path.dirname(__file__), default_config.execution_prof_filename)
    stats.dump_stats(filename=filename)


def run_testipy(args=None):
    show_intro()

    fails = 1
    try:
        ap = ArgsParser.from_str(args) if args else ArgsParser.from_sys()
        sa = ParseStartArguments(ap).get_start_arguments()

        with ExecutionLogger(sa.results_folder_runtime) as log:
            with Runner(ap, sa, log.execution_log) as runner:
                if ap.has_flag_or_option("--prof"):
                    with cProfile.Profile() as prof:
                        fails = runner.run()
                    save_stats(sa.results_folder_runtime, prof)
                else:
                    fails = runner.run()

            print(f"exitcode={fails} | Results at {sa.results_folder_runtime}")
    except Exception as ex:
        print(ex, file=sys.stderr)

    sys.exit(fails)


if __name__ == "__main__":
    run_testipy()
