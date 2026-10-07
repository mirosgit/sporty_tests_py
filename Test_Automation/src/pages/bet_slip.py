"""Right-side bet slip: the selected outcome, stake input, totals and Place Bet."""

from __future__ import annotations

from decimal import Decimal

from selenium.webdriver.common.by import By

from src.pages.base_page import BasePage


class BetSlip(BasePage):
    SELECTED_MATCH = (By.CSS_SELECTOR, "#bet-slip .betSelectionTeams")
    SELECTED_MARKET = (By.CSS_SELECTOR, "#bet-slip .betSelectionMarket")
    STAKE_INPUT = (By.ID, "bet-slip-stake-input")
    VALIDATION_MESSAGE = (
        By.CSS_SELECTOR,
        "#bet-slip .stakeWarning > span:not(.stakeWarningIcon)",
    )
    TOTAL_STAKE = (By.ID, "bet-slip-total-stake")
    POTENTIAL_PAYOUT = (By.ID, "bet-slip-potential-payout")
    PLACE_BET_BUTTON = (By.ID, "bet-slip-place-bet")
    REMOVE_ALL_BUTTON = (By.ID, "bet-slip-remove-all")
    EMPTY_STATE = (
        By.XPATH,
        "//*[@id='bet-slip']//*[normalize-space()='Select odds to place a bet']",
    )

    def selected_match(self) -> str:
        return self._text(self.SELECTED_MATCH)

    def selected_market(self) -> str:
        return self._text(self.SELECTED_MARKET)

    def enter_stake(self, stake: Decimal | str) -> None:
        """Type the stake. A string is typed as is, which allows invalid input."""
        text = f"{stake:.2f}" if isinstance(stake, Decimal) else stake
        self._type(self.STAKE_INPUT, text)

    def validation_message(self) -> str | None:
        if not self._is_displayed(self.VALIDATION_MESSAGE, timeout=1):
            return None
        return self._text(self.VALIDATION_MESSAGE)

    def total_stake(self) -> Decimal:
        return self._amount(self.TOTAL_STAKE)

    def potential_payout(self) -> Decimal:
        return self._amount(self.POTENTIAL_PAYOUT)

    def can_place_bet(self) -> bool:
        return self._is_enabled(self.PLACE_BET_BUTTON)

    def place_bet(self) -> None:
        self._click(self.PLACE_BET_BUTTON)

    def place_bet_label(self) -> str:
        return self._text(self.PLACE_BET_BUTTON)

    def remove_all(self) -> None:
        self._click(self.REMOVE_ALL_BUTTON)

    def is_empty(self) -> bool:
        return self._is_displayed(self.EMPTY_STATE)
