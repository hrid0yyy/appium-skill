"""Page object for Windows Calculator (UWP, AUMID Microsoft.WindowsCalculator_8wekyb3d8bbwe!App).

All locators use AutomationId (accessibility id) because AutomationIds are not
localized, while Name values ("Seven", "Plus") change with the OS display language.
Ids verified against Microsoft's open-source Calculator XAML (microsoft/calculator) and
its UI test framework. Confirm with Inspect.exe / Accessibility Insights if the Store build changes.

Calculator remembers the last-used mode across launches; the operator ids below only
exist in Standard/Scientific mode, so wait_until_loaded() forces Standard mode.
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
    NAV_TOGGLE = (AppiumBy.ACCESSIBILITY_ID, "TogglePaneButton")
    NAV_STANDARD = (AppiumBy.ACCESSIBILITY_ID, "Standard")

    _OPS = {"+": PLUS, "-": MINUS, "*": MULTIPLY}

    @staticmethod
    def digit(d: int) -> tuple[str, str]:
        return (AppiumBy.ACCESSIBILITY_ID, f"num{d}Button")

    def wait_until_loaded(self) -> "CalculatorPage":
        self.wait.visible(self.RESULTS)
        self.ensure_standard_mode()
        return self

    def ensure_standard_mode(self) -> None:
        """Switch to Standard mode unless its buttons are already there.

        Locale-independent: checks for the plusButton AutomationId instead of reading
        the (localized) Header text. Same navigation path Microsoft's own tests use.
        """
        if self.is_displayed(self.PLUS) and self.is_displayed(self.CLEAR):
            return
        self.tap(self.NAV_TOGGLE)
        self.tap(self.NAV_STANDARD)
        self.wait.visible(self.PLUS)

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

    def _read_result(self) -> str:
        """Single non-waiting read. The Name is e.g. 'Display is 1,234' (en-US); strip
        the prefix, invisible direction marks and digit-group separators."""
        raw = self.driver.find_element(*self.RESULTS).text
        raw = re.sub(r"[\u200e\u200f\u202a-\u202e]", "", raw)
        match = re.search(r"-?[\d.,\s\u00a0\u202f]*\d", raw)
        if not match:
            return raw.strip()
        return re.sub(r"[,\s\u00a0\u202f]", "", match.group(0))

    def result(self) -> str:
        self.wait.visible(self.RESULTS)
        return self._read_result()

    def wait_for_result(self, expected: str) -> str:
        # One flat wait; stale/missing elements are retried by Waits (no nested waits).
        self.wait.until(lambda _d: self._read_result() == expected,
                        message=f"Calculator display never showed {expected!r}")
        return self._read_result()
