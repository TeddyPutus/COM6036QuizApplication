import uuid
from behave import given, when, then

# --- Auth Steps ---

@given('I have a new user email and password')
def step_impl(context):
    context.user_email = f"bdd_user_{uuid.uuid4().hex[:6]}@example.com"
    context.user_password = "password123"
    context.user_name = "BDD Test User"

@when('I send a request to register as a "{role}"')
def step_impl(context, role):
    payload = {
        "email": context.user_email,
        "password": context.user_password,
        "full_name": context.user_name,
        "role": role
    }
    context.response = context.session.post(f"{context.base_url}/auth/register", json=payload)

@then('the response status code should be {status_code:d}')
def step_impl(context, status_code):
    assert context.response.status_code == status_code, \
        f"Expected {status_code}, got {context.response.status_code}. Response: {context.response.text}"

@then('the response should contain my email and role "{role}"')
def step_impl(context, role):
    data = context.response.json()
    assert data["email"] == context.user_email
    assert data["role"] == role

@given('I am a registered user')
def step_impl(context):
    context.execute_steps('''
        Given I have a new user email and password
        When I send a request to register as a "student"
    ''')
    assert context.response.status_code == 201

@when('I log in with my credentials')
def step_impl(context):
    payload = {
        "email": context.user_email,
        "password": context.user_password
    }
    context.response = context.session.post(f"{context.base_url}/auth/login", json=payload)

@then('the response should contain an access token')
def step_impl(context):
    data = context.response.json()
    assert "access_token" in data
    context.access_token = data["access_token"]
    context.session.headers.update({"Authorization": f"Bearer {context.access_token}"})

@given('I am a logged in user')
def step_impl(context):
    context.execute_steps('''
        Given I am a registered user
        When I log in with my credentials
        Then the response should contain an access token
    ''')

@when('I request my profile')
def step_impl(context):
    context.response = context.session.get(f"{context.base_url}/auth/me")

@then('the response should contain my email')
def step_impl(context):
    data = context.response.json()
    assert data["email"] == context.user_email


# --- Quiz & Attempt Steps ---

@given('I am logged in as {a_or_an} "{role}"')
def step_impl(context, a_or_an, role):
    context.execute_steps(f'''
        Given I have a new user email and password
        When I send a request to register as a "{role}"
        And I log in with my credentials
        Then the response should contain an access token
    ''')

@when('I create a quiz about "{title}" with 1 question')
def step_impl(context, title):
    payload = {
        "title": title,
        "subject": "BDD Testing",
        "time_limit_minutes": 30,
        "passing_score_percentage": 50,
        "questions": [
            {
                "prompt": "Is BDD awesome?",
                "points": 1,
                "options": [
                    {"text": "Yes", "is_correct": True},
                    {"text": "No", "is_correct": False}
                ]
            }
        ]
    }
    context.response = context.session.post(f"{context.base_url}/quizzes", json=payload)
    if context.response.status_code == 201:
        context.quiz_id = context.response.json()["id"]

@then('the response should contain the quiz id')
def step_impl(context):
    data = context.response.json()
    assert "id" in data
    context.quiz_id = data["id"]

@given('an instructor has created a quiz with 1 question')
def step_impl(context):
    inst_email = f"inst_{uuid.uuid4().hex[:6]}@example.com"
    context.session.post(f"{context.base_url}/auth/register", json={
        "email": inst_email, "password": "password123", "full_name": "Inst", "role": "instructor"
    })
    res = context.session.post(f"{context.base_url}/auth/login", json={"email": inst_email, "password": "password123"})
    token = res.json()["access_token"]
    
    res = context.session.post(f"{context.base_url}/quizzes", json={
        "title": "Student Test Quiz",
        "subject": "Testing",
        "time_limit_minutes": 10,
        "passing_score_percentage": 50,
        "questions": [
            {
                "prompt": "What color is the sky?",
                "points": 1,
                "options": [
                    {"text": "Blue", "is_correct": True},
                    {"text": "Green", "is_correct": False}
                ]
            }
        ]
    }, headers={"Authorization": f"Bearer {token}"})
    context.quiz_id = res.json()["id"]
    
    context.session.headers.clear()
    context.session.headers.update({"Content-Type": "application/json"})

@when('I request to take the quiz')
def step_impl(context):
    context.response = context.session.get(f"{context.base_url}/quizzes/{context.quiz_id}/take")

@then('the response should contain the question without correct answers')
def step_impl(context):
    data = context.response.json()
    assert "questions" in data
    context.question_id = data["questions"][0]["id"]
    context.option_id = data["questions"][0]["options"][0]["id"]
    assert "is_correct" not in data["questions"][0]["options"][0]

@when('I start a new attempt')
def step_impl(context):
    context.response = context.session.post(f"{context.base_url}/attempts/start", json={"quiz_id": context.quiz_id})

@then('the response should contain an attempt id')
def step_impl(context):
    data = context.response.json()
    assert "attempt_id" in data
    context.attempt_id = data["attempt_id"]

@when('I submit my attempt with the correct answer')
def step_impl(context):
    payload = {
        "answers": [
            {
                "question_id": context.question_id,
                "selected_option_id": context.option_id
            }
        ]
    }
    context.response = context.session.post(f"{context.base_url}/attempts/{context.attempt_id}/submit", json=payload)

@then('my score should be 100.0')
def step_impl(context):
    data = context.response.json()
    assert data["score"] == 100.0, f"Expected 100.0, got {data.get('score')}"
    assert data["passed"] is True
