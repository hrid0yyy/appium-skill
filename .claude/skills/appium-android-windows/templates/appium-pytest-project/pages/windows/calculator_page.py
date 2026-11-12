"""Page object for Windows Calculator (UWP, AUMID Microsoft.WindowsCalculator_8wekyb3d8bbwe!App).

All locators use AutomationId (accessibility id) because AutomationIds are not
localized, while Name values ("Seven", "Plus") change with the OS display language.
Confirm with Inspect.exe / Accessibility Insights if Microsoft updates the app.
"""
from __future__ import annotations

import re

from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage


class CalculatorPage(BasePage):
    RESULTS = (AppiumBy.ACCESSIBILITY_ID, "CalculatorResults")
    CLEAR = (AppiumBy.ACCESSIBILITY_ID, "clearButton")
    PLUS = (AppiumBy.ACCESSIBILITY_ID, "plusButton")
    MINUS = (AppiumBy.ACCESSIBILITY_ID, "minusButton")
    MULTIPLY = (AppiumBy.ACCESSIBILITY_ID, "multiplyButton")
    EQUALS = (AppiumBy.ACCESSIBILITY_ID, "equalButton")

    _OPS = {"+": PLUS, "-": MINUS, "*": MULTIPLY}

    @staticmethod
    def digit(d: int) -> tuple[str, str]:
        return (AppiumBy.ACCESSIBILITY_ID, f"num{d}Button")

    def wait_until_loaded(self) -> "CalculatorPage":
        self.wait.visible(self.RESULTS)
        return self

    def clear(self) -> None:
        self.tap(self.CLEAR)

    def enter_number(self, number: int) -> None:
        for ch in str(number):
            self.tap(self.digit(int(ch)))

    def calculate(self, a: int, op: str, b: int) -> None:
        self.enter_number(a)
        self.tap(self._OPS[op])
        self.enter_number(b)
        self.tap(self.EQUALS)

    def result(self) -> str:
        """The display's Name is e.g. 'Display is 3'; return just the number part."""
        raw = self.text_of(self.RESULTS)
        match = re.search(r"-?[\d.,]+\s*$", raw)
        return match.group(0).strip() if match else raw

    def wait_for_result(self, expected: str) -> str:
        self.wait.until(lambda _d: self.result() == expected,
                        message=f"Calculator display never showed {expected!r}")
        return self.result()
