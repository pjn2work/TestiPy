#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import subprocess
import json
import yaml

from time import sleep
from datetime import datetime, timedelta
from time import time
from traceback import TracebackException
from typing import Union, Tuple, Dict, List, Iterable

from testipy import __app__, __version__, __app_full__
from testipy.configs import default_config


TESTS_ROOT_FOLDER = os.getcwd()


def get_app_version() -> Tuple[str, str, str]:
    return __app__, __version__, __app_full__


# returns full path filename, based on other file path
def create_filename_fullpath(fpn: str, same_path_as_file=None) -> str:
    if os.path.isfile(fpn):
        fpn = os.path.abspath(fpn)
    else:
        fpn = os.path.split(fpn)[-1]
        fpn = os.path.join(os.path.dirname(os.path.abspath(same_path_as_file)), fpn) if same_path_as_file else os.path.join(TESTS_ROOT_FOLDER, fpn)
        if not os.path.isfile(fpn):
            raise FileNotFoundError(f"File {fpn} not found.")
    return fpn


def load_config(fpn: str, same_path_as_file=None) -> Union[Dict, str]:
    fpn = create_filename_fullpath(fpn, same_path_as_file)

    if fpn.lower().endswith(".json"):
        return read_json_from_file(fpn)

    if fpn.lower().endswith(".yaml"):
        return read_yaml_from_file(fpn)

    return read_text_from_file(fpn)


# returns dict, from a json file
def read_json_from_file(fpn: str) -> Dict:
    with open(fpn) as json_file:
        data = json.load(json_file)
    return data


# returns dict, from a yaml file
def read_yaml_from_file(fpn: str) -> Dict:
    with open(fpn) as yaml_file:
        data = yaml.full_load(yaml_file)
    return data


# returns text from a text file
def read_text_from_file(fpn: str) -> str:
    with open(fpn, "r") as f:
        text = f.read()
    return str(text).rstrip("\n")


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


def format_duration(seconds: float) -> str:
    if seconds < 1:
        return f"{seconds*1000:.1f}ms"
    if seconds < 60:
        return f"{seconds:.3f}sec"

    secs = seconds % 60
    minutes = int(seconds // 60) % 60
    if seconds < 3600:
        return f"{minutes:02d}:{secs:02.0f}min"

    hours = int(seconds // 3600)
    return f"{hours}:{minutes:02d}:{secs:02.0f}hrs"


def _dict2pstr(data, sp: str = "", indent: int = 3):
    """prettify dicts to string"""
    if isinstance(data, dict):
        if len(data) == 0:
            return "{}"

        res = "{\n"
        for k, v in data.items():
            if isinstance(k, str):
                k = f'"{k}"'
            res += sp + " " * indent + f"{k}: " + _dict2pstr(v, sp=sp + " " * indent, indent=indent) + ",\n"

        return res + sp + "}"
    elif isinstance(data, (list, tuple, set)):
        if len(data) == 0:
            return "[]"

        res = "[\n"
        for v in data:
            res += sp + " " * indent + _dict2pstr(v, sp=sp + " " * indent, indent=indent) + ",\n"

        return res + sp + "]"
    elif isinstance(data, str):
        return f'"{data}"'

    return str(data)


def prettify(json_obj, as_yaml: bool = False, indent: int = 3) -> str:
    """prettify json to string"""
    try:
        if isinstance(json_obj, str):
            json_obj = json.loads(json_obj)
        if isinstance(json_obj, (dict, list, tuple, set)):
            if as_yaml:
                return yaml.dump(json_obj, allow_unicode=True).replace("\\n", "\n")
            return json.dumps(json_obj, indent=indent).replace("\\n", "\n")
    except:
        pass
    return _dict2pstr(json_obj, indent=indent)


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
def dict_without_keys(_dict: Dict, key_to_remove) -> Dict:
    if not isinstance(key_to_remove, (list, tuple, set)):
        key_to_remove = [key_to_remove]
    return {k: v for k, v in _dict.items() if k not in key_to_remove}


# returns (int, str, str), with (exitcode, stdout, stderr)
def exec_cmd(cmd: str, timeout: int = 2, change_to_path: str = "") -> Tuple[int, str, str]:
    try:
        if change_to_path:
            cwd = os.getcwd()
            os.chdir(change_to_path)

        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
        try:
            outs, errs = proc.communicate(timeout=timeout)
            # proc.stdout.flush()
            result = (proc.returncode, str(outs, "utf-8"), str(errs, "utf-8"))
        except subprocess.TimeoutExpired:
            proc.kill()
            outs, errs = proc.communicate()
            # proc.stdout.flush()
            result = (-101, str(outs, "utf-8"), f"{cmd} Timeout after {timeout} seconds")
    except:
        result = (-102, "", sys.exc_info()[1])

    if change_to_path:
        os.chdir(cwd)

    return result


class Timer:

    def __init__(self, seconds: float = 0.0, **kwargs):
        self.timer_end = datetime.now()
        self.set_timer_for(seconds=seconds, **kwargs)

    def set_timer_for(self, seconds: float = 0.0, **kwargs) -> Timer:
        self.timer_end = datetime.now() + timedelta(seconds=seconds, **kwargs)
        return self

    def is_timer_over(self) -> bool:
        return datetime.now() >= self.timer_end

    def is_timer_valid(self) -> bool:
        return datetime.now() < self.timer_end

    def seconds_left(self) -> float:
        sl = (self.timer_end - datetime.now()).total_seconds()
        return max(0, sl)

    def sleep_until_over(self) -> Timer:
        sleep(self.seconds_left())
        return self

    @staticmethod
    def sleep_for(seconds: float):
        if seconds > 0.0:
            sleep(seconds)

    def sleep_for_if_not_over(self, seconds: float, **kwargs) -> Timer:
        if datetime.now() + timedelta(seconds=seconds, **kwargs) > self.timer_end:
            self.sleep_until_over()
        else:
            self.sleep_for(seconds)
        return self


def list_traceback(exc_value: BaseException) -> List[Dict]:
    result = []

    # get previous fails, so errors are appended by order of execution
    if exc_value.__context__:
        result += list_traceback(exc_value.__context__)

    # convert Exception into TracebackException
    tbe = TracebackException.from_exception(exc_value)

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
