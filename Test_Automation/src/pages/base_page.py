"""Explicit-wait helpers shared by the page objects."""

from __future__ import annotations

import re
from collections.abc import Callable
from contextlib import suppress
from decimal import Decimal

from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from src.utils.calculations import to_decimal

Locator = tuple[str, str]

_EURO_AMOUNT = re.compile(r"€\s*(-?[\d,]+(?:\.\d+)?)")


class BasePage:
    def __init__(self, driver: WebDriver, timeout: float) -> None:
        self._driver = driver
        self._timeout = timeout

    def _wait(self, timeout: float | None = None) -> WebDriverWait:
        # The app re-renders often, so a stale element is retried instead of failing the wait.
        return WebDriverWait(
            self._driver,
            self._timeout if timeout is None else timeout,
            ignored_exceptions=[StaleElementReferenceException],
        )

    def _visible(self, locator: Locator, timeout: float | None = None) -> WebElement:
        return self._wait(timeout).until(
            ec.visibility_of_element_located(locator),
            f"Element {locator} is not visible",
        )

    def _click(self, locator: Locator) -> None:
        element = self._wait().until(
            ec.element_to_be_clickable(locator),
            f"Element {locator} is not clickable",
        )
        # Centre the element first, so the fixed header cannot cover it.
        self._driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        element.click()

    def _type(self, locator: Locator, text: str) -> None:
        element = self._visible(locator)
        element.clear()
        element.send_keys(text)

    def _text(self, locator: Locator) -> str:
        """Visible text of the element, read again if the app re-renders it meanwhile."""

        def visible_text(driver: WebDriver) -> tuple[str] | None:
            element = driver.find_element(*locator)
            # Wrapped in a tuple, so an empty text still ends the wait.
            return (element.text.strip(),) if element.is_displayed() else None

        (text,) = self._wait().until(visible_text, f"Element {locator} is not visible")
        return text

    def _number(self, locator: Locator) -> Decimal:
        """Read a plain number such as odds '3.70'."""
        return to_decimal(self._text(locator))

    def _amount(self, locator: Locator) -> Decimal:
        """Read a euro amount such as '€45.66' or 'Balance: €-80.00'."""
        text = self._text(locator)
        match = _EURO_AMOUNT.search(text)
        if match is None:
            raise ValueError(f"No euro amount in {text!r} at {locator}")
        return Decimal(match.group(1).replace(",", ""))

    def _is_displayed(self, locator: Locator, timeout: float | None = None) -> bool:
        try:
            self._visible(locator, timeout)
        except TimeoutException:
            return False
        return True

    def _is_enabled(self, locator: Locator) -> bool:
        return self._visible(locator).is_enabled()

    def _wait_until_hidden(self, locator: Locator) -> None:
        self._wait().until(
            ec.invisibility_of_element_located(locator),
            f"Element {locator} is still visible",
        )

    def _text_when(self, locator: Locator, condition: Callable[[str], bool]) -> str:
        """Wait until the element text meets `condition` and return the last text seen.

        It does not raise on timeout: the test asserts on the returned value, so a failure
        shows what the UI displayed instead of a bare TimeoutException.
        """
        last_text = ""

        def text_matches(driver: WebDriver) -> bool:
            nonlocal last_text
            last_text = driver.find_element(*locator).text.strip()
            return condition(last_text)

        with suppress(TimeoutException):
            self._wait().until(text_matches)
        return last_text
