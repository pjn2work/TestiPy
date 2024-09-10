#!/usr/bin/env python3

import os
import sys
import cProfile, pstats

from typing import Dict, List
from tabulate import tabulate


# allow root folder to be available for imports
TESTIPY_ROOT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if TESTIPY_ROOT_FOLDER not in sys.path:
    sys.path.insert(0, TESTIPY_ROOT_FOLDER)

from testipy import get_exec_logger
from testipy.configs import default_config, enums_data
from testipy.engine import read_files_to_get_selected_tests, run_selected_tests
from testipy.engine.models import PackageAttr
from testipy.reporter.report_manager import build_report_manager_with_reporters
from testipy.helpers import get_traceback_list, format_duration, prettify
from testipy.lib_modules.args_parser import ArgsParser
from testipy.lib_modules.common_methods import get_app_version
from testipy.engine.execution_logger import ExecutionLogger
from testipy.lib_modules.start_arguments import ParseStartArguments, StartArguments


__app__, __version__, __app_full__ = get_app_version()
_exec_logger = get_exec_logger()


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
    def __init__(self, ap: ArgsParser, sa: StartArguments):
        # configurations and logging
        self.ap = ap
        self.sa = sa

        # Log running parameters
        p = tabulate([(k, v) for k, v in self.sa.as_dict().items()], headers=("Parameter", "Value"), tablefmt="simple")
        _exec_logger.debug("Runtime Parameters:\n" + p)

        # Change working directory to tests directory and added to sys.path
        os.chdir(self.sa.full_path_tests_scripts_foldername)
        sys.path.insert(0, self.sa.full_path_tests_scripts_foldername)

        # Select tests to run based on args filters
        self.selected_tests: List[PackageAttr] = read_files_to_get_selected_tests(
            ap=ap,
            storyboard_json_files=sa.storyboard,
            full_path_tests_scripts_foldername=sa.full_path_tests_scripts_foldername,
            verbose=sa.debug_testipy
        )
        if len(self.selected_tests) == 0:
            raise FileNotFoundError(f"Found no tests under {sa.full_path_tests_scripts_foldername}")

        # Reporter Manager, with all reporters
        self.report_manager = build_report_manager_with_reporters(ap, sa)

    # Execute Tests
    def run(self) -> int:
        total_fails = 0

        for rep in range(1, self.sa.repetitions + 1):
            _exec_logger.info(f"--- Execution #{rep} ---")
            try:
                total_fails += run_selected_tests(
                    sa=self.sa,
                    selected_tests=self.selected_tests,
                    rm=self.report_manager
                )
            except Exception as ex:
                total_fails += 1
                _exec_logger.error(f"Execution #{rep} - {ex}")

                if self.sa.debug_testipy:
                    raise ex

        return total_fails

    def __enter__(self):
        self.report_manager._startup_(self.selected_tests)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.report_manager._teardown_(None)

        if exc_val and self.sa.debug_testipy:
            _exec_logger.error(prettify(get_traceback_list(exc_val)))
            raise exc_val

        # export the overall results
        f = os.path.join(self.sa.full_path_results_folder_runtime, "results.yaml")
        self.report_manager.pm.state_counter.export_summary_to_file(f)

        return self

    @property
    def duration(self) -> str:
        return format_duration(self.report_manager.get_reporter_duration())


def save_stats(folder: str, prof):
    stats = pstats.Stats(prof)
    stats.sort_stats(pstats.SortKey.TIME)

    filename = os.path.join(folder or os.path.dirname(__file__), default_config.execution_prof_filename)
    stats.dump_stats(filename=filename)


def run_testipy(args=None) -> int:
    show_intro()

    fails = 1
    try:
        ap = ArgsParser.from_str(args) if args else ArgsParser.from_sys()
        sa = ParseStartArguments(ap).get_start_arguments()

        with ExecutionLogger(sa.full_path_results_folder_runtime, sa.debug_testipy) as exec_logger:
            with Runner(ap, sa) as runner:
                if ap.has_flag_or_option("--prof"):
                    with cProfile.Profile() as prof:
                        fails = runner.run()
                    save_stats(sa.full_path_results_folder_runtime, prof)
                else:
                    fails = runner.run()

            exec_logger.log_info(f"exitcode={fails} | Results at {sa.full_path_results_folder_runtime}")
    except Exception as ex:
        print(ex, file=sys.stderr)
        # remove comment for debug purpose
        raise ex

    return fails


if __name__ == "__main__":
    sys.exit(run_testipy())
