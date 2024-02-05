import os
import sys
import logging
import logging.config
import yaml

from testipy import get_exec_logger
from testipy.configs.default_config import execution_log_filename


def setup_logging(log_filename: str) -> logging.Logger:
    with open(os.path.join(os.path.dirname(__file__), "execution_logger_config.yaml")) as f_in:
        config = yaml.full_load(f_in)

        # override execution log filename
        config["handlers"]["file_log"]["filename"] = log_filename
        logging.config.dictConfig(config)

    return get_exec_logger()


class ExecutionLogger:

    def __init__(self, results_folder_runtime: str):
        self._log_file_full_path = os.path.join(results_folder_runtime, execution_log_filename)
        self._create_results_folder(results_folder_runtime)
        self._logger = setup_logging(self._log_file_full_path)

    def _create_results_folder(self, folder_name):
        try:
            os.makedirs(folder_name, exist_ok=True)
            print(f"> Created results folder {folder_name}", file=sys.stdout)
        except Exception as ex:
            print(f"> Could not create results folder {folder_name}, {ex}", file=sys.stderr)

    def log_info(self, message: str):
        self._logger.info(message)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            self._logger.error(str(exc_val), exc_info=True)
        self.close_logger()
        return self

    def close_logger(self):
        for handler in self._logger.handlers:
            try:
                handler.close()
            except Exception as ex:
                print(f"Cannot close {handler} on {self._log_file_full_path}!", str(ex), file=sys.stderr)
