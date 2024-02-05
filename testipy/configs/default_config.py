import os

from testipy.configs import enums_data

# run.py
default_project_name = "local"
default_environment_name = "dev"
default_results_folder = os.path.join(os.path.expanduser("~"),  "testipy", "results")
default_foldername_separator = "_"
tests_build_filename = "build.json"
execution_log_filename = "testipy_exe.log"
execution_prof_filename = "testipy_exe.prof"

# read_tests.py
my_app_path = os.path.dirname(os.path.dirname(__file__))
default_testscripts_foldername = os.path.join(os.path.expanduser("~"),  "testipy", "tests")
auto_include_tests_with_tags = ["SETUP", "TEARDOWN"]
execute_test_with_no_doc = True
prefix_suite = "Suite"
prefix_tests = "test_"
trim_prefix_suite = True
trim_prefix_tests = True
separator_package = "."
separator_and_join_tags = "&"

# execute_tests.py
if_no_test_started_mark_as = enums_data.STATE_PASSED
count_as_failed_states = [enums_data.STATE_FAILED]
suite_threads = 1

# report_base.py
separator_package_suite_test = "/"
separator_cycle = "#"
