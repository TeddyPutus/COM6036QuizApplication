Feature: Quiz and Attempt Workflow
  As an instructor, I want to create quizzes
  As a student, I want to take quizzes and submit my attempts

  Scenario: Instructor creates a new quiz
    Given I am logged in as an "instructor"
    When I create a quiz about "Python Basics" with 1 question
    Then the response status code should be 201
    And the response should contain the quiz id

  Scenario: Student takes and submits a quiz
    Given an instructor has created a quiz with 1 question
    And I am logged in as a "student"
    When I request to take the quiz
    Then the response status code should be 200
    And the response should contain the question without correct answers
    When I start a new attempt
    Then the response status code should be 201
    And the response should contain an attempt id
    When I submit my attempt with the correct answer
    Then the response status code should be 200
    And my score should be 100.0
