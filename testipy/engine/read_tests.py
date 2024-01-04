#!/usr/bin/env python3

import inspect
import os

from typing import Union, List, Tuple, Dict, Any

from testipy.configs import enums_data, default_config
from testipy.lib_modules import py_inspector, common_methods as cm


AUTO_INCLUDED_TESTS = 0
TYPE_DOC = Dict[str, Any]
TYPE_SELECTED_TESTS_LIST = List[Dict]


# returns dict of doc from class or method
def get_doc_dict(obj, name="") -> TYPE_DOC:
    doc_dict = dict()
    doc_dict[enums_data.TAG_NAME] = name
    doc_dict[enums_data.TAG_TAG] = set()
    doc_dict[enums_data.TAG_LEVEL] = 1 if default_config.execute_test_with_no_doc else 0
    doc_dict[enums_data.TAG_PRIO] = 0
    doc_dict[enums_data.TAG_FEATURES] = ""
    doc_dict[enums_data.TAG_TESTNUMBER] = ""
    doc_dict[enums_data.TAG_DEPENDS] = set()
    doc_dict[enums_data.TAG_ON_SUCCESS] = set()
    doc_dict[enums_data.TAG_ON_FAILURE] = set()

    doc = py_inspector.get_doc(obj)
    if doc:
        for line in doc.split("\n"):
            if line.startswith("@"):
                first_space = line.index(" ")
                tag_name = line.upper()[:first_space] if first_space > 0 else line.strip().upper()

                if tag_name in [enums_data.TAG_PRIO, enums_data.TAG_LEVEL]:
                    doc_dict[tag_name] = int(line[len(tag_name)+1:].strip())
                    continue

                if tag_name == enums_data.TAG_TAG:
                    for current_tag in line[len(tag_name)+1:].strip().upper().split():
                        doc_dict[tag_name].add(current_tag)
                    continue

                if tag_name in [enums_data.TAG_DEPENDS, enums_data.TAG_ON_SUCCESS, enums_data.TAG_ON_FAILURE]:
                    for current_tag in line[len(tag_name)+1:].strip().split():
                        doc_dict[tag_name].add(int(current_tag))
                        doc_dict[enums_data.TAG_DEPENDS].add(int(current_tag))
                    continue

                doc_dict[tag_name] = line[first_space+1:].strip()

    return doc_dict


# auto include tests with tags on default_config.py
def is_auto_include_test_tag(doc: TYPE_DOC) -> bool:
    global AUTO_INCLUDED_TESTS

    doc["auto_included"] = False
    if doc[enums_data.TAG_LEVEL] > 0:
        for tag in default_config.auto_include_tests_with_tags:
            if tag in doc[enums_data.TAG_TAG]:
                AUTO_INCLUDED_TESTS += 1
                doc["auto_included"] = True
                return True
    return False


# returns bool, if name_prefix=(test or suite) has valid tags
def is_valid_tag(name: str, name_prefix: str, doc: TYPE_DOC, include_tags: List[str], exclude_tags: List[str]) -> bool:
    tag_list = set(doc[enums_data.TAG_TAG])
    tag_list.add(name)                     # python def method name
    tag_list.add(name[len(name_prefix):])  # python def method name without the name_prefix
    tag_list.add(doc[enums_data.TAG_NAME])  # DOC tag @NAME

    return name.startswith(name_prefix) and (doc[enums_data.TAG_LEVEL] > 0) and (
            (not include_tags and not exclude_tags) or
            (not exclude_tags and cm.intersection(tag_list, include_tags)) or
            (not include_tags and not cm.intersection(tag_list, exclude_tags)) or
            (cm.intersection(tag_list, include_tags)) and not cm.intersection(tag_list, exclude_tags))


# returns bool, if @FEATURES has valid tags
def is_valid_tag_features(doc: TYPE_DOC, include_tags: List = [], exclude_tags: List = []) -> bool:
    tag_list = doc[enums_data.TAG_FEATURES].split(" ")
    tag_list = [] if tag_list == [""] else tag_list

    return ((not include_tags and not exclude_tags) or
            (not exclude_tags and cm.intersection(tag_list, include_tags)) or
            (not include_tags and not cm.intersection(tag_list, exclude_tags)) or
            (cm.intersection(tag_list, include_tags)) and not cm.intersection(tag_list, exclude_tags))


# returns bool, if @TN has valid tags
def is_valid_tag_testnumber(doc: TYPE_DOC, include_tags: List = [], exclude_tags: List = []) -> bool:
    tag_list = doc[enums_data.TAG_TESTNUMBER].split(" ")
    tag_list = [] if tag_list == [""] else tag_list

    if tag_list:
        for exc_tag in exclude_tags:
            for tag in tag_list:
                if tag.startswith(exc_tag):
                    return False

        if include_tags:
            for inc_tag in include_tags:
                for tag in tag_list:
                    if tag.startswith(inc_tag):
                        return True
            return False
    elif include_tags:
        return False

    return True


# returns bool, if the test level is inside limits of selection
def is_valid_level(doc: TYPE_DOC, level_filter: Tuple[List, List, List, List] = ([], [], [], [])) -> bool:
    include_level = level_filter[0]
    exclude_level = level_filter[1]
    above_level = level_filter[2]
    below_level = level_filter[3]

    # get test level
    test_level = doc[enums_data.TAG_LEVEL]

    # no filter, then all included
    if not (include_level or exclude_level or above_level or below_level):
        return True

    # cherry-pick level
    if str(test_level) in exclude_level:
        return False
    if str(test_level) in include_level:
        return True

    # group select
    if above_level:
        if below_level:
            return int(above_level[-1]) <= test_level <= int(below_level[-1])
        return test_level >= int(above_level[-1])
    if below_level:
        return test_level <= int(below_level[-1])

    return len(include_level) == 0


# show test list
def show_test_structure(execution_log, test_list: TYPE_SELECTED_TESTS_LIST):
    str_res = ""
    for package in test_list:
        str_res += "\npackage_name {} | {} suites\n".format(package["package_name"], len(package["suite_list"]))

        for suite in package["suite_list"]:
            str_res += "   {}\n".format(cm.dict_without_keys(suite, ("test_list", "suite_obj", "suite_comment", enums_data.TAG_LEVEL)))  # len(suite["test_list"]),

            for test in suite["test_list"]:
                str_res += "      {}\n".format(cm.dict_without_keys(test, ("test_obj", "test_comment")))

    execution_log("INFO", "TestStructure:" + str_res[:-1])


def sort_test_structure(test_list: TYPE_SELECTED_TESTS_LIST) -> TYPE_SELECTED_TESTS_LIST:
    method_id = 0
    for package in test_list:
        package["suite_list"] = sorted(package["suite_list"], key=lambda x: x[enums_data.TAG_PRIO], reverse=True)

        for suite in package["suite_list"]:
            suite["test_list"] = sorted(suite["test_list"], key=lambda x: x[enums_data.TAG_PRIO], reverse=True)

            for test in suite["test_list"]:
                method_id += 1
                test["method_id"] = method_id

    return test_list


def mark_meid(test_list: TYPE_SELECTED_TESTS_LIST) -> TYPE_SELECTED_TESTS_LIST:
    method_id = 0
    for package in test_list:
        for suite in package["suite_list"]:
            for test in suite["test_list"]:
                method_id += 1
                test["method_id"] = method_id

    return test_list


# returns list of dict with all tests to run
def get_tests(execution_log,
              full_path_tests_scripts_foldername: str,
              include_package=[], exclude_package=[],
              include_suite_tag=[], exclude_suite_tag=[],
              include_test_tag=[], exclude_test_tag=[],
              level_filter=([],[],[],[]),
              include_feature=[], exclude_feature=[],
              include_testnumber=[], exclude_testnumber=[]) -> TYPE_SELECTED_TESTS_LIST:
    """
    list structure, example:
    [
      {package_name="qa/regression/v1", suite_list=[
            {filename="abcdef.py", suite_name="suite_Rest_Api", suite_obj=@class, @TAGs=..., test_list=[ ... ]},
            {filename="abcdef.py", suite_name="suite_draft_Api", suite_obj=@class, @TAGs=..., test_list=[ ... ]},
      , {package_name="...", suite_list=[ --- ]}
    ]

    test_list = [
        {method_name="test01_rest_api",
         method_id=1,
         test_obj=<function suite02.testUnder at 0x7efc4a49c730>,
         @NAME="Test Name", @TAG={tag1, tag2}, @LEVEL=3, @PRIO=999,
         test_comment="# This is the function comment"}
    , { --- }
    ]
    """

    def is_valid_package(package_name: str) -> bool:
        return not package_name.startswith(".") and not package_name.endswith("__pycache__") and (
                (not include_package and not exclude_package) or
                (not include_package and not cm.validate_begins_with(package_name, exclude_package)) or
                (not exclude_package and cm.validate_begins_with(package_name, include_package)) or
                (cm.validate_begins_with(package_name, include_package) and not cm.validate_begins_with(package_name, exclude_package)))

    def is_valid_suite(obj, doc: TYPE_DOC, suite_name: str) -> bool:
        return inspect.isclass(obj) and is_valid_tag(suite_name, default_config.prefix_suite, doc, include_suite_tag, exclude_suite_tag)

    def is_valid_test(obj, doc: TYPE_DOC, method_name: str) -> bool:
        return inspect.isfunction(obj) and is_valid_level(doc, level_filter) and (is_auto_include_test_tag(doc) or (
                is_valid_tag(method_name, default_config.prefix_tests, doc, include_test_tag, exclude_test_tag) and
                is_valid_tag_features(doc, include_feature, exclude_feature) and
                is_valid_tag_testnumber(doc, include_testnumber, exclude_testnumber))
        )

    # returns sorted list of dict
    def get_test_list_from_suite_obj(suite_obj, suite_doc) -> List[Dict]:
        test_list = []
        _test_methods = dict()

        depends_prio_tests_to_auto_include = set()
        global AUTO_INCLUDED_TESTS
        AUTO_INCLUDED_TESTS = 0

        def is_test_on_list(test) -> bool:
            for t in test_list:
                if t["method_name"] == test["method_name"]:
                    return True
            return False

        # find tests (methods) under the same suite (class)
        for method_name, obj in inspect.getmembers(suite_obj):
            mname = method_name[len(default_config.prefix_tests):] if default_config.trim_prefix_tests else method_name
            doc = get_doc_dict(obj, mname)
            doc["@TN"] = suite_doc["@TN"] + doc["@TN"]

            # create new test and add to test_methods
            current_method = dict(method_name=method_name,
                                  test_obj=obj,
                                  test_comment=py_inspector.get_comment(obj) or "",
                                  ncycles=py_inspector.get_method_parameter_default_value(obj, "ncycles", 1),
                                  param=py_inspector.get_method_parameter_default_value(obj, "param", None))
            current_method.update(doc)
            _test_methods[method_name] = current_method

            # add to selected tests and add dependency to other tests
            if is_valid_test(obj, current_method, method_name):
                test_list.append(current_method)

                # update auto include tests that have dependency to other tests, based on prio
                depends_prio_tests_to_auto_include.update(doc[enums_data.TAG_DEPENDS])

        # find tests (methods) that must be included because of dependency
        changes_were_made = len(depends_prio_tests_to_auto_include) > 0
        while changes_were_made:
            changes_were_made = False
            for method_name, test in _test_methods.items():
                if test[enums_data.TAG_PRIO] in depends_prio_tests_to_auto_include:
                    if not is_test_on_list(test):
                        test_list.append(test)
                        depends_prio_tests_to_auto_include.update(test[enums_data.TAG_DEPENDS])

                        AUTO_INCLUDED_TESTS += 1
                        changes_were_made = True

        # order test list
        if test_list:
            if len(test_list) > AUTO_INCLUDED_TESTS:
                test_list = sorted(test_list, key=lambda x: x[enums_data.TAG_PRIO], reverse=True)
            else:
                test_list = []

        return test_list

    # returns suites (with test_list)
    def get_suites_list_from_file_with_tests(fpn: str, filename: str) -> List[Dict]:
        suite_list = []

        for suite_name, obj in py_inspector.get_members_from_file(fpn):
            sname = suite_name[len(default_config.prefix_suite):] if default_config.trim_prefix_suite else suite_name
            doc = get_doc_dict(obj, sname)
            if is_valid_suite(obj, doc, suite_name):
                test_list = get_test_list_from_suite_obj(obj, doc)
                if test_list:
                    current_suite = dict(filename=filename,
                                         suite_name=suite_name,
                                         suite_obj=obj,
                                         suite_comment=py_inspector.get_comment(obj),
                                         test_list=test_list)

                    current_suite.update(doc)
                    suite_list.append(current_suite)

        return suite_list

    # returns list with dict of files/suites/tests, sorted by suites/tests
    def get_package_suite_test_list(full_path_foldername: str, package_name: str = "") -> List[Dict]:
        result_list = []

        # passed package filters
        vp = is_valid_package(package_name)

        # new package
        if vp:
            package_dict = dict(package_name=package_name, suite_list=[])
            # add current package to PATH
            #sys.path.insert(1, full_path_foldername)

        # search in all files and sub-folders
        for filename in sorted(os.listdir(full_path_foldername)):
            fpn = os.path.join(full_path_foldername, filename)

            # check for sub-packages
            if os.path.isdir(fpn):
                result_list += get_package_suite_test_list(fpn, package_name + default_config.separator_package + filename)

            # check for suites
            elif vp and os.path.isfile(fpn) and filename.endswith(".py"):
                suite_list = get_suites_list_from_file_with_tests(fpn, filename)
                if suite_list:
                    package_dict["suite_list"] += suite_list

        # add all suites under this package (store them ordered)
        if vp and package_dict["suite_list"]:
            package_dict["suite_list"] = sorted(package_dict["suite_list"], key=lambda x: x[enums_data.TAG_PRIO], reverse=True)
            result_list.append(package_dict)

        return result_list

    #  -  -  -  -  -  -  -  -  main function starts here  -  -  -  -  -  -  -  -  #
    if not os.path.isdir(full_path_tests_scripts_foldername):
        raise NotADirectoryError(full_path_tests_scripts_foldername)

    # final list with all tests (already filtered by include/exclude)
    result_list = []

    # all folders under tests
    for name in sorted(os.listdir(full_path_tests_scripts_foldername)):
        fpn = os.path.join(full_path_tests_scripts_foldername, name)
        if os.path.isdir(fpn):
            test_list = get_package_suite_test_list(fpn, name)
            if test_list:
                result_list += test_list

    result_list = mark_meid(sort_test_structure(result_list))

    return result_list


# get value from a list of dict
def get_dict_by_value(value_obj, my_list_of_dict: List[Dict], key_name, execution_log, make_copy: bool = False) -> Union[Dict, None]:
    if not isinstance(key_name, (list, tuple, set)):
        key_name = [key_name]

    for current_dict in my_list_of_dict:
        for k in key_name:
            if current_dict.get(k, "") == value_obj:
                if make_copy:
                    return current_dict.copy()
                return current_dict

    if make_copy:
        execution_log("WARNING", f"{key_name}={value_obj} excluded, because not found in list of {len(my_list_of_dict)} objects!")
    return None


def filter_tests_by_storyboard(execution_log, storyboard_json_files: List[str], all_tests: TYPE_SELECTED_TESTS_LIST) -> TYPE_SELECTED_TESTS_LIST:
    selected_tests = []

    for sb_json_file in storyboard_json_files:
        storyboard = cm.load_config(sb_json_file)

        for sb_package in storyboard["package_list"]:
            # get cloned package dict, based on package_of_storyboard, from all tests
            current_package = get_dict_by_value(sb_package["package_name"], all_tests, "package_name", execution_log, make_copy=True)

            if current_package:
                suite_list = list()

                # add all suites from package if none specified on storyboard
                if not sb_package.get("suite_list"):
                    sb_package["suite_list"] = [{"suite_name": suite["suite_name"]} for suite in current_package["suite_list"]]

                for sb_suite in sb_package["suite_list"]:
                    # get cloned suite dict, based on suite_of_storyboard, from all_tests->current_package
                    current_suite = get_dict_by_value(sb_suite["suite_name"], current_package["suite_list"], ["suite_name", enums_data.TAG_NAME], execution_log, make_copy=True)
                    if current_suite:
                        test_list = list()

                        # add storyboard suite attributes, override values such as ncycle
                        for k, v in sb_suite.items():
                            if k in ["ncycles"]:
                                current_suite[k] = v

                        # add all tests from suite if none specified on storyboard
                        if not sb_suite.get("test_list"):
                            sb_suite["test_list"] = [{"test_name": test["method_name"]} for test in current_suite["test_list"]]

                        # filter tests based on storyboard
                        for sb_test in sb_suite["test_list"]:
                            current_test = get_dict_by_value(sb_test["test_name"], current_suite["test_list"], ["method_name", enums_data.TAG_NAME], execution_log, make_copy=True)
                            if current_test:
                                # add storyboard test attributes, override values such as ncycle and param
                                for k, v in sb_test.items():
                                    if k in ["ncycles", "param"]:
                                        current_test[k] = v

                                test_list.append(current_test)

                        # add to selected_tests
                        if test_list:
                            # add suite kwargs for suite __init__()
                            current_suite["suite_kwargs"] = {k: v for k, v in sb_suite.items() if k not in ["suite_name", "test_list", "ncycles"]}

                            # update lists
                            current_suite["test_list"] = test_list
                            suite_list.append(current_suite)

                if suite_list:
                    # add storyboard package attributes, override values such as ncycle
                    for k, v in sb_package.items():
                        if k in ["ncycles"]:
                            current_package[k] = v

                    current_package["suite_list"] = suite_list
                    selected_tests.append(current_package)

    selected_tests = mark_meid(selected_tests)

    return selected_tests


def run(execution_log, ap, storyboard_json_files, full_path_tests_scripts_foldername, verbose=True):
    cm.TESTS_ROOT_FOLDER = full_path_tests_scripts_foldername
    all_tests = get_tests(execution_log,
                          full_path_tests_scripts_foldername=full_path_tests_scripts_foldername,
                          include_package=ap.get_options_arguments("-ip"), exclude_package=ap.get_options_arguments("-ep"),
                          include_suite_tag=ap.get_options_arguments("-is"), exclude_suite_tag=ap.get_options_arguments("-es"),
                          include_test_tag=ap.get_options_arguments("-it"), exclude_test_tag=ap.get_options_arguments("-et"),
                          level_filter=(ap.get_options_arguments("-ilv"), ap.get_options_arguments("-elv"), ap.get_options_arguments("-alv"), ap.get_options_arguments("-blv")),
                          include_feature=ap.get_options_arguments("-if"), exclude_feature=ap.get_options_arguments("-ef"),
                          include_testnumber=ap.get_options_arguments("-itn"), exclude_testnumber=ap.get_options_arguments("-etn"))

    if storyboard_json_files:
        all_tests = filter_tests_by_storyboard(execution_log, storyboard_json_files, all_tests)

    # TODO remove this comments for debugging purpose
    if verbose and all_tests:
        show_test_structure(execution_log, all_tests)

    return all_tests

