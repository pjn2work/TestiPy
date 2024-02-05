import os
import sys

from typing import List, Set, Dict
from getpass import getuser
from socket import gethostname
from dataclasses import dataclass

from testipy import __app__, __version__
from testipy.configs import default_config
from testipy.helpers import load_config
from testipy.lib_modules.args_parser import ArgsParser
from testipy.lib_modules.common_methods import get_current_short_time, get_current_short_date


@dataclass
class StartArguments:
    results_folder_base: str
    foldername_runtime: str
    full_path_results_folder_runtime: str
    full_path_tests_scripts_foldername: str

    valid_reporters: Set[str]
    project_name: str
    environment_name: str

    dryrun: bool
    debugcode: bool
    onlyonce: bool
    repetitions: int
    suite_threads: int

    storyboard: List[str]

    hostname: str
    user: str
    tests_scripts_build: Dict
    version: str = __app__ + "_" + __version__

    namespace: str = "/testipytests"

    def as_dict(self):
        return self.__dict__


class ParseStartArguments:

    def __init__(self, ap: ArgsParser):
        self.ap = ap

    # returns str, with folder id if its by jenkins parameter or timestamp
    def _get_rid(self) -> str:
        return str(self.ap.get_option("-rid", get_current_short_time())).zfill(6)

    # returns str, with witch home folder have been storing the results
    def _get_results_folder_base(self) -> str:
        return os.path.join(str(self.ap.get_option("-rf", default_config.default_results_folder)),
                            self._get_project_name())

    # returns str, with project name
    def _get_project_name(self) -> str:
        return str(self.ap.get_option("-pn", default_config.default_project_name))

    # returns str, with environment name
    def _get_environment_name(self) -> str:
        return str(self.ap.get_option("-env", default_config.default_environment_name)).lower()

    # returns str, with folder_id (ex: testipy_20201231_00123)
    def _generate_foldername_runtime(self) -> str:
        return default_config.default_foldername_separator.join(
            (self._get_project_name(),
            get_current_short_date(),
            self._get_rid())
        )

    # returns str, with folder tha will store this results
    def _build_results_folder_runtime(self, create_folder: bool = False) -> str:
        rfr = str(os.path.join(self._get_results_folder_base(), self._generate_foldername_runtime()))
        if create_folder:
            os.makedirs(rfr, exist_ok=True)
            print("DEBUG", f"Created results folder {rfr}", file=sys.stdout)
        return rfr

    # returns str, with full path to where the tests are stored, remember that all tests must be under other folders
    def _get_tests_scripts_foldername(self) -> str:
        scripts_folder = os.path.abspath(self.ap.get_option("-tf", default_config.default_testscripts_foldername))
        if not os.path.isdir(scripts_folder):
            raise FileNotFoundError(f"Scripts folder {scripts_folder} not found!")
        return scripts_folder

    # returns bool, if this will be a valid report run or just debugging issues
    def _get_valid_reporters(self) -> Set:
        return set(self.ap.get_options_arguments(["-reporter", "-r"]))

    # returns bool, if its only to show tests selected - MODE = 0
    def _is_dryrun(self) -> bool:
        return self.ap.has_flag_or_option("--dryrun")

    # returns bool, if its only to show tests selected - MODE = 0
    def _is_debugcode(self) -> bool:
        return self.ap.has_flag_or_option("--debugcode")

    # returns bool, if its only to run all tests only once
    def _is_onlyonce(self) -> bool:
        return self.ap.has_flag_or_option("--1")

    # returns list of str or None, with filenames of the storyboard - MODE = 2
    def _get_storyboard(self) -> List[str]:
        return self.ap.get_options_arguments("-sb", "")

    # returns int, with the number of test repetitions
    def _get_repetitions(self) -> int:
        try:
            rep = int(self.ap.get_option("-repeat", 1))
        except:
            rep = 1
        return rep

    def get_suite_threads(self) -> int:
        if self._is_debugcode():
            return 1

        st = int(self.ap.get_option("-st", str(default_config.suite_threads)))
        if st > 8:
            raise ValueError("Number of suite_threads cannot exceed 8.")
        return st

    def _get_tests_scripts_build(self, full_path_tests_scripts_foldername: str) -> Dict:
        try:
            filename = os.path.join(full_path_tests_scripts_foldername, default_config.tests_build_filename)
            return load_config(filename)
        except Exception as e:
            print("WARNING", f"Failed to open {filename}, {e}", file=sys.stderr)
        return {"build": 0.0, "description": ""}

    def get_start_arguments(self) -> StartArguments:
        return StartArguments(
            results_folder_base=self._get_results_folder_base(),
            foldername_runtime=self._generate_foldername_runtime(),
            full_path_results_folder_runtime=self._build_results_folder_runtime(),
            full_path_tests_scripts_foldername=self._get_tests_scripts_foldername(),

            valid_reporters=self._get_valid_reporters(),
            project_name=self._get_project_name(),
            environment_name=self._get_environment_name(),

            dryrun=self._is_dryrun(),
            debugcode=self._is_debugcode(),
            onlyonce=self._is_onlyonce(),
            repetitions=self._get_repetitions(),
            suite_threads=self.get_suite_threads(),

            storyboard=self._get_storyboard(),

            hostname = gethostname(),
            user = getuser(),
            tests_scripts_build=self._get_tests_scripts_build(self._get_tests_scripts_foldername())
        )
