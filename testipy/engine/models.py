from typing import Union, List, Set, Dict


class TestMethodAttr:
    def __init__(
            self, suite_attr: "SuiteAttr", method_name: str,
            method_obj: object = None, ncycles: int = 1, param: object = None,
            name: str = "", comment: str = "", prio: int = 0, level: int = 1,
            features: str = "", test_number: str = "",
            tags: Set[str] = None,
            depends: Set[int] = None, on_success: Set[int] = None, on_failure: Set[int] = None
    ):
        self.suite_attr: SuiteAttr = suite_attr

        self.method_name: str = method_name
        self.method_obj: object = method_obj
        self.method_id: int = suite_attr.get_max_test_method_id()

        self.param: object = param
        self.ncycles: int = ncycles

        self.name: str = name or method_name
        self.comment: str = comment
        self.prio: int = prio
        self.level: int = level
        self.features: str = features
        self.test_number: str = test_number
        self.tags: Set[str] = tags or set()

        self.depends: Set[int] = depends or set()
        self.on_success: Set[int] = on_success or set()
        self.on_failure: Set[int] = on_failure or set()
        
        suite_attr.test_method_attr_list.append(self)

    def duplicate(self, suite_attr: "SuiteAttr"):
        _new_attr = TestMethodAttr(
            suite_attr=suite_attr,

            method_name=self.method_name,
            method_obj=self.method_obj,

            param=self.param,
            ncycles=self.ncycles,

            name=self.name,
            comment=self.comment,
            prio=self.prio,
            level=self.level,
            features=self.features,
            test_number=self.test_number,
            tags = self.tags,

            depends=self.depends,
            on_success=self.on_success,
            on_failure=self.on_failure
        )
        _new_attr.method_id = self.method_id

        return _new_attr

    def get_common_attr_as_dict(self) -> Dict:
        return dict(
            method_name=self.method_name,
            method_id=self.method_id,

            param=self.param,
            ncycles=self.ncycles,

            name=self.name,
            comment=self.comment,
            prio=self.prio,
            level=self.level,
            features=self.features,
            test_number=self.test_number,
            tags=list(self.tags),

            depends=list(self.depends),
            on_success=list(self.on_success),
            on_failure=list(self.on_failure)
        )

    def __repr__(self):
        return f"<TestMethodAttr {self.method_id}: {self.method_name}[x{self.ncycles}]>"


class SuiteAttr:
    def __init__(self, package_attr: "PackageAttr", filename: str, suite_name: str,
                 suite_obj: object = None, ncycles: int = 1, suite_kwargs: dict = None,
                 test_method_attr_list: List[TestMethodAttr] = None,
                 name: str = "", comment: str = "", prio: int = 0, level: int = 1,
                 features: str = "", test_number: str = "",
                 tags: Set[str] = None):
        self.package: PackageAttr = package_attr

        self.filename: str = filename
        self.suite_name: str = suite_name
        self.suite_obj = suite_obj
        self.suite_id: int = package_attr.get_max_suite_id()
        self.suite_kwargs: dict = suite_kwargs or {}

        self.app = None

        self.test_method_attr_list: List[TestMethodAttr] = test_method_attr_list or []
        self.ncycles: int = ncycles

        self.name: str = name or suite_name or filename
        self.comment: str = comment
        self.prio: int = prio
        self.level: int = level
        self.features: str = features
        self.test_number: str = test_number
        self.tags: Set[str] = tags or set()
        
        package_attr.suite_attr_list.append(self)

    def get_test_method_by_name(self, name: str) -> Union[TestMethodAttr, None]:
        for test_method_attr in self.test_method_attr_list:
            if test_method_attr.method_name == name or test_method_attr.name == name:
                return test_method_attr
        return None

    def get_max_test_method_id(self) -> int:
        _max_rec = len(self.test_method_attr_list)
        _max_id = max([ma.method_id for ma in self.test_method_attr_list]) if _max_rec > 0 else 0
        return max(_max_rec, _max_id) + 1

    def duplicate(self, package: "PackageAttr", clone_children: bool = True):
        _new_attr = SuiteAttr(
            package_attr=package,

            filename=self.filename,
            suite_name=self.suite_name,
            suite_obj=self.suite_obj,
            suite_kwargs=self.suite_kwargs,

            test_method_attr_list=self.test_method_attr_list,
            ncycles=self.ncycles,

            name=self.name,
            comment=self.comment,
            prio=self.prio,
            level=self.level,
            tags=self.tags,
            features=self.features,
            test_number=self.test_number
        )
        _new_attr.suite_id = self.suite_id

        if clone_children:
            for test_method_attr in self.test_method_attr_list:
                test_method_attr.duplicate(_new_attr)

        return _new_attr

    def __repr__(self):
        return f"<SuiteAttr {self.suite_id}: {self.suite_name}[x{self.ncycles}], Methods: {len(self.test_method_attr_list)}>"


class PackageAttr:
    __counter: int = 0

    def __init__(
            self,
            package_name: str,
            suite_attr_list: List[SuiteAttr] = None,
            ncycles: int = 1
    ):
        self.__counter += 1
        self.package_name: str = package_name
        self.package_id: int = self.__counter

        self.suite_attr_list: List[SuiteAttr] = suite_attr_list or []
        self.ncycles: int = ncycles

    def get_suite_by_name(self, name: str) -> Union[SuiteAttr, None]:
        for suite in self.suite_attr_list:
            if suite.suite_name == name or suite.name == name:
                return suite
        return None

    def get_max_suite_id(self) -> int:
        _max_rec = len(self.suite_attr_list)
        _max_id = max([suite_attr.suite_id for suite_attr in self.suite_attr_list]) if _max_rec > 0 else 0
        return max(_max_rec, _max_id) + 1

    def get_max_test_method_id(self):
        _max_rec = len(self.suite_attr_list)
        _max_id = max([suite_attr.get_max_test_method_id() for suite_attr in self.suite_attr_list]) if _max_rec > 0 else 0
        return max(_max_rec+1, _max_id)

    def duplicate(self, clone_children: bool = True):
        _new_attr = PackageAttr(
            package_name=self.package_name,
            suite_attr_list=self.suite_attr_list,
            ncycles=self.ncycles
        )
        _new_attr.package_id = self.package_id
        
        if clone_children:
            for suite in self.suite_attr_list:
                suite.duplicate(_new_attr, clone_children=clone_children)
            
        return _new_attr

    def __repr__(self):
        return f"<PackageAttr {self.package_id}: {self.package_name}[x{self.ncycles}], Suites: {len(self.suite_attr_list)}>"


def mark_packages_suites_methods_ids(package_attr_list: List[PackageAttr]) -> List[PackageAttr]:
    package_id = suite_id = method_id = 0

    for package in package_attr_list:
        package_id += 1
        package.package_id = package_id

        for suite in package.suite_attr_list:
            suite_id += 1
            suite.suite_id = suite_id

            for method in suite.test_method_attr_list:
                method_id += 1
                method.method_id = method_id

    return package_attr_list


# Sorting function for package, suite, and method structure
def sort_test_structure(package_attr_list: List[PackageAttr]) -> List[PackageAttr]:
    # Sort Packages
    package_attr_list.sort(key=lambda package: (package.package_name))

    for package_attr in package_attr_list:
        # Sort Suites within each Package
        package_attr.suite_attr_list.sort(key=lambda suite: (suite.prio, suite.suite_name))

        for suite_attr in package_attr.suite_attr_list:
            # Sort Test Methods within each Suite
            suite_attr.test_method_attr_list.sort(key=lambda test: (test.prio, test.method_name))

    return package_attr_list


def get_package_by_name(package_attr_list: List[PackageAttr], name: str) -> Union[PackageAttr, None]:
    for package_attr in package_attr_list:
        if package_attr.package_name == name:
            return package_attr
    return None


# show test list
def show_test_structure(package_attr_list: List[PackageAttr]) -> str:
    str_res = ""
    for package_attr in package_attr_list:
        str_res += f"\n{package_attr}\n"

        for suite_attr in package_attr.suite_attr_list:
            str_res += f"\t{suite_attr}\n"

            for test_method_attr in suite_attr.test_method_attr_list:
                str_res += f"\t\t{test_method_attr}\n"

    return str_res[1:-1]
