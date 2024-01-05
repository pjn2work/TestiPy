import traceback

from typing import Dict, List
from tabulate import tabulate


def get_traceback_str(exc_value: BaseException, full: bool = False) -> str:
    tb_list = traceback.format_tb(exc_value.__traceback__)

    if full:
        return "".join(tb_list)[:-1]

    if len(tb_list) == 1:
        return tb_list[0].strip()

    two_lines = tb_list[-1].splitlines(False)
    return f"{two_lines[0].strip()} [{two_lines[1].strip()}]"


def get_traceback_tabulate(exc_value: BaseException) -> str:
    result = ""
    for error in get_traceback_list(exc_value):
        if result:
            result += f"{'='*200}\n"

        data = [(row["filename"], row["method"], row["lineno"], row["code"]) for row in error["error_lines"]]

        result += f"{error['type']}: {error['message']}\n"
        result += tabulate(data, headers=("Filename", "Method", "Line", "Code"), tablefmt="simple") + "\n"

    return result


def get_traceback_list(exc_value: BaseException) -> List[Dict]:
    result = []

    # get previous fails, so errors are appended by order of execution
    if exc_value.__context__:
        result += get_traceback_list(exc_value.__context__)

    # convert Exception into TracebackException
    tbe = traceback.TracebackException.from_exception(exc_value)

    # get stacktrace (cascade methods calls)
    error_lines = [{
            "filename": frame_summary.filename,
            "method"  : frame_summary.name,
            "lineno"  : frame_summary.lineno,
            "code"    : frame_summary.line
        } for frame_summary in tbe.stack]

    # append error, by order of execution
    result.append({
        "error_lines": error_lines,
        "type"       : tbe.exc_type.__name__,
        "message"    : str(tbe)
    })

    return result
