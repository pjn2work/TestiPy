#!/usr/bin/env python3
from __future__ import annotations

import sys
from typing import Union, List, Tuple, Dict


class ArgsParser:
    """
    Flags       Starts with --, ex: --version
    Options     Starts with -, ex: -name Joe -name Peter
    Arguments   value or values NOT starting with -, ex: *.txt d*s.xml
    """

    def __init__(self, argv_list: Union[List, Tuple]):
        self.__argv_dict: Dict[str, List[str]] = dict()
        self.__args2dict(argv_list)

    # returns ArgsParser of sys.argv
    @classmethod
    def from_sys(cls) -> ArgsParser:
        return ArgsParser(sys.argv[1:])

    # returns ArgsParser from string args
    @classmethod
    def from_str(cls, args) -> ArgsParser:
        if isinstance(args, (list, tuple)):
            return ArgsParser(args)
        if isinstance(args, str):
            return ArgsParser(args.split(" "))
        raise TypeError(f"Unexpected type {type(args)}. Expected: list or tuple or str")

    # creates dict, keys are [flags, options, _arguments_], values are the "options values" or arguments
    def __args2dict(self, argv_list):
        total = len(argv_list)
    
        def insert(key, value):
            if key in self.__argv_dict:
                self.__argv_dict[key].append(value)
            else:
                self.__argv_dict[key] = [value]
    
        i = 0
        while i < total:
            args = argv_list[i]
    
            if args.startswith("--"):
                self.__argv_dict[args] = []
            elif args.startswith("-"):
                i += 1
                insert(args, argv_list[i])
            else:
                insert("_arguments_", args)
    
            i += 1

    # returns dict
    def get_dict(self) -> Dict[str, List[str]]:
        return self.__argv_dict

    # returns dict_keys
    def get_keys(self) -> List[str]:
        return [key for key in self.__argv_dict.keys()]

    # returns list of flags
    def get_flags(self) -> List[str]:
        return [key for key in self.__argv_dict if key.startswith("--")]

    # returns True or False if flag is present
    def has_flag_or_option(self, key: str) -> bool:
        return key in self.__argv_dict

    # returns dict of options
    def get_options(self) -> Dict[str, List[str]]:
        return {key: value for key, value in self.__argv_dict.items() if key.startswith("-") and not key.startswith("--")}

    # returns list with option values
    def get_options_arguments(self, keys, default_value=None) -> List[str]:
        if not isinstance(keys, (list, tuple)):
            keys = [keys]

        result = []
        for k in keys:
            if k in self.__argv_dict:
                result += self.__argv_dict[k]

        if len(result) == 0:
            return default_value or []

        return result

    def get_option(self, key, default_value="") -> str:
        return self.__argv_dict.get(key, [default_value])[-1]

    # returns list of arguments
    def get_arguments(self, default_value=None) -> list:
        return self.__argv_dict.get("_arguments_", default_value or [])

    def __str__(self):
        return str(self.__argv_dict)
