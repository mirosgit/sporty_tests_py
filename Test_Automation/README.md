# Single Bet Placement: Test Automation

UI and API tests for the Single Bet Placement feature of https://qae-assignment-tau.vercel.app.

Stack: Python 3.11+, Pytest, pytest-bdd, Selenium WebDriver (Chrome), requests.

## Architecture

```text
Test_Automation/
├── config/
│   └── settings.py              # settings from .env; DEFAULT_TIMEOUT = 10 s
├── src/
│   ├── api/
│   │   ├── api_client.py        # ApiClient: shared requests.Session, x-user-id, timeout, logging
│   │   └── betting_api.py       # BettingApi: get_matches, get_balance, reset_balance, place_bet
│   ├── pages/
│   │   ├── base_page.py         # BasePage: explicit waits, text and amount reading
│   │   ├── header.py            # Header: balance, shared by every view
│   │   ├── match_list_page.py   # MatchListPage: open the app, select odds
│   │   ├── bet_slip.py          # BetSlip: stake, payout, Place Bet
│   │   └── receipt_modal.py     # ReceiptModal: read and close the receipt
│   └── utils/
│       └── calculations.py      # Decimal money helpers
├── tests/
│   ├── conftest.py              # fixtures, shared steps, screenshots, end-of-run report
│   ├── features/                # Gherkin scenarios
│   ├── ui/                      # UI step definitions
│   └── api/                     # API step definitions
└── artifacts/                   # screenshots and report files (not committed)
```

How a test runs:

```text
.feature scenario → step definitions → page objects (Selenium) / BettingApi → ApiClient (requests)
```

- **BDD.** Scenarios are written in Gherkin in `tests/features`. Steps are thin: each step calls one page object or `BettingApi` method.
- **Page Object Model.** All locators and Selenium calls live in `src/pages`. Tests never use them directly.
- **API layers.** `ApiClient` handles HTTP only. `BettingApi` exposes the endpoints in business terms.
- **Fixtures.** Pytest fixtures in `conftest.py` provide the config, the API client, a new Chrome per test and the page objects.
- **Isolation.** Each test resets the balance before it starts, and test data (the nearest upcoming match) is read from the API.
- **Money as `Decimal`.** Amounts are compared exactly, never as floats.
- **Diagnostics.** A failed UI test saves a screenshot, and every run ends with a test report.

## Setup

Requires Python 3.11+ and Google Chrome.

```bash
cd Test_Automation
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # then set USER_ID in .env
```

| Variable | Required | Description |
|---|---|---|
| `USER_ID` | yes | Your user id, sent as the `x-user-id` header and the `user-id` URL parameter |
| `BASE_URL` | yes | Application URL, already set in `.env.example` |
| `HEADLESS` | no | `true` (default) runs Chrome without a window; `false` shows the browser |

## Running

```bash
pytest                    # all tests
pytest -m ui              # UI tests only
pytest -m api             # API tests only
pytest -k "invalid_stake_max"                # one test case
HEADLESS=false pytest -m ui                  # with a visible browser
pytest -vv --gherkin-terminal-reporter       # show every scenario step
```

Every run ends with a **Test report**: one line per test, and for each failure the failed step, the reason and the screenshot path. Screenshots are saved to `artifacts/screenshots/`, and `junit.xml` and `cucumber.json` to `artifacts/reports/`.

## Covered scenarios

| Feature | Scenario | Checks | Status |
|---|---|---|---|
| `place_bet.feature` (UI) | User places a single bet and the balance is debited | Select an outcome, enter a stake, place the bet; bet slip, receipt, header balance and stored balance are correct | `xfail`: BUG-06, BUG-07, BUG-08 |
| `stake_validation.feature` (API) | API rejects an invalid stake: `0`, `0.99`, `100.01`, `10.555`, `"10"` | `422` with the documented error code; the balance does not change | pass |
| `stake_validation.feature` (API) | API rejects an invalid stake: `-5` | Same as above | `xfail`: BUG-03 |

Cases with known defects are tagged `@xfail` in the feature files, so the current result is `5 passed, 2 xfailed`. Strict mode is on: when a defect is fixed, its test passes, the run fails and asks to remove the tag. Defects are described in the [test execution report](../Test_Execution/test_execution_report.md).
