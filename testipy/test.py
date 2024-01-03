from playwright.sync_api import sync_playwright
from testipy.lib_modules.common_methods import Timer

# https://playwright.dev/python/docs/api/class-browser#browser-new-context

def log_routes():
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        page = browser.new_page()

        def log_and_continue_request(route, request):
            print(request.url)
            route.continue_()

        # Log and continue all network requests
        page.route("**/*", log_and_continue_request)

        page.goto("https://wikipedia.com")

        dimensions = page.evaluate(
            """() => {
                return {
                    width: document.documentElement.clientWidth,
                    height: document.documentElement.clientHeight,
                    deviceScaleFactor: window.devicePixelRatio}
            }"""
        )
        print(dimensions)

        page.close()
        browser.close()


def context():
    with sync_playwright() as p:
        # show devices
        for d in p.devices:
            print(d)

        browser = p.webkit.launch(headless=False)

        # emulate phone
        phone = p.devices["iPhone 12 Pro landscape"]
        for k, v in phone.items():
            print(k, v)

        context = browser.new_context(
            **phone,
            locale="en-US",
            geolocation={"longitude": 12.492507, "latitude": 41.889938},
            permissions=["geolocation"]
        )
        page = context.new_page()

        page.goto("https://www.whatismybrowser.com/")

        Timer(10).sleep_until_over()
        context.close()
        page.close()



        context = browser.new_context(
            locale="pt-PT"
        )
        page = context.new_page()

        page.goto("https://www.whatismybrowser.com/")

        Timer(10).sleep_until_over()
        context.close()
        page.close()
        browser.close()


def show_devices():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        for i, d in enumerate(p.devices):
            print("-", d)
    print(p.devices["Nexus 10"])


if __name__ == "__main__":
    import sys
    print(sys.version)
    #context()
    show_devices()
