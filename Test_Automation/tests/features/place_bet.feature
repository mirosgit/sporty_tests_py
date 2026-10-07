@ui
Feature: Placing a single bet through the UI
  Why this test: it is the main revenue journey (TC-01) and the only flow that crosses
  every layer (UI, API, stored balance), so one scenario catches the most regressions.

  # Known defects BUG-06, BUG-07, BUG-08: the receipt shows a wrong payout, swapped teams
  # and no selection. Remove @xfail when they are fixed; strict mode fails the run until then.
  @xfail
  Scenario: User places a single bet and the balance is debited
    Given the balance is reset
    And the betting page is open
    When the user selects "Draw" on the nearest upcoming match
    # A whole-euro stake keeps stake × odds exact for any odds with two decimals.
    And the user enters a stake of 10
    Then the bet slip shows the selected match and the potential payout
    When the user places the bet
    Then the bet is shown as being placed
    And the receipt shows the bet details
    When the user closes the receipt
    Then the bet slip is empty
    And the balance is reduced by the stake
