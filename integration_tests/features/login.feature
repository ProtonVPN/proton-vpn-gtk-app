Feature: Login

  Scenario: Successful login without 2FA.
    Given a user without 2FA enabled
    And the user is not logged in
    When the correct username and password are introduced in the login form
    And the login form is submitted
    Then the user should be logged in.

  Scenario: Successful login with 2FA.
    Given a user with 2FA enabled
    And the user is not logged in
    When the correct username and password are introduced in the login form
    And the login form is submitted
    And a correct 2FA code is submitted
    Then the user should be logged in.

  Scenario: Wrong password.
    Given the user is not logged in
    When the wrong password is introduced
    And the login form is submitted
    Then the user should be notified with the error message: "Wrong credentials."
