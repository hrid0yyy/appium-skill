"""Page objects for the official Appium ApiDemos app (io.appium.android.apis).

Locator notes (verified against the ApiDemos-debug.apk shipped in the `android-apidemos`
npm package): the home list uses SimpleAdapterWithDesc, which sets each row's
content-desc to its label, so accessibility ids ("Views", "App", ...) work.
"""
from __future__ import annotations

from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage


class ApiDemosHomePage(BasePage):
    VIEWS = (AppiumBy.ACCESSIBILITY_ID, "Views")
    APP = (AppiumBy.ACCESSIBILITY_ID, "App")

    def wait_until_loaded(self) -> "ApiDemosHomePage":
        self.wait.visible(self.VIEWS)
        return self

    def open_views(self) -> "ViewsPage":
        self.tap(self.VIEWS)
        return ViewsPage(self.driver, self.timeout).wait_until_loaded()


class ViewsPage(BasePage):
    # Each Views sub-demo row also carries a content-desc equal to its label.
    ANIMATION = (AppiumBy.ACCESSIBILITY_ID, "Animation")

    def wait_until_loaded(self) -> "ViewsPage":
        self.wait.visible(self.ANIMATION)
        return self

    def scroll_to(self, label: str) -> None:
        """Scroll the list until a row with this content-desc is visible (no sleeps)."""
        self.driver.execute_script(
            "mobile: scroll",
            {"strategy": "accessibility id", "selector": label, "maxSwipes": 15},
        )
        self.wait.visible((AppiumBy.ACCESSIBILITY_ID, label))
