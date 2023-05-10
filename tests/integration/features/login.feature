Feature: Login

  Background:
    Given the user is not logged in

  Scenario: Successful login without 2FA.
    Given a user without 2FA enabled
    When the correct username and password are introduced in the login form
    And the login form is submitted
    Then the user should be logged in
    And the credentials should be stored in the system's keyring

  Scenario: Successful login with 2FA.
    Given a user with 2FA enabled
    When the correct username and password are introduced in the login form
    And the login form is submitted
    And a correct 2FA code is submitted
    Then the user should be logged in
    And the credentials should be stored in the system's keyring

  Scenario: Username and password not provided.
    When the login data is not provided
    Then the user should not be able to submit the form
