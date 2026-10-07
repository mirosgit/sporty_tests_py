"""Step definitions for features/stake_validation.feature."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import requests
from pytest_bdd import parsers, scenarios, then, when

from src.api.betting_api import BettingApi, Selection
from src.utils.calculations import to_decimal

scenarios("stake_validation.feature")


@when(parsers.parse("a bet with stake {stake} is sent to the API"), target_fixture="response")
def send_bet(
    betting_api: BettingApi, upcoming_match: dict[str, Any], stake: str
) -> requests.Response:
    return betting_api.place_bet(upcoming_match["id"], Selection.HOME, _stake_value(stake))


@then(parsers.parse('the response is {status:d} with error "{error}"'))
def response_is_rejected(response: requests.Response, status: int, error: str) -> None:
    assert response.status_code == status, (
        f"expected {status}, got {response.status_code}: {response.text}"
    )
    assert response.json().get("error") == error, response.text


@then("the balance is unchanged")
def balance_is_unchanged(betting_api: BettingApi, start_balance: Decimal) -> None:
    assert betting_api.get_balance() == start_balance


def _stake_value(raw: str) -> Decimal | str:
    """A quoted value is sent as a JSON string, anything else as a number."""
    if raw.startswith('"') and raw.endswith('"'):
        return raw[1:-1]
    return to_decimal(raw)
