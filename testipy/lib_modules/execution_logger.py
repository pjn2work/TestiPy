import os
import sys
import logging
import traceback

from testipy.configs import default_config
from testipy.lib_modules.common_methods import get_current_date_time


PRINTED_LEVELS = {"CRITICAL", "ERROR", "WARNING", "INFO"}


class ExecutionLogger:

    def __init__(self, results_folder_runtime: str):
        self._log_file_full_path = os.path.join(results_folder_runtime, default_config.execution_log_filename)
        self._create_results_folder(results_folder_runtime)

    def _create_results_folder(self, folder_name):
        try:
            os.makedirs(folder_name, exist_ok=True)
            print(f"> Created results folder {folder_name}", file=sys.stdout)
        except Exception as ex:
            print(f"> Could not create results folder {folder_name}, {ex}", file=sys.stderr)

# Local App Logger
    def execution_log(self, level, info_text):
        if level in PRINTED_LEVELS:
            print(f"> {get_current_date_time()} {level} {info_text}", file=sys.stdout if level in ["INFO"] else sys.stderr)
        self._logger.log(logging.getLevelName(level), info_text)

        if sys.exc_info()[1]:
            tb_list = traceback.format_tb(sys.exc_info()[1].__traceback__)
            tb_list = str(sys.exc_info()[0]) + "\n" + "\n".join(tb_list)
            self._logger.log(logging.getLevelName(level), tb_list)

    def __enter__(self):
        # Configure default execution logging
        _f_handler = logging.FileHandler(self._log_file_full_path, mode="w", encoding="utf-8")
        _f_handler.setFormatter(logging.Formatter(default_config.default_log_format))

        self._logger = logging.getLogger(default_config.execution_log_filename)
        self._logger.addHandler(_f_handler)
        self._logger.setLevel(logging.DEBUG)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            self.execution_log("ERROR", str(exc_val))
        self.close_logger()
        return self

    def close_logger(self):
        for handler in self._logger.handlers:
            try:
                handler.close()
            except Exception as ex:
                print(f"Cannot close {handler} on {default_config.execution_log_filename}!", str(ex), file=sys.stderr)
