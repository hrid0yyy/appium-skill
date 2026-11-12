"""Sample Windows test: built-in Calculator (UWP) via the Appium Windows driver.

Run:  pytest -m windows
Needs: Developer Mode on, WinAppDriver installed (`appium driver run windows install-wad`),
       WINDOWS_APP=Microsoft.WindowsCalculator_8wekyb3d8bbwe!App (default in .env.example).
"""
import pytest

from pages.windows.calculator_page import CalculatorPage


@pytest.fixture
def calculator(driver, settings) -> CalculatorPage:
    page = CalculatorPage(driver, settings.explicit_wait).wait_until_loaded()
    page.clear()
    return page


@pytest.mark.windows
def test_addition(calculator):
    calculator.calculate(1, "+", 2)
    assert calculator.wait_for_result("3") == "3"


@pytest.mark.windows
@pytest.mark.parametrize("a, op, b, expected", [(9, "-", 4, "5"), (6, "*", 7, "42")])
def test_basic_operations(calculator, a, op, b, expected):
    calculator.calculate(a, op, b)
    assert calculator.wait_for_result(expected) == expected
