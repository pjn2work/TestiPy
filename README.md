## TestiPy - Python Test Tool

[![PyPI Version](https://img.shields.io/pypi/v/TestiPy.svg)](https://pypi.python.org/pypi/TestiPy)
[![Python Versions](https://img.shields.io/pypi/pyversions/TestiPy.svg)](https://pypi.org/project/TestiPy)

This documentation provides an overview of TestiPy, a Python tool designed for test selection, execution, and reporting. TestiPy offers features like test management, parallel execution, and integration with various reporting tools. It aims to streamline the testing process, making it easier to organize, execute, and analyze test results.


# 1. Installation
  - ## From GitHub
    - Clone this repo:
      ```bash
      git clone https://github.com/pjn2work/TestiPy.git
      ```
    - Change any setting you'd like inside this file [default_config.py](https://github.com/pjn2work/TestiPy/blob/main/testipy/configs/default_config.py) \(this step is optional\)
    - Install:
      ```bash
      # Windows
      install.bat
      ```
      ```bash
      # Linux or Mac
      ./install.sh
      ```
  - ## From PyPi
    ```bash
    pip install testipy
    ```


# 2. Running TestiPy
  - ## if you didn't install it, just cloned
    ```bash
    # goto your folder where you've cloned this repo
    cd /where_you_have_cloned_this_repo

    # run demo tests indicating where the tests are and using the web reporter
    python testipy/run.py -tf testipy/tests -r web
    ```
  - ## if you install
    ```bash
    # run demo tests indicating where the tests are and using the web reporter
    testipy -tf /where_you_have_cloned_this_repo/testipy/tests -r web
    ```


# 2.1. Test selection options:
  Select Tests (by tags coded in suites and tests with @TAG, @NAME, @LEVEL, @FEATURES)
  #### options (excludes have higher importance over includes):
      -ip         Include Package (ex: -is qa.regression -es qa.regression.dev), can be several
      -ep         Exclude Package
      -is         Include Suite (ex: -is suiteCertificates -is MICROSERVICES -es DEV), can be several
      -es         Exclude Suite
      -it         Include Test (ex: -it REST), can be several
      -et         Exclude Test
      -sb         filename of the StoryBoard to run (ex: -sb storyboard_QA_rest.json -sb "/qa/tests/sb/sb01.json"), can be several
      -ilv        Include tests of level y (ex: -ilv 5 -ilv 8)
      -elv        Exclude tests of level y
      -alv        Include tests above level y (ex: -alv 5)
      -blv        Include tests below level y
      -if         Include tests by @FEATURES tag (ex: -if 850222)
      -ef         Exclude tests by @FEATURES tag
      -itn        Include tests by @TN tag (beginsWith) (ex: -itn 1.3.1.10)
      -etn        Exclude tests by @TN tag (beginsWith)


# 2.2. Select Reporters
  - ### options:
    * **-reporter** or **-r**  add Reporter (ex: -reporter echo -reporter log -reporter web)

      * **echo:** shows test execution on stdout, and errors in stderr
      * **excel:** creates an Excel file with test execution summary and test execution details
      * **log:** shows test execution on .log file, with the same name as the project_name, errors are shown in stderr
      * **portalio:** ReportPortalIO Web REST DB and reporter:
      * **slack:** tests results are sent to Slack channel
      * **web:** tests results can be seen in realtime on a browser. use **-r-web-port PORT** to specify other than 9204
      * **xml:** test results will be saved on report.xml file


# 2.3. Run:
  - ### options:
    *   `-rid`:  Run ID (e.g., `-rid 17`). If not provided, the current hour and minute will be used (e.g., `2359`).
    *   `-pn`: Project Name (e.g., `-pn my_project`).
    *   `-env`: Environment Name for testing (e.g., `-env qa`).
    *   `-rf`: Results Folder (e.g., `-rf /path/to/results/`), where test results will be stored.
    *   `-tf`: Tests Folder (e.g., `-tf /path/to/tests/`), the directory containing test scripts.
    *   `-r` or `-reporter`: Add a reporter (e.g., `-r echo -r log -r web`).
        *   Available reporters include: `echo`, `excel`, `log`, `portalio`, `slack`, `web`, `xml`.
    *   `-repeat`: Number of times to repeat the test execution (e.g., `-repeat 3`).
    *   `-st`: Suite Threads (1 to 8), controls the number of suites that can run in parallel (e.g., `-st 4`).

  - ### flags
    *   `--dryrun`: Runs tests without actual execution (all tests are marked as 'SKIPPED').
    *   `--debugcode`: Disables try/except blocks in tests, showing detailed error messages.
    *   `--debug-testipy`: Shows stack traces for TestiPy classes (useful for debugging the tool itself).
    *   `--1`: Overrides the default number of test cycles (ncycles) defined in test suites, forcing all tests to run only once.
    *   `--prof`: Generates a `.prof` file with profiling data.


# 3. Example of usage:
  - #### Example of usage:
    ```
    python3 run.py -env dev -reporter log -reporter web -rid 1 -tf "/home/testipy/my_test_scripts" -et NO_RUN -it DEV
    ```
  - #### Storyboard:
      - If storyboard passed, tests will run by the order defined on json file
      - If no storyboard is passed, then tests will run ordered (DESC) by package name, @PRIO defined on suite, then by @PRIO defined on test itself
  - #### Results Folder:
      - A folder will be created under the (specified -rf option) composed by: projectName_currentDate_RID (ex: testipy_20201231_00525)
      - Under the folder defined above, subfolders can be created with package_name/suite_name containing the tests results (created by each reporter)
  - #### Tests not ended:
      - If a test ends without being formally ended (by a testFailed, testSkipped or testPassed), it will be passed by the executor


In addition to the reporter-specific outputs, TestiPy creates a `results.yaml` file in the results folder, containing a summary of the overall test execution results.

This tool provides a flexible and customizable framework for Python testing, offering features for test organization, execution control, and comprehensive reporting through various channels.


For integrations with Behave framework, [check the example here](https://github.com/pjn2work/testipy-tests)


# 4. Suite Example
``` python
from typing import Dict

from testipy.helpers.handle_assertions import ExpectedError
from testipy.reporter import ReportManager

from pet_store_toolbox import Toolbox


_new_pet = {
                "id": 1,
                "name": "Sissi",
                "category": {
                    "id": 1,
                    "name": "Dogs"
                },
                "photoUrls": [""],
                "tags": [
                    {
                        "id": 0,
                        "name": "Schnauzer"
                    },
                    {
                        "id": 0,
                        "name": "mini"
                    }
                ],
                "status": "available"
            }


class SuitePetStore:
    """
    @LEVEL 1
    @TAG PETSTORE
    @PRIO 2
    """

    def __init__(self):
        self.toolbox = Toolbox()

    # Create a new pet
    def test_create_pet_valid(self, sd: SuiteDetails, rm: ReportManager, ncycles=1, param=None):
        """
        @LEVEL 3
        @PRIO 5
        """
        current_test = rm.startTest(sd)

        data = {
            "control": {"expected_status_code": 200},
            "param": _new_pet,
            "expected_response": _new_pet
        }

        try:
            self.toolbox.post_pet(rm, current_test, data, "create_pet")
        except Exception as ex:
            rm.testFailed(current_test, reason_of_state=str(ex), exc_value=ex)
        else:
            rm.testPassed(current_test, reason_of_state="pet created")

    # Get the pet created before
    def test_get_pet_valid(self, sd: SuiteDetails, rm: ReportManager, ncycles=1, param=None):
        """
        @LEVEL 3
        @PRIO 10
        @ON_SUCCESS 5
        """
        current_test = rm.startTest(sd)

        data = {
            "control": {"expected_status_code": 200},
            "param": _new_pet["id"],
            "expected_response": _new_pet
        }

        try:
            self.toolbox.get_pet(rm, current_test, data, "get_pet")
        except Exception as ex:
            rm.testFailed(current_test, reason_of_state=str(ex), exc_value=ex)
        else:
            rm.testPassed(current_test, reason_of_state="pet fetched")
```
