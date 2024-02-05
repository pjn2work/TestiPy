import logging
from datetime import datetime


class MyScreenFormatter(logging.Formatter):
    def __init__(self, *, fmt_keys: dict[str, str] | None = None):
        super().__init__()
        self.fmt_keys = fmt_keys if fmt_keys is not None else {}

    def format(self, record: logging.LogRecord) -> str:
        ts = str(datetime.fromtimestamp(record.created))
        message = f"{ts} {record.levelname} {record.getMessage().split("\n")[0]}"
        return message


class MyFileFormatter(logging.Formatter):
    def __init__(self, *, fmt_keys: dict[str, str] | None = None):
        super().__init__()
        self.fmt_keys = fmt_keys if fmt_keys is not None else {}

    def format(self, record: logging.LogRecord) -> str:
        ts = str(datetime.fromtimestamp(record.created))
        message = f"{ts} {record.levelname} [{record.module}.{record.funcName}@{record.threadName}] {record.getMessage()}"
        return message
