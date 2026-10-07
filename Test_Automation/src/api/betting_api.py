"""Domain layer: the betting endpoints from section 5 of the spec, in business terms."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import Any

import requests

from src.api.api_client import ApiClient
from src.utils.calculations import to_decimal


class Selection(StrEnum):
    """Bet outcomes as the API names them. The UI shows them as 1, X and 2."""

    HOME = "HOME"
    DRAW = "DRAW"
    AWAY = "AWAY"

    @classmethod
    def from_name(cls, name: str) -> Selection:
        """Selection from a readable name such as 'Draw', case-insensitive."""
        try:
            return cls[name.strip().upper()]
        except KeyError:
            options = ", ".join(selection.capitalize() for selection in cls)
            raise ValueError(f"Unknown selection {name!r}, expected one of: {options}") from None


class ApiError(RuntimeError):
    """An endpoint used for setup or reading state did not answer as documented."""


class BettingApi:
    def __init__(self, client: ApiClient) -> None:
        self._client = client

    def get_matches(self) -> list[dict[str, Any]]:
        return _json_body(self._client.get("/matches"))

    def get_balance(self) -> Decimal:
        body = _json_body(self._client.get("/balance"))
        if "balance" not in body:
            raise ApiError(f"GET /balance returned no 'balance' field: {body}")
        return to_decimal(body["balance"])

    def reset_balance(self) -> Decimal:
        """Reset the balance and return the persisted value.

        The value is read back with GET /balance because the reset response body
        does not always match the stored balance.
        """
        _json_body(self._client.post("/reset-balance"))
        return self.get_balance()

    def place_bet(
        self, match_id: str, selection: Selection | str, stake: Decimal | float | str
    ) -> requests.Response:
        """Send a bet as given and return the raw response.

        Accepted and rejected bets are both valid outcomes for a test, so the status code
        and body are left to the caller. Plain strings are allowed for invalid input.
        """
        payload = {"matchId": match_id, "selection": str(selection), "stake": _to_json(stake)}
        return self._client.post("/place-bet", json=payload)


def _json_body(response: requests.Response) -> Any:
    """Return the JSON body of a successful response, or raise ApiError with the details."""
    request = f"{response.request.method} {response.url}"
    if not response.ok:
        raise ApiError(f"{request} -> {response.status_code}: {response.text[:300]}")
    try:
        return response.json()
    except ValueError as error:
        raise ApiError(f"{request} returned a non-JSON body: {response.text[:300]!r}") from error


def _to_json(stake: Decimal | float | str) -> float | str:
    # JSON has no decimal type; float(Decimal("12.34")) serializes as 12.34.
    return float(stake) if isinstance(stake, Decimal) else stake
