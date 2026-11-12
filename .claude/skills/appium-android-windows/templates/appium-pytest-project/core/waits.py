"""Explicit-wait helpers. The only sanctioned way to wait. Never time.sleep()."""
from __future__ import annotations

from typing import Callable, TypeVar

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

Locator = tuple[str, str]
T = TypeVar("T")


class Waits:
    def __init__(self, driver: WebDriver, timeout: float, poll: float = 0.25):
        self._driver = driver
        self._timeout = timeout
        self._poll = poll

    def _wait(self, timeout: float | None = None) -> WebDriverWait:
        return WebDriverWait(self._driver, timeout or self._timeout, poll_frequency=self._poll)

    def present(self, locator: Locator, timeout: float | None = None) -> WebElement:
        return self._wait(timeout).until(EC.presence_of_element_located(locator), f"not present: {locator}")

    def visible(self, locator: Locator, timeout: float | None = None) -> WebElement:
        return self._wait(timeout).until(EC.visibility_of_element_located(locator), f"not visible: {locator}")

    def clickable(self, locator: Locator, timeout: float | None = None) -> WebElement:
        return self._wait(timeout).until(EC.element_to_be_clickable(locator), f"not clickable: {locator}")

    def gone(self, locator: Locator, timeout: float | None = None) -> bool:
        return self._wait(timeout).until(EC.invisibility_of_element_located(locator), f"still visible: {locator}")

    def until(self, condition: Callable[[WebDriver], T], message: str = "", timeout: float | None = None) -> T:
        """Wait for any custom condition, e.g. lambda d: d.query_app_state(pkg) == 4."""
        return self._wait(timeout).until(condition, message)
