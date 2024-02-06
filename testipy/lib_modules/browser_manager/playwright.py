#!/usr/bin/env python3
import base64

from time import sleep
from playwright.sync_api import sync_playwright, Browser, Page, Locator, BrowserContext

from testipy import get_exec_logger

SAFE_BROWSER = {
    "browser_name": "chrome",
    "is_custom": True,
    "method_args": {
        "headless": True
    },
    "option_arguments": ["--no-sandbox", "--disable-dev-shm-usage", "--incognito", "--disable-cache"],
    "option_preferences": {}
}

_exec_logger = get_exec_logger()


class PlaywrightController:

    def __init__(self, rm):
        self.rm = rm
        self.name = "playwright"
        self.iframes_selectors = list()
        self.default_browser_settings: dict = None
        self.browser_name = None
        self._screenshot_num = 0

        # playwright stuff
        self.playwright = sync_playwright().start()
        self.browsers: dict[str, Browser] = {
            "chrome": None,
            "firefox": None,
            "webkit": None,
            "custom": None
        }
        self.contexts: dict[str, BrowserContext] = {
            "chrome": None,
            "firefox": None,
            "webkit": None,
            "custom": None
        }
        self.page: Page = None
        self.tabs: dict[str, Page] = dict()

    def set_default_webdriver(self, default_browser_settings: dict):
        assert isinstance(default_browser_settings, dict)
        self.default_browser_settings = default_browser_settings

        return self

    def new_context(self, device: dict = None):
        browser = self.get_browser_in_use()

        # close current context if exists
        if self.contexts[self.browser_name]:
            self.contexts[self.browser_name].close()

        # create new context
        if device and isinstance(device, dict):
            _device = self.playwright.devices[device["name"]] if "name" in device else {}
            _context = device.get("context", {})
            self.contexts[self.browser_name] = browser.new_context(**_device, **_context)
        else:
            self.contexts[self.browser_name] = browser.new_context()

        return self

    def setup_webdriver(self, browser_name: str = None, **kwargs):
        if browser_name is None:
            self._setup_default_webdriver()
        else:
            self.close_browser()
            self._init_browsers(browser_name=browser_name, **kwargs)

        return self

    def close_browser(self):
        if self.browser_name and self.browser_name == "custom":
            try:
                self.browsers["custom"].close()
            except:
                pass

            self.browsers["custom"] = None
            self.contexts["custom"] = None
            self.browser_name = None
        else:
            try:
                self.page.close()
            except:
                pass

        for k in list(self.tabs):
            del self.tabs[k]

        self.page = None

    def stop(self):
        self.close_browser()
        self.playwright.stop()

    def _init_browsers(self,
                       browser_name: str = None,
                       method_args: dict = None,
                       option_arguments: list[str] = None,
                       option_preferences: dict = None,
                       device: dict = None,
                       is_custom: bool = True):
        # assert browser to be valid
        assert browser_name in self.browsers, f"{browser_name=} not known!"
        self.browser_name = "custom" if is_custom else browser_name

        # don't init same browser if already launched, unless is custom
        if is_custom or self.browsers[browser_name] is None:
            # by default headless is False
            if method_args is None or not isinstance(method_args, dict):
                method_args = {"headless": False}
            if "headless" not in method_args:
                method_args["headless"] = False

            # override test env settings with run parameters
            if self.rm.has_ap_flag("--headless"):
                method_args["headless"] = True

            # launch specific browsers
            if browser_name == "webkit":
                self.browsers[self.browser_name] = self.playwright.webkit.launch(**method_args, args=option_arguments)
            elif browser_name == "firefox":
                self.browsers[self.browser_name] = self.playwright.firefox.launch(**method_args, args=option_arguments, firefox_user_prefs=option_preferences)
            else:
                self.browsers[self.browser_name] = self.playwright.chromium.launch(**method_args, args=option_arguments)

            # start new context
            self.new_context(device)
            _exec_logger.debug(f"{self.name} - Created new browser {browser_name} {is_custom=} {method_args}")

    def get_browser_in_use(self) -> Browser:
        if self.browser_name is None or self.browsers[self.browser_name] is None:
            self._setup_default_webdriver()
        return self.browsers[self.browser_name]

    def get_context_in_use(self) -> BrowserContext:
        if self.browser_name is None or self.contexts[self.browser_name] is None:
            self._setup_default_webdriver()
        return self.contexts[self.browser_name]

    def _setup_default_webdriver(self):
        try:
            if self.default_browser_settings and self.default_browser_settings["browser_name"]:
                self.setup_webdriver(**self.default_browser_settings)
                _exec_logger.debug(f"{self.name} - Started 'Default' {self.browser_name}")
            else:
                raise ValueError("No default browser set!")
        except:
            self.setup_webdriver(**SAFE_BROWSER)
            _exec_logger.debug(f"{self.name} - Started 'Safe' {self.browser_name}")

        return self

    # -----------------------------------------------------------------------------------------------------------------

    def is_browser_setup(self) -> bool:
        if self.browser_name and self.contexts[self.browser_name]:
            return True
        return False

    def is_page_open(self) -> bool:
        return self.page is not None and self.is_browser_setup() and not self.page.is_closed()

    def get_webdriver(self) -> Page:
        return self.page

    def take_screenshot(self, current_test, name_of_file: str = ""):
        self._screenshot_num += 1
        name_of_file = name_of_file or "playwright_screenshot"
        name_of_file = f"{name_of_file}_{self._screenshot_num:03.0f}.png"

        if self.is_page_open():
            self.page.screenshot(path=name_of_file, full_page=True)
            self.rm.copy_file(current_test, orig_filename=name_of_file, delete_source=True)

        return self

    def goto(self, url: str, timeout: float = 20.0):
        if not self.is_page_open():
            return self.new_tab(url, tab_name="__home__")
        self.page.goto(url, timeout=timeout*1000)

        def handle_new_page(page):
            tab_name = page.title()
            self.tabs[tab_name] = page
            self.switch_tab(tab_name)
            page.wait_for_load_state()
        self.get_context_in_use().on("page", handle_new_page)

        return self

    def find_elements(self, selector: str) -> Locator:
        page = self.page
        page.wait_for_load_state()
        for iframe in self.iframes_selectors:
            page = page.frame_locator(iframe)

        return page.locator(selector)

    def find_element(self, selector: str) -> Locator:
        element = self.find_elements(selector)
        if element.count() > 1:
            element = element.first

        return element

    def get_element(self, selector: str, text: str = None, timeout: float = None) -> Locator:
        if timeout is None:
            timeout = 10

        if text:
            text = f"\"{text}\"" if "'" in text else f"'{text}'"
            selector = f"{selector}:text-is({text})"

        element = self.find_element(selector)
        element.wait_for(timeout=timeout*1000, state="attached")

        return element

    def click_and_type(self, selector: str, text_to_send: str, add_enter=True, timeout: float = None):
        element = self.get_element(selector, timeout=timeout)
        element.fill(text_to_send)
        if add_enter:
            element.press("Enter")

        return self

    def click_element(self, selector: str, text: str = None, timeout: float = None, **kwargs):
        self.get_element(selector, text=text, timeout=timeout).click(**kwargs)
        return self

    def new_tab(self, url: str, tab_name: str = "new_tab"):
        if tab_name in self.tabs:
            self.page = self.tabs[tab_name]
            if self.page is None or self.page.is_closed():
                self.page = self.tabs[tab_name] = self.get_context_in_use().new_page()
        else:
            self.page = self.get_context_in_use().new_page()
            self.tabs[tab_name] = self.page

        self.goto(url)

        return self

    def switch_tab(self, tab_name: str = "new_tab"):
        if tab_name in self.tabs:
            self.page = self.tabs[tab_name]
        else:
            self.switch_tab("__home__")

        return self

    def close_tab(self, tab_name: str = "new_tab"):
        if tab_name in self.tabs:
            try:
                self.tabs[tab_name].close()
            except:
                pass
            finally:
                del self.tabs[tab_name]

        return self.switch_tab("__home__")

    def close_page(self):
        try:
            for name, page in self.tabs.items():
                if page is self.page:
                    del self.tabs[name]
                    break
            self.page.close()
        except:
            pass
        finally:
            self.page = None

    def switch_to_frame(self, selector: str):
        self.iframes_selectors.append(selector)
        return self

    def switch_to_previous_frame(self):
        if self.iframes_selectors:
            self.iframes_selectors.pop()
        return self

    def sleep(self, wait_for: float = 0.0):
        if wait_for > 0:
            sleep(wait_for)
        return self

    def execute_script(self, script: str):
        return self.page.evaluate(script)

    def select_by_visible_text(self, text: str, selector=None, timeout: float = None):
        self.get_element(selector, timeout=timeout).select_option(label=text)
        return self

    # div.name-of-class[field='value'] > span.name-of-class[...
    def page_has_element(self, selector: str, text: str = None, timeout: float = None) -> bool:
        if self.get_element(selector, text=text, timeout=timeout).is_visible(timeout=1):
            return True
        return False

    # assure that the element (with text) is not being displayed on the page
    def page_doesnt_has_element(self, selector: str, text: str = None) -> bool:
        try:
            self.page_has_element(selector, text, timeout=1)
        except:
            return True
        return False

    def set_input_file(self, selector: str, filename: str, timeout: float = None, **trash):
        self.get_element(selector, timeout=timeout).set_input_files(files=filename)
        return self

    def get_element_screenshot_as_base64(self, selector: str, timeout: float = None):
        element = self.get_element(selector=selector, timeout=timeout)

        return base64.b64encode(element.screenshot())
