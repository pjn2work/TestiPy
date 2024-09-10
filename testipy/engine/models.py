from typing import Union, List, Set


class TestMethodAttr:
    def __init__(
            self, suite: "SuiteAttr", method_name: str,
            method_obj: object = None, ncycles: int = 1, param: object = None,
            name: str = "", comment: str = "", prio: int = 0, level: int = 1,
            features: str = "", test_number: str = "",
            tags: Set[str] = None,
            depends: Set[int] = None, on_success: Set[int] = None, on_failure: Set[int] = None
    ):
        self.suite: SuiteAttr = suite

        self.method_name: str = method_name
        self.method_obj: object = method_obj
        self.method_id: int = 0

        self.param: object = param
        self.ncycles: int = ncycles

        self.name: str = name
        self.comment: str = comment
        self.prio: int = prio
        self.level: int = level
        self.features: str = features
        self.test_number: str = test_number
        self.tags: Set[str] = tags or set()

        self.depends: Set[int] = depends or set()
        self.on_success: Set[int] = on_success or set()
        self.on_failure: Set[int] = on_failure or set()

    def duplicate(self, suite: "SuiteAttr"):
        _other = TestMethodAttr(
            suite=suite,

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
        _other.method_id = self.method_id

        return _other

    def __repr__(self):
        return f"<TestMethodAttr {self.method_id}: {self.method_name}[x{self.ncycles}]>"


class SuiteAttr:
    def __init__(self, package: "PackageAttr", filename: str, suite_name: str,
                 suite_obj: object = None, ncycles: int = 1, suite_kwargs: dict = None,
                 test_methods_list: List[TestMethodAttr] = None,
                 name: str = "", comment: str = "", prio: int = 0, level: int = 1,
                 features: str = "", test_number: str = "",
                 tags: Set[str] = None):
        self.package: PackageAttr = package

        self.filename: str = filename
        self.suite_name: str = suite_name
        self.suite_obj = suite_obj
        self.suite_id: int = 0
        self.suite_kwargs: dict = suite_kwargs or {}

        self.app = None

        self.test_methods_list: List[TestMethodAttr] = test_methods_list or []
        self.ncycles: int = ncycles

        self.name: str = name
        self.comment: str = comment
        self.prio: int = prio
        self.level: int = level
        self.features: str = features
        self.test_number: str = test_number
        self.tags: Set[str] = tags or set()

    def add_tests(self, method_items: Union[TestMethodAttr, List[TestMethodAttr]]):
        if isinstance(method_items, TestMethodAttr):
            method_items = [method_items]
        for method_item in method_items:
            method_item.suite = self
            self.test_methods_list.append(method_item)

    def get_test_method_by_name(self, name: str) -> Union[TestMethodAttr, None]:
        for test_method in self.test_methods_list:
            if test_method.method_name == name or test_method.name == name:
                return test_method
        return None

    def duplicate(self, package: "PackageAttr", clone_children: bool = True):
        _other = SuiteAttr(
            package=package,

            filename=self.filename,
            suite_name=self.suite_name,
            suite_obj=self.suite_obj,
            suite_kwargs=self.suite_kwargs,

            test_methods_list=self.test_methods_list,
            ncycles=self.ncycles,

            name=self.name,
            comment=self.comment,
            prio=self.prio,
            level=self.level,
            tags=self.tags,
            features=self.features,
            test_number=self.test_number
        )
        _other.suite_id = self.suite_id

        if clone_children:
            _other.test_methods_list = [test_method.duplicate(_other) for test_method in self.test_methods_list]

        return _other

    def __repr__(self):
        return f"<SuiteAttr {self.suite_id}: {self.suite_name}[x{self.ncycles}], Methods: {len(self.test_methods_list)}>"


class PackageAttr:
    def __init__(self, package_name: str,
                 suite_list: List[SuiteAttr] = None, ncycles: int = 1):
        self.package_name: str = package_name
        self.package_id: int = 0

        self.suite_list: List[SuiteAttr] = suite_list or []
        self.ncycles: int = ncycles

    def add_suites(self, suites: Union[SuiteAttr, List[SuiteAttr]]):
        if isinstance(suites, SuiteAttr):
            suites = [suites]
        for suite in suites:
            suite.package = self
            self.suite_list.append(suite)

    def get_suite_by_name(self, name: str) -> Union[SuiteAttr, None]:
        for suite in self.suite_list:
            if suite.suite_name == name or suite.name == name:
                return suite
        return None

    def duplicate(self, clone_children: bool = True):
        _other = PackageAttr(
            package_name=self.package_name,
            suite_list=self.suite_list,
            ncycles=self.ncycles
        )
        _other.package_id = self.package_id
        if clone_children:
            _other.suite_list = [suite.duplicate(_other, clone_children=clone_children) for suite in self.suite_list]
            
        return _other

    def __repr__(self):
        return f"<PackageAttr {self.package_id}: {self.package_name}[x{self.ncycles}], Suites: {len(self.suite_list)}>"


def mark_packages_suites_methods_ids(test_list: List[PackageAttr]) -> List[PackageAttr]:
    package_id = suite_id = method_id = 0

    for package in test_list:
        package_id += 1
        package.package_id = package_id

        for suite in package.suite_list:
            suite_id += 1
            suite.suite_id = suite_id

            for method in suite.test_methods_list:
                method_id += 1
                method.method_id = method_id

    return test_list


# Sorting function for package, suite, and method structure
def sort_test_structure(test_structure: List[PackageAttr]) -> List[PackageAttr]:
    # Sort Packages
    test_structure.sort(key=lambda package: (package.package_name))

    for package in test_structure:
        # Sort Suites within each Package
        package.suite_list.sort(key=lambda suite: (suite.prio, suite.suite_name))

        for suite in package.suite_list:
            # Sort Test Methods within each Suite
            suite.test_methods_list.sort(key=lambda test: (test.prio, test.method_name))

    return test_structure


def get_package_by_name(packages: List[PackageAttr], name: str) -> Union[PackageAttr, None]:
    for package in packages:
        if package.package_name == name:
            return package
    return None


# show test list
def show_test_structure(selected_packages_suites_methods_list: List[PackageAttr]) -> str:
    str_res = ""
    for package in selected_packages_suites_methods_list:
        str_res += f"\n{package}\n"

        for suite in package.suite_list:
            str_res += f"\t{suite}\n"

            for test_method in suite.test_methods_list:
                str_res += f"\t\t{test_method}\n"

    return str_res[1:-1]
