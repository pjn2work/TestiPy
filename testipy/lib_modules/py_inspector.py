#!/usr/bin/env python3

import os
import importlib.util
import inspect

from typing import List, Tuple, Dict, Any


# returns str comment from class or function
def get_comment(obj) -> str:
    comment = inspect.getcomments(obj)
    if comment:
        comment = comment.lstrip("#").replace("\n# ", "\n").replace("\n", "\n").strip()
    return comment


# returns str doc from class or function
def get_doc(obj) -> str:
    """
    If a method or class has this - it will return all this text
    """
    return inspect.getdoc(obj)


# returns module from a .py file
def import_module_from_file(full_path_filename: str):
    filename = os.path.basename(full_path_filename)

    spec = importlib.util.spec_from_file_location(filename[:-3], full_path_filename)
    module_obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module_obj)

    return module_obj


# returns list with all classes, vars, functions, etc...
def get_members_from_file(full_path_filename: str) -> List[Tuple[str, Any]]:
    return inspect.getmembers(import_module_from_file(full_path_filename))


def get_classes_from_file(full_path_filename: str) -> List[Tuple[str, Any]]:
    return [(name, obj) for name, obj in get_members_from_file(full_path_filename) if inspect.isclass(obj)]


# returns the class found (having that prefix) inside the python file
def get_class_from_file_with_prefix(full_path_filename: str, class_prefix: str) -> Tuple[str, Any]:
    for name, obj in get_members_from_file(full_path_filename):
        if inspect.isclass(obj) and name.startswith(class_prefix):
            return name, obj


# returns obj, the default value of a parameter on the method definition
def get_method_parameter_default_value(method_obj, param_name, your_default_value=None):
    try:
        return dict(inspect.signature(method_obj).parameters)[param_name].default
    except:
        return your_default_value


# returns dict with default kwargs of a method
def get_default_kwargs(method) -> Dict:
    if not (inspect.isfunction(method) or inspect.isclass(method)):
        raise TypeError(f"{method} is not a method nor class")

    default_kwargs = dict(inspect.signature(method).parameters)
    default_kwargs = {default_kwargs[k].name: default_kwargs[k].default for k, v in default_kwargs.items() if str(default_kwargs[k].kind) == "POSITIONAL_OR_KEYWORD" and str(k) != str(v)}

    return default_kwargs
