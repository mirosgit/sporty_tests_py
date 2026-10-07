# Test Plan: Single Bet Placement

**Risk assessment:** Product risk is evaluated based on Impact × Likelihood.

**Test priority:** Priority is assigned based primarily on the resulting product risk and business criticality:
- **Critical** - very high business/financial impact and high overall risk
- **High** - high overall risk or significant business impact
- **Medium** - moderate risk and/or limited business impact
- **Low** - low likelihood and low impact

### TC-01: Place a valid single bet end-to-end; payout, receipt and balance are correct and persisted

**Priority:** Critical

**Risk rationale:** **High - High impact / Medium likelihood.** Failure would block the primary bet placement flow and directly affect revenue, while an incorrect debit, payout or persisted balance would cause financial discrepancies and customer disputes. The flow spans multiple UI and API representations of the same financial data, increasing the risk of state and calculation inconsistencies.

**Preconditions:** Balance reset (`POST /api/reset-balance`) and the current balance from `GET /api/balance` noted as the **start balance** (must be at least €12.34). Bet slip is empty.

**Test data:**
- Match: any upcoming match from the list (kickoff time is in the future). Selection: **Draw** (button **X**), so the UI choice is checked against the API value `DRAW`. Stake: **€12.34**.
- **Expected payout** = 12.34 × odds.

**Steps**
1. Open `https://qae-assignment-tau.vercel.app/?user-id=<user_id>` in desktop Chrome and open DevTools on the **Network** tab.
2. Pick any upcoming match and click **Draw**. Note the match name and the odds.
3. Enter stake `12.34`.
4. Click **Place Bet** and watch the button.
5. In the Network tab, open the `POST /api/place-bet` request sent by the click in step 4 and inspect the request and response.
6. Review the success receipt.
7. Close the receipt.
8. Reload the page and call `GET /api/balance`.

**Expected result**
- Step 2: the slip shows the chosen match and selection **Draw** with the same odds as on the button. Only this odds button is highlighted.
- Step 3: the slip shows stake **€12.34**, available balance equal to the **start balance**, and potential payout equal to the **expected payout**.
- Step 4: the button changes to **Placing...** and remains disabled until the request completes. Only one bet submission is processed.
- Step 5:
  - `POST /api/place-bet` request body is `{"matchId":"<id of the chosen match>","selection":"DRAW","stake":12.34}` and carries the `x-user-id` header.
  - `POST /api/place-bet` response is `200` with every field from 5.3:
    ```json
    {
      "message": "Bet placed successfully",
      "matchId": "<id of the chosen match>",
      "selection": "DRAW",
      "stake": 12.34,
      "odds": <odds noted in step 2>,
      "payout": <expected payout>,
      "balance": <start balance − 12.34>,
      "currency": "EUR"
    }
    ```
- Step 6: the receipt matches the slip and the API response from step 5:
  - **Bet ID**: non-empty (the API response has no bet ID field)
  - **Match**: the chosen match, home vs away team (`matchId`)
  - **Selection**: Draw (`selection: "DRAW"`)
  - **Stake**: €12.34 (`stake`)
  - **Odds**: the odds noted in step 2 (`odds`)
  - **Potential payout**: the expected payout (`payout`)
  - **Placement timestamp**: the current local time within an acceptable tolerance (not in the API response)
- Step 7: the user is back on the match list. The slip is empty, the stake is cleared, no odds button is highlighted, and the balance shows **start balance − €12.34**.
- Step 8: the balance is still **start balance − €12.34** after reload and from the API, so the debit was persisted and not only shown in the UI.

---

### TC-02: A bet on a past-dated match is rejected 

**Priority:** Critical

**Risk rationale:** **High - High impact / Medium likelihood.** Accepting bets on past events could allow users to wager after the outcome is already known, causing direct financial loss and compromising betting integrity. The specification limits betting to upcoming/pre-match events, while 4.2 requires only that the match ID exists and does not explicitly define server-side validation of the match date.

**Preconditions:** Balance is reset and the current balance is noted as the **start balance**. A valid `x-user-id` is available.

**Test data:** any match with `kickoffDate` < today, selection **Home** (button **1**), stake **€1.00**. If no past-dated match exists in the catalog, the placement part of this scenario is blocked due to unavailable test data.

**Steps**
1. Call `GET /api/matches` and compare each returned `kickoffDate` with today's date. Also check the match list in the UI.
2. If a past-dated match is exposed as bettable, select **Home**, enter €1.00, and click **Place Bet**.
3. Send the same bet directly to `POST /api/place-bet` with a valid `x-user-id`:
   ```json
   {
     "matchId": "<id of the past-dated match>",
     "selection": "HOME",
     "stake": 1
   }
   ```
4. Call `GET /api/balance`.

**Expected result**
- Step 1: `GET /api/matches` and the UI expose only matches with `kickoffDate` >= today. Past-dated matches are not available for betting.
- Step 2: if a past-dated match is incorrectly exposed in the UI, bet placement is rejected, no success receipt is displayed, and no bet is created.
- Step 3: the API rejects the bet with HTTP `422` as a semantic match validation failure:
  ```json
  {
    "error": "invalid_match_id",
    "message": "Match id is invalid."
  }
  ```
- Step 4: the balance remains equal to the **start balance**, confirming that no stake was deducted.

---

### TC-03: Stake above the available balance is rejected, stake equal to the balance is accepted

**Priority:** Critical

**Risk rationale:** **High - High impact / Medium likelihood.** Accepting a stake greater than the available balance could create unfunded bets, negative balances, and inconsistent financial state. The exact-balance boundary is also financially sensitive because a successful bet must reduce the balance to exactly zero without calculation or state inconsistencies.

**Preconditions:** Reset the balance, then place one bet so that the available balance is between €1.00 and €100.00 (below €100.00, so the maximum-stake rule does not interfere with the balance validation). Note this balance as the **start balance**. A valid `x-user-id` is available and at least one upcoming match can be selected.

**Steps**
1. Select any upcoming match and enter a stake of **start balance + €0.01**. Note the match `id` from `GET /api/matches`.
2. Send the same bet directly to `POST /api/place-bet` with a valid `x-user-id`, then call `GET /api/balance`:
   ```json
   {
     "matchId": "<id of the match selected in step 1>",
     "selection": "HOME",
     "stake": <start balance + 0.01>
   }
   ```
3. Enter a stake equal to the **start balance** and click **Place Bet**.
4. Verify the success receipt, close it, and check the balance in the UI and via `GET /api/balance`.
5. Select another upcoming match. With the balance now at zero, enter stake `1.00` and attempt placement in the UI. Send the same request directly to the API, with the `id` of this match and `"stake": 1`.

**Expected result**
- Step 1: the UI shows "Insufficient balance" and placement is blocked.
- Step 2: the API rejects the request with HTTP `422` and an insufficient-balance error body (values from the OpenAPI `Error` schema example):
  ```json
  {
    "error": "insufficient_balance",
    "message": "Insufficient balance"
  }
  ```
  The balance remains equal to the **start balance**.
- Step 3: the bet succeeds because a stake equal to the available balance is valid. The receipt shows a stake equal to the **start balance**.
- Step 4: after the receipt is closed, the available balance is exactly **€0.00** in the UI and `0` in `GET /api/balance`. No negative balance, `-0.00`, or floating-point residue is exposed.
- Step 5: the UI shows "Insufficient balance" and blocks placement. The API returns the same `422` response as in step 2, and the balance remains 0.

---

### TC-04: Parallel placement requests for the same user create exactly one bet and one debit

**Priority:** Critical

**Risk rationale:** **High - High impact / Medium likelihood.** Concurrent submissions from the same user, such as a double-click, retry, or requests from multiple tabs, could create duplicate bets and duplicate debits, leaving the user's balance and betting state inconsistent. The specification explicitly defines `409 bet already in progress` for the same user, so correct concurrency control is required to prevent race-condition defects.

**Preconditions:** Balance is reset and noted as the **start balance**. The available balance is at least €60.00 (5 × €10.00 if every concurrent request were wrongly accepted, plus €10.00 for step 3), so the insufficient-balance rule cannot mask a duplicate debit. A valid `x-user-id` is available.

**Test data:** any upcoming match from `GET /api/matches` (its id is `<matchId>` below), selection **HOME**, stake **€10.00**.

**Steps**
1. Send 5 identical `POST /api/place-bet` requests concurrently for the same user, starting them as close to simultaneously as possible, and record every response status. Example:
   ```bash
   for i in 1 2 3 4 5; do
     curl -s -w " [%{http_code}]\n" \
       -X POST "https://qae-assignment-tau.vercel.app/api/place-bet" \
       -H "x-user-id: <user_id>" \
       -H "Content-Type: application/json" \
       -d '{"matchId":"<matchId>","selection":"HOME","stake":10}' &
   done
   wait
   ```
2. Call `GET /api/balance`.
3. After all concurrent requests have completed, send the same valid request once more.
4. Call `GET /api/balance` again.

**Expected result**
- Step 1: exactly one concurrent request returns `200`. All other overlapping requests return `409` (bet already in progress). No additional bet is successfully processed.
- Step 2: the balance equals **start balance − €10.00**. The financial invariant is that the balance decreases by exactly €10.00 for each successful `200` response and is never debited for rejected `409` requests.
- Step 3: the subsequent request returns `200`, confirming that the in-progress lock was released after the previous placement completed.
- Step 4: the balance equals **start balance − €20.00**, confirming exactly two successful debits in total.

---

### TC-05: Stake amount boundaries are enforced consistently in the UI and API

**Priority:** High

**Risk rationale:** **High - Medium impact / High likelihood.** Incorrect handling of stake boundaries could allow values outside the permitted business limits or reject valid bets. The specification contains conflicting minimum-stake requirements (€1.00 in sections 3 and 4.4 versus €1.01 in section 4.1), creating a high likelihood of inconsistent UI and API validation.

**Preconditions:** A valid upcoming match is available; its id from `GET /api/matches` is used as `<matchId>` below. The balance after reset is at least €100.00. A valid `x-user-id` is available.

**Steps** (repeat independently for each test-data row)
1. Reset the balance and select **Home** on the test match.
2. Enter the stake in the UI. Record the validation message and whether **Place Bet** is enabled. If placement is allowed, submit the bet and check the balance via `GET /api/balance`.
3. Reset the balance again and send the same stake directly to `POST /api/place-bet` for the same match. Example:
   ```bash
   curl -s -X POST "https://qae-assignment-tau.vercel.app/api/place-bet" \
     -H "x-user-id: <user_id>" -H "Content-Type: application/json" \
     -d '{"matchId":"<matchId>","selection":"HOME","stake":<value>}'
   ```
4. Call `GET /api/balance` and verify whether the balance changed.

**Test data and expected result**

| # | Stake | Boundary | UI expected | API expected |
|---|---|---|---|---|
| 1 | `0` | Zero | "Minimum stake is €1.00", placement blocked | `422` `invalid_stake_min` |
| 2 | `0.99` | Min − €0.01 | "Minimum stake is €1.00", placement blocked | `422` `invalid_stake_min` |
| 3 | `1.00` | Conflicting minimum | Requirement clarification required: sections 3, 4.4 and the OpenAPI (`minimum: 1`) imply €1.00 is valid, while section 4.1 defines €1.01 as the minimum | Requirement clarification required |
| 4 | `1.01` | Explicit minimum in section 4.1 | Accepted | `200` |
| 5 | `99.99` | Max − €0.01 | Accepted | `200` |
| 6 | `100.00` | Max | Accepted | `200` |
| 7 | `100.01` | Max + €0.01 | "Maximum stake is €100.00", placement blocked | `422` `invalid_stake_max` |

Error bodies for rejected rows, from the OpenAPI `422` examples:
```json
{ "error": "invalid_stake_min", "message": "Stake must be at least 1.00." }
{ "error": "invalid_stake_max", "message": "Stake must be at most 100.00." }
```

**Overall expected result**
- UI and API apply the same confirmed stake boundaries.
- Rejected stakes do not change the balance.
- Accepted stakes debit exactly the submitted amount.
- No value above €100.00 is accepted.
- The conflicting €1.00 / €1.01 minimum must be clarified before the €1.00 boundary can receive a definitive pass/fail result.
