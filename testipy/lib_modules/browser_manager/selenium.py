from time import sleep

from selenium import webdriver as WEB_DRIVER_SELENIUM
from selenium.common.exceptions import InvalidSessionIdException
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

from testipy import get_exec_logger
from testipy.helpers import Timer


SAFE_BROWSER = {
    "browser_name": "chrome",
    "option_arguments": ["--headless", "--no-sandbox", "--disable-dev-shm-usage", "--incognito", "disable-cache"]
}


def is_chrome(browser_name):
    return browser_name == "chrome"


def is_firefox(browser_name):
    return browser_name == "firefox"


def setup_options(browser_name: str = None, option_arguments: list = None, option_preferences: dict = None):
    if is_firefox(browser_name):
        browser_options = WEB_DRIVER_SELENIUM.FirefoxOptions()
    else:
        browser_options = WEB_DRIVER_SELENIUM.ChromeOptions()

    # add arguments & preferences to browser options
    for arg in option_arguments:
        browser_options.add_argument(arg)
    for k, v in option_preferences.items():
        browser_options.set_preference(k, v)

    return browser_options


class SeleniumController:

    def __init__(self, rm):
        self.rm = rm
        self.name = "selenium"

        self.webdriver: WEB_DRIVER_SELENIUM.Chrome = None
        self.browser_name = None
        self.default_browser_settings: dict = None

    def set_default_webdriver(self, default_browser_settings: dict):
        assert isinstance(default_browser_settings, dict)
        self.default_browser_settings = default_browser_settings
        return self

    def setup_webdriver(self, browser_name, option_arguments: list = [], option_preferences: dict = {}, implicitly_wait=14, set_page_load_timeout=17, **trash):
        if browser_name is None:
            self._setup_default_webdriver()
        else:
            self.close()
            self.browser_name = browser_name

            # setup browser options
            browser_options = setup_options(browser_name, option_arguments, option_preferences)

            if is_firefox(browser_name):
                self.webdriver = WEB_DRIVER_SELENIUM.Firefox(options=browser_options)
            elif is_chrome(browser_name):
                self.webdriver = WEB_DRIVER_SELENIUM.Chrome(options=browser_options)
            else:
                raise ValueError(f"Unknown {browser_name=}")

            # setup timeouts
            self.webdriver.implicitly_wait(implicitly_wait)
            self.webdriver.set_page_load_timeout(set_page_load_timeout)

        return self

    def _setup_default_webdriver(self):
        try:
            if self.default_browser_settings and self.default_browser_settings["browser_name"]:
                self.setup_webdriver(**self.default_browser_settings)
                _exec_logger.debug(f"Started 'Default' {self}")
            else:
                raise ValueError("No default browser set!")
        except:
            self.setup_webdriver(**SAFE_BROWSER)
            _exec_logger.debug(f"Started 'Safe' {self}")
        return self

    def close(self):
        if self.webdriver is not None:
            try:
                self.webdriver.quit()
            except:
                pass
            self.webdriver = None

        return self

    def stop(self):
        self.close()

    def is_browser_setup(self) -> bool:
        return self.webdriver is not None

    def get_webdriver(self) -> WEB_DRIVER_SELENIUM.Chrome:
        return self.webdriver

    def take_screenshot(self, current_test):
        if self.webdriver is not None:
            try:
                self.webdriver.save_screenshot("selenium_screenshot.png")
                self.rm.copy_file(current_test, orig_filename="selenium_screenshot.png", delete_source=True)
            except InvalidSessionIdException:
                pass    # browser was closed...

        return self

    def goto(self, url: str):
        self.webdriver.get(url)
        return self

    def find_element(self, value=None, by=By.CSS_SELECTOR):
        return self.webdriver.find_element(by=by, value=value)

    def find_elements(self, value=None, by=By.CSS_SELECTOR):
        return self.webdriver.find_elements(by=by, value=value)

    def click_and_type(self, value, text_to_send, add_enter=True, by=By.CSS_SELECTOR, timeout=10.0, sleep_time=0.5):
        if add_enter:
            text_to_send = "" if not text_to_send else text_to_send
            text_to_send += Keys.RETURN

        wait_timer = Timer(timeout)
        while wait_timer.is_timer_valid():
            try:
                element = self.find_element(by=by, value=value)
                element.click()
                if text_to_send:
                    element.send_keys(text_to_send)
            except Exception as e:
                em = str(e)
                et = type(e)
                wait_timer.sleep_for(sleep_time)
            else:
                return self
        raise et(f"Get element '{value}' FAILED: {em}")

    def click_element(self, **kwargs):
        self.find_element(**kwargs).click()
        return self

    def select_by_visible_text(self, text: str, value=None, by=By.CSS_SELECTOR):
        Select(self.find_element(by=by, value=value)).select_by_visible_text(text)
        return self

    def new_tab(self, url: str, tab_name: str = "new_tab"):
        self.webdriver.execute_script(f'''window.open("{url}", "{tab_name}");''')
        self.webdriver.switch_to.window(tab_name)

    def open_tab(self, tab_name: str = "new_tab"):
        self.webdriver.switch_to.window(tab_name)

    def close_tab(self):
        self.webdriver.close()
        self.webdriver.switch_to.window(self.webdriver.window_handles[0])

    def switch_to_frame(self, **kwargs):
        self.webdriver.switch_to.frame(self.find_element(**kwargs))
        return self

    def switch_to_previous_frame(self):
        self.webdriver.switch_to.default_content()
        return self

    def sleep(self, wait_for: float = 0.0):
        if wait_for > 0:
            sleep(wait_for)

    def execute_script(self, script: str):
        return self.webdriver.execute_script(script)

    def get_element_by_visible_text(self, by: str, value: str, text: str, wait_for: int = None):
        if wait_for is None:
            wait_for = 12

        t = Timer(wait_for)
        while t.is_timer_valid():
            t.sleep_for(0.2)
            for elem in self.find_elements(by=by, value=value):
                if elem.text == text:
                    return elem

        raise ValueError(f"Unable to locate element: {value} {text}")

    def get_element(self, by: str, value: str, wait_for: int = None):
        if wait_for is None:
            wait_for = 12

        t = Timer(wait_for)
        while t.is_timer_valid():
            t.sleep_for(0.2)
            try:
                return self.find_element(by=by, value=value)
            except Exception as ex:
                exception = ex

        raise exception

    # div.name-of-class[field='value'] > span.name-of-class[...
    def page_has_element(self, tag_filter: str, text: str = None, wait_for: int = None):
        if wait_for is None:
            wait_for = 12

        t = Timer(wait_for)
        while t.is_timer_valid():
            t.sleep_for(0.2)
            try:
                for element in self.find_elements(by=By.CSS_SELECTOR, value=tag_filter):
                    if text is None or element.text == text:
                        return element
            except:
                pass

        raise ValueError(f"Element {tag_filter} with {text=} not found within {wait_for}s")

    # assure that the element (with text) is not being displayed on the page
    def page_doesnt_has_element(self, tag_filter: str, text: str = None):
        for element in self.find_elements(by=By.CSS_SELECTOR, value=tag_filter):
            if text is None:
                raise ValueError(f"Page has element {tag_filter}")
            if element.text == text:
                raise ValueError(f"Page has element {tag_filter} with {text=}")

    def get_element_screenshot_as_base64(self, value: str, wait_for: float = 10):
        element = self.get_element(value=value, wait_for=wait_for)

        assert element.size["width"] > 0, "0 width"
        assert element.size["height"] > 0, "0 height"

        # data:image/png;base64,
        return element.screenshot_as_base64
