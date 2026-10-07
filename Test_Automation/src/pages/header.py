"""App header, shown on every view: the account balance."""

from __future__ import annotations

from decimal import Decimal

from selenium.webdriver.common.by import By

from src.pages.base_page import BasePage


class Header(BasePage):
    BALANCE = (By.ID, "header-balance")

    def balance(self) -> Decimal:
        return self._amount(self.BALANCE)

    def wait_for_balance(self, expected: Decimal) -> Decimal:
        """Give the header time to refresh and return the balance it shows."""
        self._text_when(self.BALANCE, lambda text: f"€{expected:.2f}" in text)
        return self.balance()
