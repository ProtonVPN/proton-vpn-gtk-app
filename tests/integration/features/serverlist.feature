Feature: Server List

  Scenario: Server list initialization
    Given the user is logged in
    When the server list widget is initialized
    Then the server list should be displayed
