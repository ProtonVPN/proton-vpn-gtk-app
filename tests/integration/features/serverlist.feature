Feature: Server List

  Background:
    Given the user is logged in

  Scenario:
    Given the server list widget is ready
    Then the server list should be displayed
