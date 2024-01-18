#!/usr/bin/env python3
from __future__ import annotations

import os
import threading
import functools

from datetime import datetime
from time import time
from typing import Tuple, Dict, List, Iterable

from testipy import __app__, __version__, __app_full__
from testipy.configs import default_config


TESTS_ROOT_FOLDER = os.getcwd()


def get_app_version() -> Tuple[str, str, str]:
    return __app__, __version__, __app_full__


def get_current_date_time_ns() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")


def get_current_date_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_current_short_date() -> str:
    return datetime.now().strftime("%Y%m%d")


def get_current_short_time() -> str:
    return datetime.now().strftime("%H%M%S")


def get_timestamp() -> int:
    return int(time() * 1000)


def get_datetime_now() -> datetime:
    return datetime.now()


# returns bool True if any string in tag_list begins with text
def validate_begins_with(text: str = "", tag_list: Iterable = None) -> bool:
    if not text and not tag_list:
        return True

    for tag in tag_list:
        if text.startswith(tag):
            return True
    return False


# returns list with elements in common in both lists. lst2 can have multiple elements joined with & to make an AND
def intersection(lst1: Iterable, lst2: Iterable) -> List:
    result = list()
    for elem in lst2:
        aux = []
        for elm in elem.split(default_config.separator_and_join_tags):
            if elm not in lst1:
                break
            aux.append(elm)
        else:
            result += aux
    return result
    # return [v for v in lst1 if v in lst2]


# returns dict cloned from dic without key element, key = [str, list, tuple, set]
def dict_without_keys(_dict: Dict, keys_to_remove) -> Dict:
    if not isinstance(keys_to_remove, (list, tuple, set)):
        keys_to_remove = [keys_to_remove]
    return {k: v for k, v in _dict.items() if k not in keys_to_remove}


def synchronized(wrapped):
    lock = threading.Lock()

    @functools.wraps(wrapped)
    def _wrap(*args, **kwargs):
        #print(f"Locking {wrapped.__name__} with Lock {id(lock)}")
        with lock:
            return wrapped(*args, **kwargs)

    return _wrap
