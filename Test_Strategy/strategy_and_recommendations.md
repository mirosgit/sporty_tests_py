# Strategy & Recommendations

## Why these 2 tests were automated

| Test | Layer | Why it was chosen |
|---|---|---|
| *User places a single bet and the balance is debited* (`place_bet.feature`, TC-01) | UI | The main revenue journey. One scenario goes through the UI, the API and the stored balance, so it catches the widest range of regressions. It already catches three receipt defects (BUG-06, BUG-07, BUG-08). |
| *API rejects an invalid stake* (`stake_validation.feature`, TC-05 + negative stake) | API | Stake limits are a financial control, and the API is the last line of defence because the UI can be bypassed. The test is fast and deterministic: one scenario outline covers six rules, each with a documented error code as a clear expected result, and checks that the balance does not change. It already catches the most expensive defect found: a negative stake that adds money (BUG-03). |

Both tests are written as BDD scenarios, so the Product Owner can read and review them. Cases that hit known defects are tagged `@xfail` with the bug ID; the run stays green until the defect is fixed, then fails and asks to remove the tag.

## What stays manual, and why

- **Exploratory testing around bet placement.** The double-click double charge (BUG-04) and the overdraft through a stale UI balance (BUG-02 with BUG-05) were found by trying things no scenario described.
- **Error modal, Rebet and Close.** They need fault injection through a proxy, which is expensive and fragile in a UI test. They are better covered once the API supports a controlled failure.
- **Ambiguous requirements.** The €1.00 vs €1.01 minimum, bets on a match dated today, and how the payout is calculated have no reliable expected result yet. Automating them would turn an assumption into a test.
- **Visual details and wording.** Receipt layout, message copy and filters are low risk, and these checks break often when the UI changes.

## Recommendations if the project scales

1. **Put most coverage on the API layer and run it in CI.**
   - **Where the bugs are.** 5 of the 10 defects reported are in the API, including three of the four Critical ones (BUG-01, BUG-02, BUG-03). API tests catch them faster and more reliably than UI tests.
   - **What to add.** Contract tests that validate responses against the OpenAPI schema; this would have caught `currency: "USD"` (BUG-10). Also API scenarios for the balance, past-match and concurrency rules.
   - **How to run it.** API tests on every pull request; a thin UI smoke suite (2-3 journeys) on merge and nightly. Critical failures block the release. The framework already writes `junit.xml`, `cucumber.json` and failure screenshots, so CI only needs to publish them.
2. **Make test data deterministic and isolated.**
   - **The problem today.** The live catalog changes with the calendar: 81 of 103 matches are already past. The API accepts only one user id per candidate, so all tests share one balance and must run one at a time.
   - **What to do.** A seeded match catalog with fixed future dates, plus provisioning of test users, so that each test or worker gets its own account. This also enables parallel runs.
3. **Close the spec gaps before automating these areas.** The Product Owner should confirm:
   - the minimum stake: €1.00 or €1.01;
   - the error code for insufficient balance and for past matches;
   - whether a match dated today can still be bet on (kickoff has no time);
   - how the payout is calculated and stored (the API returns 254.99 for 100 × 2.55);
   - whether retries need an idempotency key, so that Rebet after a lost response cannot place the bet twice.

   Each answer turns an open question into a clear expected result for an automated test.
