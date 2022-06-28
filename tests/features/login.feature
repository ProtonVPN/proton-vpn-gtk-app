Feature: Login

  Scenario: Successful login
    Given the user is not logged in
    When a correct username and password is submitted
    Then the user should be logged in.