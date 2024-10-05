## TestiPy - Python Test Tool

This documentation provides an overview of TestiPy, a Python tool designed for test selection, execution, and reporting. TestiPy offers features like test management, parallel execution, and integration with various reporting tools. It aims to streamline the testing process, making it easier to organize, execute, and analyze test results.

### Inputs

TestiPy uses a combination of command-line arguments, Python decorators within test suites, and optional storyboard files to define and control test execution. Here's a breakdown of the common inputs:

*   **Command-Line Arguments:**
    *   `-rid`:  Run ID (e.g., `-rid 17`). If not provided, the current hour and minute will be used (e.g., `2359`).
    *   `-pn`: Project Name (e.g., `-pn my_project`).
    *   `-env`: Environment Name for testing (e.g., `-env qa`).
    *   `-rf`: Results Folder (e.g., `-rf /path/to/results/`), where test results will be stored.
    *   `-tf`: Tests Folder (e.g., `-tf /path/to/tests/`), the directory containing test scripts.
    *   `-reporter` or `-r`: Add a reporter (e.g., `-r echo -r log -r web`).
        *   Available reporters include: `echo`, `excel`, `log`, `portalio`, `slack`, `web`, `xml`.
    *   `-repeat`: Number of times to repeat the test execution (e.g., `-repeat 3`).
    *   `-st`: Suite Threads (1 to 8), controls the number of suites that can run in parallel (e.g., `-st 4`).
    *   `--dryrun`: Runs tests without actual execution (all tests are marked as 'SKIPPED').
    *   `--debugcode`: Disables try/except blocks in tests, showing detailed error messages.
    *   `--debug-testipy`: Shows stack traces for TestiPy classes (useful for debugging the tool itself).
    *   `--1`: Overrides the default number of test cycles (ncycles) defined in test suites, forcing all tests to run only once.
    *   `--prof`: Generates a `.prof` file with profiling data.
*   **Python Decorators:**
    *   `@LEVEL`: Defines the level of the test suite or test method.
    *   `@TAG`: Assigns tags to test suites or test methods for filtering.
    *   `@PRIO`: Sets the priority of test suites or test methods, influencing execution order.
    *   `@FEATURES`: Links tests to specific features (e.g., `@FEATURES 850222`).
    *   `@TN`: Assigns test numbers (e.g., `@TN 1.3.1.10`).
    *   `@DEPENDS`: Specifies dependencies on other tests based on their priority.
    *   `@ON_SUCCESS`: Defines tests to run only if tests with a given priority pass.
    *   `@ON_FAILURE`: Defines tests to run only if tests with a given priority fail.
*   **Storyboard Files (Optional):**
    *   JSON files used to define a specific execution order for tests, overriding the default priority-based order.

### Outputs

TestiPy produces various outputs based on the selected reporters, including:

*   **Console Output:**
    *   The `echo` reporter displays test execution progress and results on the console.
*   **Log Files:**
    *   The `log` reporter creates log files with detailed test execution information.
*   **Excel Reports:**
    *   The `excel` reporter generates Excel files with test summaries, details, and analysis.
*   **ReportPortal.io Integration:**
    *   The `portalio` reporter sends test results to the ReportPortal.io platform.
*   **Slack Notifications:**
    *   The `slack` reporter sends notifications about test results to a specified Slack channel.
*   **Web Reports:**
    *   The `web` reporter provides a real-time web interface to view test execution progress and results.
*   **JUnit XML Reports:**
    *   The `xml` reporter generates JUnit XML reports, often used for integration with CI/CD systems.

In addition to the reporter-specific outputs, TestiPy creates a `results.yaml` file in the results folder, containing a summary of the overall test execution results.

This tool provides a flexible and customizable framework for Python testing, offering features for test organization, execution control, and comprehensive reporting through various channels.