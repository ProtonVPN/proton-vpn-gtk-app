Feature: Login

  Scenario: Successful login without 2FA.
    Given a user without 2FA enabled
    And the user is not logged in
    When a correct username and password is submitted
    Then the user should be logged in.

  Scenario: Successful login with 2FA.
    Given a user with 2FA enabled
    And the user is not logged in
    When a correct username and password is submitted
    And a correct 2FA code is submitted
    Then the user should be logged in.
