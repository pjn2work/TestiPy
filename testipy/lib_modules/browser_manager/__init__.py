from testipy.lib_modules.browser_manager.playwright import PlaywrightController
# from lib_modules.browser_manager.selenium import SeleniumController


class BrowserManager(PlaywrightController):

    def __init__(self, rm):
        super().__init__(rm)
