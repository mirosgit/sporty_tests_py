# Test Execution Report: Single Bet Placement

| | |
|---|---|
| Application | `https://qae-assignment-tau.vercel.app/?user-id=<user_id>` |
| API | `https://qae-assignment-tau.vercel.app/api` |

## Execution summary

| Scenario | Result | Defects |
|---|---|---|
| TC-01: Place a valid single bet end-to-end | **Fail** | BUG-04, BUG-05, BUG-06, BUG-07, BUG-08, BUG-09, BUG-10 |
| TC-02: A bet on a past-dated match is rejected | **Fail** | BUG-01 |
| TC-03: Stake above the available balance is rejected | **Fail** | BUG-02 |

## Defects

| ID | Title | Severity |
|---|---|---|
| BUG-01 | Bets on past-dated matches are accepted | Critical |
| BUG-02 | API accepts a stake above the available n balance-balance goes negative | Critical |
| BUG-03 | Negative stake is accepted and credited to the balance | Critical |
| BUG-04 | Double-click on Place Bet places the bet twice | Critical |
| BUG-05 | Balance in the UI is not updated after a successful bet | High |
| BUG-06 | Receipt shows a wrong potential payout | High |
| BUG-07 | Receipt shows home and away teams swapped | Medium |
| BUG-08 | Receipt does not show the selection | Medium |
| BUG-09 | API payout is €0.01 lower than stake × odds | High |
| BUG-10 | Place-bet response returns currency USD | Medium |

---

### BUG-01: Bets on past-dated matches are accepted

**Severity:** Critical

**Reproduction Steps**
1. Reset the balance and open the application.
2. In the "Upcoming Football Matches" list, find any match with a **PAST** badge (kickoff date before today).
3. Click any odds button on it, enter a valid stake and click **Place Bet**.
4. Send the same bet directly to the API:
   ```json
   POST /api/place-bet
   {"matchId":"<id of a past-dated match>","selection":"HOME","stake":1}
   ```
5. Call `GET /api/balance`.

**Expected Result:** past-dated matches are not offered for betting, placement is rejected with `422`, the balance does not change

**Actual Result:** past-dated matches are listed with active odds buttons. The UI shows "Bet Placed Successfully!", the API returns `200 "Bet placed successfully"` and the stake is debited.

**Business Impact:** users can place bets after an event outcome may already be known, creating an exploitable betting-integrity issue and direct financial exposure for the operator.

**Evidence:** [`tc02_1_past_matches_listed.png`](evidence/tc02_1_past_matches_listed.png), [`tc02_3_past_match_receipt.png`](evidence/tc02_3_past_match_receipt.png) (Manchester Utd vs Chelsea, kickoff 2026-02-27: balance 120 → 119)

---

### BUG-02: API accepts a stake above the available balance n balance goes negative

**Severity:** Critical

**Reproduction Steps**
1. Reset the balance and place one bet, so the balance is below €100.00 (the maximum stake).
2. Send `POST /api/place-bet` for any upcoming match with a stake of **balance + €0.01**.
3. Call `GET /api/balance`.

**Expected Result:** the bet is rejected with HTTP `422` as a semantic stake validation failure, the balance does not change

**Actual Result:** `200 "Bet placed successfully"`, and the balance becomes negative.

**Business Impact:** users can place bets with money they do not have, creating unfunded bets and a negative balance.

**Evidence:** API response with a balance of €90.00 and a stake of €90.01:
```json
{"message":"Bet placed successfully","matchId":"eredivisie-feyenoord-psv-2026-10-18","selection":"HOME","stake":90.01,"odds":2.55,"payout":229.52,"balance":-0.01,"currency":"USD"}
```
 ([`explore_ui_overdraft_after_reload.png`](evidence/explore_ui_overdraft_after_reload.png)).

---

### BUG-03: Negative stake is accepted and credited to the balance

**Severity:** Critical

**Reproduction Steps**
1. Reset the balance.
2. Send `POST /api/place-bet` for any upcoming match with a negative stake:
   ```json
   {"matchId":"<id of an upcoming match>","selection":"HOME","stake":-50}
   ```
3. Call `GET /api/balance`.

**Expected Result:** the bet is rejected with HTTP `422` as a semantic validation failure (the OpenAPI documents this case as `invalid_stake_min`). The balance does not change

**Actual Result:** `200 "Bet placed successfully"` with a negative payout, and the balance **increases** by the stake amount.

**Business Impact:** a user can artificially increase their balance by submitting negative stakes, violating financial integrity and potentially enabling unlimited balance manipulation.

**Evidence:** stake -50, balance 120 → 170:
```json
{"message":"Bet placed successfully","matchId":"mls-atlanta-seattle-2026-10-28","selection":"HOME","stake":-50,"odds":2.65,"payout":-132.5,"balance":170,"currency":"USD"}
```

---

### BUG-04: Double-click on Place Bet places the bet twice

**Severity:** Critical

**Reproduction Steps**
1. Reset the balance and open the application.
2. Select any outcome on any upcoming match and enter a valid stake.
3. Click **Place Bet**.
4. Click **Place Bet** again while it shows **PLACING...**.
5. Call `GET /api/balance`.

**Expected Result:** while placement is in progress, duplicate submission is prevented. Only one bet is created and the stake is debited once

**Actual Result:** during PLACING... the button remains enabled (`disabled=false`). The second click triggers another `POST /api/place-bet`, both requests return `200`, creating two bets and debiting the stake twice.

**Business Impact:** a common user action creates duplicate bets and double charges, leading to refunds and complaints.

**Evidence:** [`explore_double_click.png`](evidence/explore_double_click.png). Stake €10: two `200` responses with `"balance":110` and `"balance":100`.

---

### BUG-05: Balance in the UI is not updated after a successful bet

**Severity:** High

**Reproduction Steps**
1. Reset the balance, open the application and note the balance in the header.
2. Place a bet on any upcoming match with any valid stake.
3. Close the receipt.
4. Call `GET /api/balance`.
5. Reload the page.

**Expected Result:** after step 3 the header and the bet slip show **starting balance − stake** .

**Actual Result:** after step 3 the header and the bet slip still show the starting balance, while `GET /api/balance` already returns the reduced value. The UI shows the correct balance only after a reload.

**Business Impact:** after every successful bet the customer sees an outdated balance, which can lead them to repeat a bet they think failed or to bet money they no longer have.

**Evidence:** stake €12.34: [`tc01_3_after_close.png`](evidence/tc01_3_after_close.png) (UI €120.00, API 107.66), [`tc01_4_after_reload.png`](evidence/tc01_4_after_reload.png) (€107.66 after reload)

---

### BUG-06: Receipt shows a wrong potential payout

**Severity:** High

**Reproduction Steps**
1. Open the application.
2. Select any outcome on any upcoming match and enter a valid stake. Note the potential payout in the slip.
3. Click **Place Bet**.
4. Check **Potential Payout** on the receipt.

**Expected Result:** the receipt shows the same potential payout as the slip and the API, stake × odds.

**Actual Result:** the receipt always shows stake × 2, regardless of odds:

| Stake | Odds | Slip | Receipt |
|---|---|---|---|
| €12.34 | 3.70 | €45.66 | €24.68 |
| €10.00 | 2.65 | €26.50 | €20.00 |
| €5.00 | 3.35 | €16.75 | €10.00 |

**Business Impact:** the receipt is the customer's confirmation of the bet, a wrong payout on it leads to disputes and complaints when the bet is settled.

**Evidence:** [`tc01_1_slip.png`](evidence/tc01_1_slip.png) (slip: €45.66), [`tc01_2_receipt.png`](evidence/tc01_2_receipt.png) (receipt: €24.68), [`explore_receipt_home.png`](evidence/explore_receipt_home.png), [`explore_receipt_away.png`](evidence/explore_receipt_away.png)

---

### BUG-07: Receipt shows home and away teams swapped

**Severity:** Medium

**Reproduction Steps**
1. Open the application.
2. Place a bet on any upcoming match.
3. Check the **Match** field on the receipt.

**Expected Result:** "Home team vs Away team", the same order as in the match list and the slip

**Actual Result:** the receipt shows "Away team vs Home team" on every bet.

**Business Impact:** for Home/Away bets the customer may believe the bet was placed on the other team, leading to disputes.

**Evidence:** Dortmund vs Frankfurt - "Frankfurt vs Dortmund" ([`tc01_2_receipt.png`](evidence/tc01_2_receipt.png)), Monaco vs Lyon - "Lyon vs Monaco" ([`explore_receipt_away.png`](evidence/explore_receipt_away.png))

---

### BUG-08: Receipt does not show the selection

**Severity:** Medium

**Reproduction Steps**
1. Open the application.
2. Place a bet on any upcoming match.
3. Check the fields on the receipt.

**Expected Result:** the receipt shows the selection (Home / Draw / Away) together with Bet ID, match, stake, odds, potential payout and placement time

**Actual Result:** the receipt shows Bet ID, match, stake, odds, payout and placement time, the selection is missing.

**Business Impact:** the receipt does not confirm which outcome the customer bet on, so a mistaken selection goes unnoticed until settlement and leads to disputes and support requests.

**Evidence:** [`tc01_2_receipt.png`](evidence/tc01_2_receipt.png)

---

### BUG-09: API payout is €0.01 lower than stake × odds

**Severity:** High

**Reproduction Steps**
1. Reset the balance and open the application.
2. Select any upcoming match and enter a stake. Note the potential payout in the slip.
3. Click **Place Bet**.
4. Compare `payout` in the `POST /api/place-bet` response with stake × odds and with the slip.
5. Repeat with other stakes and odds: the issue appears on many combinations, not all.

**Expected Result:** `payout` equals stake × odds, the same value the slip shows

**Actual Result:** on many combinations the API returns a payout €0.01 lower than stake × odds and lower than the slip:

| Stake × odds | Correct | Slip | API |
|---|---|---|---|
| 100 × 2.55 | 255.00 | €255.00 | 254.99 |
| 90 × 2.55 | 229.50 | €229.50 | 229.49 |
| 12.34 × 3.70 | 45.658 | €45.66 | 45.65 |

**Business Impact:** the backend stores a payout lower than the amount shown to the customer, which can systematically underpay winning bets and cause reconciliation issues and disputes.

**Evidence:** stake €100 at 2.55:
```json
{"message":"Bet placed successfully","matchId":"eredivisie-feyenoord-psv-2026-10-18","selection":"HOME","stake":100,"odds":2.55,"payout":254.99,"balance":0,"currency":"USD"}
```

---

### BUG-10: Place-bet response returns currency USD

**Severity:** Medium

**Reproduction Steps**
1. Place any bet via the UI or `POST /api/place-bet`.
2. Check `currency` in the response.

**Expected Result:** `"currency": "EUR"` 

**Actual Result:** `"currency": "USD"` in every place-bet response

**Business Impact:** any receipt, history or report built on this response would show or record the bet in the wrong currency.

**Evidence:** right after a bet, the same balance (107.66) is reported in two different currencies:
```
POST /api/place-bet → {"message":"Bet placed successfully","matchId":"bundesliga-dortmund-frankfurt-2026-10-10","selection":"DRAW","stake":12.34,"odds":3.7,"payout":45.65,"balance":107.66,"currency":"USD"}
GET  /api/balance   → {"balance":107.66,"currency":"EUR"}
```
Observed in every place-bet response during the run, both from the UI and from direct API calls.
