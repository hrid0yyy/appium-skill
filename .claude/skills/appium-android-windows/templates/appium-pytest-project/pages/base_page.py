"""Base page object shared by Android and Windows pages (platform-agnostic actions only)."""
from __future__ import annotations

import logging

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from core.waits import Locator, Waits


class BasePage:
    def __init__(self, driver: WebDriver, timeout: float):
        self.driver = driver
        self.timeout = timeout
        self.wait = Waits(driver, timeout)
        self.log = logging.getLogger(self.__class__.__name__)

    def find(self, locator: Locator) -> WebElement:
        return self.wait.visible(locator)

    def tap(self, locator: Locator) -> None:
        self.log.debug("click %s", locator)
        self.wait.clickable(locator).click()

    def type_text(self, locator: Locator, text: str) -> None:
        el = self.wait.visible(locator)
        el.clear()
        el.send_keys(text)

    def text_of(self, locator: Locator) -> str:
        return self.wait.visible(locator).text

    def is_displayed(self, locator: Locator) -> bool:
        """Non-throwing presence check (no waiting); use the wait helpers to wait."""
        try:
            return any(e.is_displayed() for e in self.driver.find_elements(*locator))
        except StaleElementReferenceException:  # element re-rendered between find and check
            return False
