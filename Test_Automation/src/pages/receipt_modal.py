"""Success receipt shown after a bet is placed (section 2.4)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from selenium.webdriver.common.by import By

from src.pages.base_page import BasePage, Locator


@dataclass(frozen=True)
class Receipt:
    bet_id: str
    match: str
    selection: str | None
    stake: Decimal
    odds: Decimal
    potential_payout: Decimal
    placed_at: str


class ReceiptModal(BasePage):
    ROOT = (By.ID, "modal-success")
    BET_ID = (By.ID, "modal-success-bet-id")
    MATCH = (By.ID, "modal-success-match")
    # The receipt has no id for the selection, so it is found by its label.
    SELECTION = (
        By.XPATH,
        "//*[@id='modal-success']//*[normalize-space()='Selection']/following-sibling::*[1]",
    )
    STAKE = (By.ID, "modal-success-stake")
    ODDS = (By.ID, "modal-success-odds")
    POTENTIAL_PAYOUT = (By.ID, "modal-success-payout")
    PLACED_AT = (By.ID, "modal-success-placed-at")
    CLOSE_BUTTON = (By.ID, "modal-success-close")

    def is_open(self) -> bool:
        return self._is_displayed(self.ROOT)

    def read(self) -> Receipt:
        self._visible(self.ROOT)
        return Receipt(
            bet_id=self._text(self.BET_ID),
            match=self._text(self.MATCH),
            selection=self._optional_text(self.SELECTION),
            stake=self._amount(self.STAKE),
            odds=self._number(self.ODDS),
            potential_payout=self._amount(self.POTENTIAL_PAYOUT),
            placed_at=self._text(self.PLACED_AT),
        )

    def close(self) -> None:
        self._click(self.CLOSE_BUTTON)
        self._wait_until_hidden(self.ROOT)

    def _optional_text(self, locator: Locator) -> str | None:
        """Text of a field the receipt may not show; None when it is absent."""
        elements = self._driver.find_elements(*locator)
        return elements[0].text.strip() if elements else None
