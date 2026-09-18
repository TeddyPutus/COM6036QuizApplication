Feature: User Authentication
  As a user of the quiz application
  I want to be able to register, log in, and view my profile
  So that I can securely access my quizzes and attempts

  Scenario: A new user registers successfully
    Given I have a new user email and password
    When I send a request to register as a "student"
    Then the response status code should be 201
    And the response should contain my email and role "student"

  Scenario: A user logs in successfully
    Given I am a registered user
    When I log in with my credentials
    Then the response status code should be 200
    And the response should contain an access token

  Scenario: Fetch current user profile
    Given I am a logged in user
    When I request my profile
    Then the response status code should be 200
    And the response should contain my email
