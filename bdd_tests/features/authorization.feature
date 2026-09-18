Feature: Endpoint Authorization and Role-Based Access Control
  As a system administrator
  I want endpoints to be properly secured
  So that unauthenticated users cannot access them and users cannot exceed their role permissions

  Scenario: Unauthenticated access is denied
    Given I have no access token
    When I request my profile
    Then the response status code should be 401

    When I attempt to create a quiz
    Then the response status code should be 401

  Scenario: Student access to instructor endpoints is denied
    Given I am logged in as a "student"
    When I attempt to create a quiz
    Then the response status code should be 403
    And the error message should mention "Required roles"
    
    When I attempt to view instructor metrics for a dummy quiz
    Then the response status code should be 403

  Scenario: Instructor access to instructor endpoints is allowed
    Given I am logged in as an "instructor"
    When I attempt to create a quiz
    Then the response status code should be 201
    
    When I attempt to view instructor metrics for the created quiz
    Then the response status code should be 200
