from typing import List, Tuple, Dict, Any

from testipy.configs import enums_data, default_config
from testipy.lib_modules import py_inspector, common_methods as cm


TYPE_DOC = Dict[str, Any]


class ConfigFilters:
    auto_included_tests = 0

    @classmethod
    def inc(cls):
        cls.auto_included_tests += 1


# returns dict of doc from class or method
def get_doc_dict(obj, name: str = "") -> TYPE_DOC:
    doc_dict = dict()
    doc_dict[enums_data.TAG_NAME] = name
    doc_dict[enums_data.TAG_TAG] = set()
    doc_dict[enums_data.TAG_LEVEL] = 1 if default_config.execute_test_with_no_doc else 0
    doc_dict[enums_data.TAG_PRIO] = 999
    doc_dict[enums_data.TAG_FEATURES] = ""
    doc_dict[enums_data.TAG_TESTNUMBER] = ""
    doc_dict[enums_data.TAG_DEPENDS] = set()
    doc_dict[enums_data.TAG_ON_SUCCESS] = set()
    doc_dict[enums_data.TAG_ON_FAILURE] = set()

    doc = py_inspector.get_doc(obj)
    if doc:
        for line in doc.split("\n"):
            if line.startswith(enums_data.PREFIX_TAGS):
                if " " not in line:
                    raise AttributeError(f"tag {line} must have arguments after, inside {obj}")

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
    doc["auto_included"] = False
    if doc[enums_data.TAG_LEVEL] > 0:
        for tag in default_config.auto_include_tests_with_tags:
            if tag in doc[enums_data.TAG_TAG]:
                ConfigFilters.inc()
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

