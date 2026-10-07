"""Main page: the list of matches with their odds buttons."""

from __future__ import annotations

from decimal import Decimal

from selenium.webdriver.common.by import By

from src.api.betting_api import Selection
from src.pages.base_page import BasePage


class MatchListPage(BasePage):
    MATCH_CARD = (By.CSS_SELECTOR, "#match-list .matchCard")

    def open(self, url: str) -> MatchListPage:
        self._driver.get(url)
        self._visible(self.MATCH_CARD)
        return self

    def odds(self, match_id: str, selection: Selection) -> Decimal:
        button_id = _odds_button_id(match_id, selection)
        return self._number((By.CSS_SELECTOR, f"#{button_id} .oddsButtonValue"))

    def select_odds(self, match_id: str, selection: Selection) -> Decimal:
        """Add the outcome to the bet slip and return the odds shown on its button."""
        odds = self.odds(match_id, selection)
        self._click((By.ID, _odds_button_id(match_id, selection)))
        return odds


def _odds_button_id(match_id: str, selection: Selection) -> str:
    return f"odds-{match_id}-{selection.lower()}"
