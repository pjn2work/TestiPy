from __future__ import annotations
from typing import List, Dict, TYPE_CHECKING
import os
import base64
import html

from testipy import get_exec_logger
from testipy.configs import enums_data
from testipy.helpers import prettify, format_duration
from testipy.reporter import ReportInterface
from testipy.reporter.reporters import df_manager as dfm

if TYPE_CHECKING:
    from testipy.models import PackageAttr, PackageDetails, SuiteDetails, TestDetails
    from testipy.reporter import ReportManager
    from testipy.lib_modules.start_arguments import StartArguments
    import pandas as pd


_exec_logger = get_exec_logger()

STATUS_TO_CLASS = {
    enums_data.STATE_PASSED: "passed",
    enums_data.STATE_SKIPPED: "skipped",
    enums_data.STATE_FAILED: "failed",
    enums_data.STATE_FAILED_KNOWN_BUG: "failed_bug",
}


class ReporterHtml(ReportInterface):
    def __init__(self, rm: ReportManager, sa: StartArguments):
        super().__init__(self.__class__.__name__)

        results_folder_runtime = rm.get_results_folder_runtime()
        self.filename = os.path.join(results_folder_runtime, "report.html")

        self.rm = rm
        self.sa = sa

        # create folder
        _ensure_folder(results_folder_runtime)

    def save_file(self, current_test: TestDetails, data, filename: str):
        pass

    def copy_file(
        self, current_test: TestDetails, orig_filename: str, dest_filename: str, data
    ):
        pass

    def _startup_(self, selected_tests: List[PackageAttr]):
        f_css = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "templates", "webreport.css"
        )
        with open(self.filename, "w") as f:
            with open(f_css) as css:
                f.write(
                    HTML_HEADER.format(
                        title=self.sa.environment_name
                        + "-"
                        + self.sa.foldername_runtime,
                        js_expand_test_log=_js_expand_test_log,
                        rm_params=_add_rm_params(self.sa),
                        dashboard=_get_dashboard(),
                        selected_tests=_add_selected_tests(selected_tests),
                        css=css.read(),
                    )
                )

    def _teardown_(self, end_state: str):
        sc = self.rm.pm.state_counter
        total_passed = sc[enums_data.STATE_PASSED]
        total_failed = sc[enums_data.STATE_FAILED]
        total_failed_bug = sc[enums_data.STATE_FAILED_KNOWN_BUG]
        total_skipped = sc[enums_data.STATE_SKIPPED]
        total = sc.get_total()
        total_perc = total_passed / total if total else 0

        _tear_down_js = f"""
    document.addEventListener('DOMContentLoaded', function() {{
        document.getElementById('total_passed').textContent = '{total_passed}';
        document.getElementById('total_failed').textContent = '{total_failed}';
        document.getElementById('total_failed_bug').textContent = '{total_failed_bug}';
        document.getElementById('total_skipped').textContent = '{total_skipped}';
        document.getElementById('total').textContent = '{total}';
        document.getElementById('total_perc').textContent = '{total_perc:.2%}';
        document.getElementById('total_duration').textContent = '{format_duration(self.rm.pm.get_duration())}';

        document.getElementById('summary').innerHTML = "{_get_div_summary(self.rm)}";
        expand_summary();
    }});"""

        with open(self.filename, "a") as f:
            f.write(HTML_FOOTER.format(tear_down_js=_tear_down_js))

    def start_package(self, pd: PackageDetails):
        pass

    def end_package(self, pd: PackageDetails):
        pass

    def start_suite(self, sd: SuiteDetails):
        pass

    def end_suite(self, sd: SuiteDetails):
        pass

    def start_test(self, current_test: TestDetails):
        pass

    def test_info(self, current_test: TestDetails, info, level, attachment=None):
        pass

    def test_step(
        self,
        current_test: TestDetails,
        state: str,
        reason_of_state: str = "",
        description: str = "",
        take_screenshot: bool = False,
        qty: int = 1,
        exc_value: BaseException = None,
    ):
        pass

    def end_test(
        self,
        current_test: TestDetails,
        ending_state: str,
        end_reason: str = "",
        exc_value: BaseException = None,
    ):
        package_name = current_test.suite.package.get_name()
        suite_name = current_test.suite.get_name()

        test_method_id = current_test.get_method_id()
        test_id = current_test.get_test_id()
        test_name = current_test.get_name()
        test_usecase = current_test.get_usecase()
        test_duration = current_test.get_duration()

        sc = STATUS_TO_CLASS.get(ending_state)

        with open(self.filename, "a") as f:
            f.write(f"""
                <tr>
                    <td class='{sc}'>{test_method_id}</td>
                    <td class='{sc}'>{package_name}</td>
                    <td class='{sc}'>{suite_name}</td>
                    <td class='{sc}'>{test_name}</td>
                    <td class='{sc}'>{test_id}</td>
                    <td class='{sc}'>{test_usecase}</td>
                    <td class='{sc}'>{ending_state}</td>
                    <td class='{sc}'>{format_duration(test_duration)}</td>
                    <td class='{sc}'>{end_reason}</td>
                </tr><tr class='collapse'>
                    <td colspan=9>
                        <div class='log' style='width: 98%; max-width: 2780px; height: 700px; max-height: 700px; overflow: auto;'>
                        {_format_info(current_test, ending_state, end_reason)}
                        </div>
                    </td>
                </tr>""")

    def show_status(self, message: str):
        pass

    def show_alert_message(self, message: str):
        pass

    def input_prompt_message(self, message: str, default_value: str = ""):
        pass


def _ensure_folder(folder_name: str):
    try:
        if not os.path.exists(folder_name):
            os.makedirs(folder_name, exist_ok=True)
            _exec_logger.info(f"Created folder {folder_name}")
    except:
        _exec_logger.critical(f"Could not create folder {folder_name}", "ERROR")


def _add_rm_params(sa: StartArguments) -> str:
    text = """
        <table id="rm_params" class="list" style="width: 700px; max-width: 700px; height: 100%">
            <caption>Parameters</caption>
            <tbody>
            {tbody}
            </tbody>
        </table>
    """

    tbody = ""
    for k, v in sa.as_dict().items():
        tbody += f"""
            <tr>
                <td class='label'>{k}</td>
                <td class='label_value'>{v}</td>
            </tr>"""
    return text.format(tbody=tbody)


def _get_dashboard() -> str:
    text = """
                <table class="list" style="width: 1100px; max-width: 1100px; height: 100%">
                    <caption>Global counters</caption>
                    <thead>
                    <tr>
                        <th>PASSED</th>
                        <th>SKIPPED</th>
                        <th>FAILED</th>
                        <th>FAILED_BUG</th>
                        <th>TOTAL</th>
                        <th>Success</th>
                        <th>Duration</th>
                    </tr>
                    </thead>
                    <tbody>
                    <tr>
                        <td class="passed"  style="text-align: center; font-size: 17px; font-weight: bold;"><span id="total_passed">0</span></td>
                        <td class="skipped" style="text-align: center; font-size: 17px; font-weight: bold;"><span id="total_skipped">0</span></td>
                        <td class="failed"  style="text-align: center; font-size: 17px; font-weight: bold;"><span id="total_failed">0</span></td>
                        <td class="failed_bug"  style="text-align: center; font-size: 17px; font-weight: bold;"><span id="total_failed_bug">0</span></td>
                        <td class="label_value" style="text-align: center; font-size: 17px; font-weight: bold;"><span id="total">0</span></td>
                        <td class="label" style="text-align: center; font-size: 17px; font-weight: bold;"><span id="total_perc">0</span></td>
                        <td class="label" style="text-align: center; font-size: 17px; font-weight: bold;"><span id="total_duration">0</span></td>
                    </tr>
                    </tbody>
                </table>

                <br>

                <div id="summary" style="width: 1100px; max-width: 1100px; height: 100%">
                    <table class="list"style="width: 1100px; max-width: 1100px; height: 100%">
                        <caption>Package/Suite summary</caption>
                        <thead>
                        <tr>
                            <th colspan=2>Package/Suite</th>
                            <th>PASSED</th>
                            <th>SKIPPED</th>
                            <th>FAILED</th>
                            <th>FAILED_BUG</th>
                            <th>TOTAL</th>
                            <th>Success</th>
                            <th>Duration</th>
                        </tr>
                        </thead>
                        <tbody>
                        </tbody>
                    </table>
                </div>
    """
    return text


def _add_selected_tests(selected_tests: List[PackageAttr]) -> str:
    text = """
        <table id="rm_selected_tests" class="list" style="width: 100%; max-width: 2820px;">
            <caption>Selected Tests</caption>
            <thead>
            <tr>
                <th>meid</th>
                <th>Package</th>
                <th>Sp</th>
                <th>Suite</th>
                <th>Tp</th>
                <th>Test</th>
                <th>Level</th>
                <th>TAGs</th>
                <th>Features</th>
                <th>Number</th>
                <th>Test description</th>
            </tr>
            </thead>
            <tbody>
            {tbody}
            </tbody>
        </table>
    """
    tbody = ""
    for pat in selected_tests:
        for sat in pat.suite_attr_list:
            for tma in sat.test_method_attr_list:
                tbody += f"""
            <tr>
                <td class='method_ended'>{tma.method_id}</td>
                <td class='method_ended'>{pat.package_name}</td>
                <td class='method_ended'>{sat.prio}</td>
                <td class='method_ended'>{sat.suite_name}</td>
                <td class='method_ended'>{tma.prio}</td>
                <td class='method_ended'>{tma.name}</td>
                <td class='method_ended'>{tma.level}</td>
                <td class='method_ended'>{' '.join(tma.tags)}</td>
                <td class='method_ended'>{tma.features}</td>
                <td class='method_ended'>{tma.test_number}</td>
                <td class='method_ended'>{tma.comment}</td>
            </tr>"""
    return text.format(tbody=tbody)


def escaped_text(text):
    return html.escape(str(text)).replace("\n", "<br>").replace(" ", "&nbsp;")


def get_image_from_attachment(attachment: Dict) -> str:
    if isinstance(attachment, dict) and attachment.get("mime", "").startswith("image/"):
        img_b64 = base64.b64encode(attachment["data"]).decode("utf-8")
        return f"<div> <p>{attachment['name']}</p> <img src='data:{attachment['mime']};base64,{img_b64}'/> </div>"
    return ""


def _format_info(current_test: TestDetails, ending_state: str, end_reason: str):
    test_attr = {
        "package": current_test.suite.package.get_name(),
        "suite": current_test.suite.get_name(),
        "suite filename": current_test.suite.suite_attr.filename,
        "test_id": current_test.get_test_id(),
    }
    test_attr.update(current_test.get_attr())

    str_res = "<h2>Test Attributes:</h2>"
    str_res += f"<p>{escaped_text(prettify(test_attr, as_yaml=True))}</p><HR>"
    str_res += f"{escaped_text(current_test.get_full_name(with_cycle_number=True))}<br>"
    str_res += escaped_text("    Status: ") + f"<strong>{ending_state}</strong><br>"
    str_res += escaped_text("End reason: ") + f"{end_reason}<br>"
    str_res += escaped_text("   Started: ") + f"{current_test.get_counters().get_begin_time()}<br>"
    str_res += escaped_text("     Ended: ") + f"{current_test.get_counters().get_end_time()}<br>"
    str_res += escaped_text("      Took: ") + f"{format_duration(current_test.get_duration())}"

    # add test info log
    for ts, current_time, level, info, attachment in current_test.get_info():
        data = f"<p>{escaped_text(info)}</p>{get_image_from_attachment(attachment)}"
        str_res += f"<hr><strong>{current_time} {level}</strong><br>{data}"

    # add test steps
    tc = current_test.get_test_step_counters()
    if len(tc.get_timed_laps()) > 0:
        str_res += "<hr>" + escaped_text(current_test.get_test_step_counters_tabulate()).replace("\n", "<br>")
    else:
        str_res += "<hr>Test Summary: " + escaped_text(str(current_test.get_counters().summary(verbose=False)))

    return str_res


def _get_div_summary(rm: ReportManager) -> str:
    text = """
    <table class='list' style='width: 1100px; max-width: 1100px; height: 100%'>
        <caption>Package/Suite summary</caption>
        <thead>
        <tr>
            <th colspan=2>Package/Suite</th>
            <th>PASSED</th>
            <th>SKIPPED</th>
            <th>FAILED</th>
            <th>FAILED_BUG</th>
            <th>TOTAL</th>
            <th>Success</th>
            <th>Duration</th>
        </tr>
        </thead>
        <tbody>"""

    results = []

    def _create_row(_obj: str = "Package", _class="label"):
        total_passed = (row[enums_data.STATE_PASSED], STATUS_TO_CLASS[enums_data.STATE_PASSED])
        total_failed = (row[enums_data.STATE_FAILED], STATUS_TO_CLASS[enums_data.STATE_FAILED])
        total_failed_bug = (row[enums_data.STATE_FAILED_KNOWN_BUG], STATUS_TO_CLASS[enums_data.STATE_FAILED_KNOWN_BUG])
        total_skipped = (row[enums_data.STATE_SKIPPED], STATUS_TO_CLASS[enums_data.STATE_SKIPPED])
        total = (total_passed[0] + total_failed[0] + total_failed_bug[0] + total_skipped[0], "label_value")
        total_perc = (f"{total_passed[0] / total[0] if total[0] else 0:.2%}", "label")
        duration = (format_duration(row["Duration"]), "label")

        name = (row[_obj], _class)

        data = [_obj, name, total_passed, total_skipped, total_failed, total_failed_bug, total, total_perc, duration]
        results.append(data)

    df = rm.get_df()
    df_packages: pd.DataFrame = dfm.get_state_dummies(df, columns=["Package"])
    for index, row in df_packages.iterrows():
        _create_row("Package", "label")

        df_pkg = df[df["Package"] == row["Package"]]
        df_suites: pd.DataFrame = dfm.get_state_dummies(df_pkg, columns=["Package", "Suite"])
        for index, row in df_suites.iterrows():
            _create_row("Suite", "label_value")

    for row in results:
        if row[0] == "Package":
            _style = "text-align: center; font-size: 17px; font-weight: bold;"
            cells = "<td colspan=2 "
        else:
            _style = "text-align: center; font-size: 15px;"
            cells = "<td></td><td "

        cells += f"class='{row[1][1]}'>{row[1][0]}</td> "
        cells += " ".join([
            f"<td class='{_class}' style='{_style}'>{_value}</td>"
            for _value, _class in row[2:]
        ])
        _class = "collapse" if row[0] == "Suite" else "visible"
        text += f"<tr class='{row[0]} {_class}'>{cells}</tr>"

    text += "</tbody></table>"

    return text.replace("\n", " ")


HTML_HEADER = """<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>{title}</title>
        <style>
{css}
        </style>
        <script>
{js_expand_test_log}
        </script>
    </head>

    <body>
        <table class="no_spacing" style="width: 100%; max-width: 2820px;">
        <tbody>
            <tr>
            <td class="no_spacing">
            {rm_params}
            </td><td class="no_spacing">
            {dashboard}
            </td>
            </tr>
        </tbody>
        </table>
        <br>
        {selected_tests}
        <br>
        <div style="width: 100%; max-width: 2820px; overflow: auto;">
            <table id="ended_tests" class="list" style="width: 100%; height: 100%">
                <caption>Ended tests</caption>
                <thead>
                <tr>
                    <th>meid</th>
                    <th>Package</th>
                    <th>Suite</th>
                    <th>Test</th>
                    <th>tid</th>
                    <th>Usecase</th>
                    <th>Status</th>
                    <th>Duration</th>
                    <th>End reason</th>
                </tr>
                </thead>
                <tbody>"""


HTML_FOOTER = """
                </tbody>
            </table>
        </div>

        <script>
        {tear_down_js}
        </script>

    </body>
</html>
"""


_js_expand_test_log = """
    document.addEventListener('DOMContentLoaded', function() {
        const table = document.getElementById('ended_tests');
        const rows = table.querySelectorAll('tbody tr');

        // Add click handler to data rows (every other row)
        for(let i = 0; i < rows.length; i += 2) {
            const dataRow = rows[i];
            const logRow = rows[i + 1];

            // Add visual indicator that row is clickable
            dataRow.style.cursor = 'pointer';

            // Add click handler
            dataRow.addEventListener('click', function() {
                // Toggle the visibility of the log row
                if(logRow.classList.contains('collapse')) {
                    logRow.classList.remove('collapse');
                    logRow.classList.add('visible');
                } else {
                    logRow.classList.remove('visible');
                    logRow.classList.add('collapse');
                }

                // Optional: collapse all other rows
                //for(let j = 1; j < rows.length; j += 2) {
                //    if(j !== i + 1) {  // Skip the row we just toggled
                //        rows[j].classList.remove('visible');
                //        rows[j].classList.add('collapse');
                //    }
                //}
            });
        }

    });


    function expand_summary() {
        // Get all Package rows
        const packageRows = document.querySelectorAll('tr.Package');

        // Add click handler to each Package row
        packageRows.forEach(packageRow => {
            packageRow.style.cursor = 'pointer';

            packageRow.addEventListener('click', function() {
                let currentRow = this.nextElementSibling;
                let isCollapsed = false;

                // Check if the next Suite row is collapsed
                if (currentRow && currentRow.classList.contains('Suite')) {
                    isCollapsed = currentRow.classList.contains('collapse');
                }

                // Toggle all consecutive Suite rows
                while (currentRow && currentRow.classList.contains('Suite')) {
                    if (isCollapsed) {
                        currentRow.classList.remove('collapse');
                    } else {
                        currentRow.classList.add('collapse');
                    }
                    currentRow = currentRow.nextElementSibling;
                }
            });

        });
    }

"""
