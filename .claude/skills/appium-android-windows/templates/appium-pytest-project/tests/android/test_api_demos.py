"""Sample Android test: official Appium ApiDemos app via UiAutomator2.

Run:  pytest -m android
Needs: ANDROID_APP (path to ApiDemos-debug.apk) or the app pre-installed, plus
       ANDROID_UDID or ANDROID_AVD (or exactly one device in `adb devices`).
"""
import pytest
from appium.webdriver.common.appiumby import AppiumBy

from pages.android.api_demos_page import ApiDemosHomePage

@pytest.mark.android
def test_open_views_and_scroll_to_webview(driver, settings):
    home = ApiDemosHomePage(driver, settings.explicit_wait).wait_until_loaded()

    views = home.open_views()
    views.scroll_to("WebView")

    assert views.is_displayed((AppiumBy.ACCESSIBILITY_ID, "WebView"))


@pytest.mark.android
def test_app_is_in_foreground(driver, settings):
    ApiDemosHomePage(driver, settings.explicit_wait).wait_until_loaded()
    # 4 == running in foreground (UiAutomator2 queryAppState contract)
    package = settings.android_app_package or driver.current_package
    assert driver.query_app_state(package) == 4
