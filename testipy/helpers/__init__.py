import os
import sys
import subprocess
import json
import yaml

from typing import Union, Dict, Tuple

from testipy.helpers.errors import get_traceback_str, get_traceback_tabulate, get_traceback_list
from testipy.helpers.timer import Timer
from testipy.helpers.prettify import prettify, format_duration


# define custom tag handler for string concatenation
def yaml_join(loader, node):
    seq = loader.construct_sequence(node)
    return "".join([str(s) for s in seq])


# register the tag handler for string concatenation
yaml.add_constructor("!join", yaml_join)


# returns full path filename, based on other file path
def create_filename_fullpath(fpn: str, same_path_as_file=None) -> str:
    if os.path.isfile(fpn):
        fpn = os.path.abspath(fpn)
    else:
        fpn = os.path.split(fpn)[-1]
        fpn = os.path.join(os.path.dirname(os.path.abspath(same_path_as_file)), fpn) if same_path_as_file else os.path.join(os.getcwd(), fpn)
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


def left_update_dict(d1: Dict, d2: Dict) -> Dict:
    # keep everything from d1 root
    res = d1.copy()

    # check for all items in d2 if they are new or to be replaced in d1
    for k, v in d2.items():
        if k in res and isinstance(v, dict):
            res[k] = left_update_dict(d1[k], v)
            continue
        res[k] = v

    return res


def exec_cmd(cmd: str, timeout: int = 2, change_to_path: str = "") -> Tuple[int, str, str]:
    """ returns (int, str, str), with (exitcode, stdout, stderr) """
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
