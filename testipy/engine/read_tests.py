import inspect
import os
import sys

from typing import List, Dict

from testipy import get_exec_logger
from testipy.configs import enums_data, default_config
from testipy.lib_modules import py_inspector, common_methods as cm
from testipy.lib_modules.args_parser import ArgsParser
from testipy.helpers import load_config
from testipy.engine.models import (
    PackageAttr, SuiteAttr, TestMethodAttr,
    get_package_by_name,
    mark_packages_suites_methods_ids,
    show_test_structure,
    sort_test_structure,
)
from testipy.engine.read_tests_utils import (
    TYPE_DOC,
    ConfigFilters,
    get_doc_dict,
    is_auto_include_test_tag,
    is_valid_level,
    is_valid_tag,
    is_valid_tag_features,
    is_valid_tag_testnumber,
)


_exec_logger = get_exec_logger()


def get_selected_tests(full_path_tests_scripts_foldername: str,
                       include_package=[], exclude_package=[],
                       include_suite_tag=[], exclude_suite_tag=[],
                       include_test_tag=[], exclude_test_tag=[],
                       level_filter=([],[],[],[]),
                       include_feature=[], exclude_feature=[],
                       include_testnumber=[], exclude_testnumber=[]) -> List[PackageAttr]:

    def __is_valid_package(package_name: str) -> bool:
        return not package_name.startswith(".") and not package_name.endswith("__pycache__") and (
                (not include_package and not exclude_package) or
                (not include_package and not cm.validate_begins_with(package_name, exclude_package)) or
                (not exclude_package and cm.validate_begins_with(package_name, include_package)) or
                (cm.validate_begins_with(package_name, include_package) and not cm.validate_begins_with(package_name, exclude_package)))

    def __is_valid_suite(obj, doc: TYPE_DOC, suite_name: str) -> bool:
        return inspect.isclass(obj) and is_valid_tag(suite_name, default_config.prefix_suite, doc, include_suite_tag, exclude_suite_tag)

    def __is_valid_test_method(obj, doc: TYPE_DOC, method_name: str) -> bool:
        return inspect.isfunction(obj) and is_valid_level(doc, level_filter) and (is_auto_include_test_tag(doc) or (
                is_valid_tag(method_name, default_config.prefix_tests, doc, include_test_tag, exclude_test_tag) and
                is_valid_tag_features(doc, include_feature, exclude_feature) and
                is_valid_tag_testnumber(doc, include_testnumber, exclude_testnumber))
        )

    def __get_test_methods_list_from_suite_obj(suite_obj, suite_doc, suite_item: SuiteAttr) -> List[TestMethodAttr]:
        test_methods_list: List[TestMethodAttr] = []
        _test_methods: Dict[str, TestMethodAttr] = {}
        _depends_prio_tests_to_auto_include = set()
        ConfigFilters.auto_included_tests = 0

        def is_test_on_list(method_attr: TestMethodAttr) -> bool:
            for ma in test_methods_list:
                if ma.method_name == method_attr.method_name:
                    return True
            return False

        for method_name, obj in inspect.getmembers(suite_obj):
            if method_name.startswith(default_config.prefix_tests):
                mname = method_name[len(default_config.prefix_tests):] if default_config.trim_prefix_tests else method_name
                doc = get_doc_dict(obj, mname)
                doc[enums_data.TAG_TESTNUMBER] = suite_doc[enums_data.TAG_TESTNUMBER] + doc[enums_data.TAG_TESTNUMBER]

                # create new test and add to test_methods
                test_method = TestMethodAttr(
                    suite=suite_item,

                    method_name=method_name,
                    method_obj=obj,

                    param=py_inspector.get_method_parameter_default_value(obj, "param", None),
                    ncycles=py_inspector.get_method_parameter_default_value(obj, "ncycles", 1),

                    name=doc[enums_data.TAG_NAME],
                    comment=py_inspector.get_comment(obj) or "",
                    prio=doc[enums_data.TAG_PRIO],
                    level=doc[enums_data.TAG_LEVEL],
                    tags=doc[enums_data.TAG_TAG],
                    features=doc[enums_data.TAG_FEATURES],
                    test_number=doc[enums_data.TAG_TESTNUMBER],

                    depends=doc[enums_data.TAG_DEPENDS],
                    on_success=doc[enums_data.TAG_ON_SUCCESS],
                    on_failure=doc[enums_data.TAG_ON_FAILURE],
                )
                _test_methods[method_name] = test_method

                # add to selected tests and add dependency to other tests
                if __is_valid_test_method(obj, doc, method_name):
                    test_methods_list.append(test_method)
                    # update auto include tests that have dependency to other tests, based on prio
                    _depends_prio_tests_to_auto_include.update(doc[enums_data.TAG_DEPENDS])

        # find tests (methods) that must be included because of dependency
        changes_were_made = len(_depends_prio_tests_to_auto_include) > 0
        while changes_were_made:
            changes_were_made = False
            for method_name, test_method in _test_methods.items():
                if test_method.prio in _depends_prio_tests_to_auto_include:
                    if not is_test_on_list(test_method):
                        test_methods_list.append(test_method)
                        _depends_prio_tests_to_auto_include.update(test_method.depends)

                        ConfigFilters.inc()
                        changes_were_made = True

        # order test list
        if test_methods_list:
            if len(test_methods_list) > ConfigFilters.auto_included_tests:
                test_methods_list = sorted(test_methods_list, key=lambda x: (x.prio, x.method_name), reverse=False)
            else:
                test_methods_list = []

        return test_methods_list

    def __get_suites_list_from_file_with_test_methods(fpn: str, filename: str, package: PackageAttr) -> List[SuiteAttr]:
        suite_list = []

        for suite_name, obj in py_inspector.get_members_from_file(fpn):
            if suite_name.startswith(default_config.prefix_suite):
                sname = suite_name[len(default_config.prefix_suite):] if default_config.trim_prefix_suite else suite_name
                doc = get_doc_dict(obj, sname)
                if __is_valid_suite(obj, doc, suite_name):
                    # Create a Suite object
                    suite = SuiteAttr(
                        package=package,
                        filename=filename,
                        suite_name=suite_name,
                        suite_obj=obj,
                        ncycles=1,
                        test_methods_list=[],
                        comment=py_inspector.get_comment(obj) or "",
                        name=doc[enums_data.TAG_NAME],
                        prio=doc[enums_data.TAG_PRIO],
                        level=doc[enums_data.TAG_LEVEL],
                        tags=doc[enums_data.TAG_TAG],
                        features=doc[enums_data.TAG_FEATURES],
                        test_number=doc[enums_data.TAG_TESTNUMBER]
                    )
                    test_methods_list = __get_test_methods_list_from_suite_obj(obj, doc, suite)
                    if test_methods_list:
                        suite.add_tests(test_methods_list)
                        suite_list.append(suite)

        return suite_list

    def __get_package_suite_test_methods_list(full_path_foldername: str, package_name: str = "") -> List[PackageAttr]:
        packages_suites_methods_list: List[PackageAttr] = []

        vp = __is_valid_package(package_name)

        if vp:
            package = PackageAttr(package_name=package_name, suite_list=[], ncycles=1)
            # add current package to PATH
            sys.path.insert(0, full_path_foldername)

        for filename in sorted(os.listdir(full_path_foldername)):
            fpn = os.path.join(full_path_foldername, filename)

            if os.path.isdir(fpn):
                packages_suites_methods_list += __get_package_suite_test_methods_list(
                    fpn, package_name + default_config.separator_package + filename
                )

            elif vp and os.path.isfile(fpn) and filename.endswith(".py"):
                suite_list = __get_suites_list_from_file_with_test_methods(fpn, filename, package)
                if suite_list:
                    package.add_suites(suite_list)

        if vp and package.suite_list:
            packages_suites_methods_list.append(package)
            # remove current package from PATH
            sys.path.remove(full_path_foldername)

        return packages_suites_methods_list

    #  -  -  -  -  -  -  -  -  main function starts here  -  -  -  -  -  -  -  -  #
    if not os.path.isdir(full_path_tests_scripts_foldername):
        raise NotADirectoryError(full_path_tests_scripts_foldername)

    selected_tests = []

    for name in sorted(os.listdir(full_path_tests_scripts_foldername)):
        fpn = os.path.join(full_path_tests_scripts_foldername, name)
        if os.path.isdir(fpn):
            package_list = __get_package_suite_test_methods_list(fpn, name)
            if package_list:
                selected_tests += package_list

    selected_tests = mark_packages_suites_methods_ids(sort_test_structure(selected_tests))

    return selected_tests


def filter_tests_by_storyboard(storyboard_json_files: List[str], all_tests: List[PackageAttr]) -> List[PackageAttr]:
    selected_tests = []

    for sb_json_file in storyboard_json_files:
        storyboard = load_config(sb_json_file)

        for sb_package in storyboard["package_list"]:
            # get cloned package dict, based on package_of_storyboard, from all tests
            current_package: PackageAttr = get_package_by_name(all_tests, sb_package["package_name"])

            if current_package:
                current_package = current_package.duplicate(clone_children=False)
                suite_list: List[SuiteAttr] = []

                # add all suites from package if none specified on storyboard
                if not sb_package.get("suite_list"):
                    sb_package["suite_list"] = [{"suite_name": suite.suite_name} for suite in current_package.suite_list]

                for sb_suite in sb_package["suite_list"]:
                    # get cloned suite dict, based on suite_of_storyboard, from all_tests->current_package
                    current_suite: SuiteAttr = current_package.get_suite_by_name(sb_suite["suite_name"])
                    if current_suite:
                        current_suite = current_suite.duplicate(current_package, clone_children=False)
                        test_methods_list: List[TestMethodAttr] = []

                        # add storyboard suite attributes, override values such as ncycle
                        for k, v in sb_suite.items():
                            if k == "ncycles":
                                current_suite.ncycles = v

                        # add all tests from suite if none specified on storyboard
                        if not sb_suite.get("test_list"):
                            sb_suite["test_list"] = [{"test_name": test_method["method_name"]} for test_method in current_suite.test_methods_list]

                        # filter tests based on storyboard
                        for sb_test in sb_suite["test_list"]:
                            current_method_attr: TestMethodAttr = current_suite.get_test_method_by_name(sb_test["test_name"])
                            if current_method_attr:
                                current_method_attr = current_method_attr.duplicate(current_suite)
                                # add storyboard test attributes, override values such as ncycle and param
                                for k, v in sb_test.items():
                                    if k  == "ncycles":
                                        current_method_attr.ncycles = v
                                    elif  k== "param":
                                        current_method_attr.param = v

                                test_methods_list.append(current_method_attr)

                        # add to selected_tests
                        if test_methods_list:
                            # add suite kwargs for suite __init__()
                            current_suite.suite_kwargs = cm.dict_without_keys(sb_suite, ["suite_name", "test_list", "ncycles"])

                            # update lists
                            current_suite.test_methods_list = test_methods_list
                            suite_list.append(current_suite)

                if suite_list:
                    # add storyboard package attributes, override values such as ncycle
                    for k, v in sb_package.items():
                        if k == "ncycles":
                            current_package.ncycles = v

                    current_package.suite_list = suite_list
                    selected_tests.append(current_package)

    selected_tests = mark_packages_suites_methods_ids(selected_tests)

    return selected_tests


def read_files_to_get_selected_tests(ap: ArgsParser, storyboard_json_files: List[str], full_path_tests_scripts_foldername: str, verbose=False):
    cm.TESTS_ROOT_FOLDER = full_path_tests_scripts_foldername
    all_tests = get_selected_tests(full_path_tests_scripts_foldername=full_path_tests_scripts_foldername,
                                   include_package=ap.get_options_arguments("-ip"), exclude_package=ap.get_options_arguments("-ep"),
                                   include_suite_tag=ap.get_options_arguments("-is"), exclude_suite_tag=ap.get_options_arguments("-es"),
                                   include_test_tag=ap.get_options_arguments("-it"), exclude_test_tag=ap.get_options_arguments("-et"),
                                   level_filter=(ap.get_options_arguments("-ilv"), ap.get_options_arguments("-elv"), ap.get_options_arguments("-alv"), ap.get_options_arguments("-blv")),
                                   include_feature=ap.get_options_arguments("-if"), exclude_feature=ap.get_options_arguments("-ef"),
                                   include_testnumber=ap.get_options_arguments("-itn"), exclude_testnumber=ap.get_options_arguments("-etn"))

    if storyboard_json_files:
        all_tests = filter_tests_by_storyboard(storyboard_json_files, all_tests)

    if verbose and all_tests:
        test_structure: str = show_test_structure(all_tests)
        print(test_structure)
        print("="*160)
        _exec_logger.info(f"TestStructure: {test_structure}")

    return all_tests
