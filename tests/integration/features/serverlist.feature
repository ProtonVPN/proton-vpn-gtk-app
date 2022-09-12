Feature: Server List

  Scenario: Server list initialization
    Given the user is logged in
    When the server list widget is initialized
    Then the server list should be displayed

  @not_implemented
  Scenario: Logical servers update
    Given the user is logged in
    When the logical servers were updated more than 3 hours ago
    Then the logical servers should be updated again

  @not_implemented
  Scenario: Connect to a server
    Given the user is logged in
    And the servers widget is initialized
    When the user pushes the "Connect" button next to a server
    Then the user should be connected to that server
