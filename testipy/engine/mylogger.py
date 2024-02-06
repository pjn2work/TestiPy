import logging
from typing import Union, Dict
from datetime import datetime


class MyScreenFormatter(logging.Formatter):
    def __init__(self, *, fmt_keys: Union[Dict[str, str], None] = None):
        super().__init__()
        self.fmt_keys = fmt_keys if fmt_keys is not None else {}

    def format(self, record: logging.LogRecord) -> str:
        ts = str(datetime.fromtimestamp(record.created))
        message = record.getMessage().split("\n")[0]
        message = f"{ts} {record.levelname} {message}"
        return message


class MyFileFormatter(logging.Formatter):
    def __init__(self, *, fmt_keys: Union[Dict[str, str], None] = None):
        super().__init__()
        self.fmt_keys = fmt_keys if fmt_keys is not None else {}

    def format(self, record: logging.LogRecord) -> str:
        ts = str(datetime.fromtimestamp(record.created))
        message = f"{ts} {record.levelname} [{record.module}.{record.funcName}@{record.threadName}] {record.getMessage()}"
        return message
