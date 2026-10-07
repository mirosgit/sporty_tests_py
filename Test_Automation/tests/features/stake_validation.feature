@api
Feature: Stake validation in the place-bet API
  Why this test: stake limits are a financial control, and the API is the last line of
  defence because the UI can be bypassed. It is fast and covers six rules in one outline.

  Scenario Outline: API rejects an invalid stake
    Given the balance is reset
    When a bet with stake <stake> is sent to the API
    Then the response is 422 with error "<error>"
    And the balance is unchanged

    # A quoted stake is sent as a JSON string, any other value as a number.
    Examples: Rejected as documented
      | stake  | error                   |
      | 0      | invalid_stake_min       |
      | 0.99   | invalid_stake_min       |
      | 100.01 | invalid_stake_max       |
      | 10.555 | invalid_stake_precision |
      | "10"   | invalid_stake_type      |

    # BUG-03: a negative stake is accepted and credited to the balance.
    # Remove @xfail when it is fixed; strict mode fails the run until then.
    @xfail
    Examples: Known defect BUG-03
      | stake | error             |
      | -5    | invalid_stake_min |
