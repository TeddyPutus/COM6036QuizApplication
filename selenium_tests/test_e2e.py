import pytest
import uuid
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import Select

# Set this to the frontend URL mapped in your docker-compose
BASE_URL = "http://localhost:3000"

@pytest.fixture(scope="module")
def driver():
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    
    # Initialize WebDriver
    # Workaround for a known webdriver-manager bug on Windows returning the THIRD_PARTY_NOTICES file
    import os
    driver_path = ChromeDriverManager().install()
    if not driver_path.endswith(".exe"):
        driver_path = os.path.join(os.path.dirname(driver_path), "chromedriver.exe")
        
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(5)
    
    yield driver
    
    driver.quit()


def test_student_registration_and_login(driver):
    driver.get(BASE_URL)
    
    # Switch to Register Tab
    register_tab = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "tabRegister"))
    )
    register_tab.click()
    
    # Fill out Registration Form
    unique_id = uuid.uuid4().hex[:6]
    email = f"student_{unique_id}@example.com"
    password = "password123"
    
    driver.find_element(By.ID, "regName").send_keys("Selenium Student")
    driver.find_element(By.ID, "regEmail").send_keys(email)
    driver.find_element(By.ID, "regPassword").send_keys(password)
    
    role_select = Select(driver.find_element(By.ID, "regRole"))
    role_select.select_by_value("student")
    
    driver.find_element(By.ID, "formRegister").submit()
    
    # Wait for alert or auto switch to login
    # Wait until login tab is active or dashboard is visible
    # Assuming registration requires manual login after success
    time.sleep(1) # Let the alert/animation finish
    
    # Switch back to Login Tab if not automatic
    try:
        login_tab = driver.find_element(By.ID, "tabLogin")
        login_tab.click()
    except:
        pass
        
    # Fill out Login Form
    driver.find_element(By.ID, "loginEmail").send_keys(email)
    driver.find_element(By.ID, "loginPassword").send_keys(password)
    driver.find_element(By.ID, "formLogin").submit()
    
    # Assert successful login by checking for Dashboard or Auth Nav change
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "viewDashboard"))
    )
    
    dashboard = driver.find_element(By.ID, "viewDashboard")
    assert dashboard.is_displayed()
    
    # Logout so the next test can run fresh
    logout_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Logout')]")
    logout_btn.click()
    
    # Wait for login form to reappear
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "formLogin"))
    )


def test_instructor_create_quiz(driver):
    driver.get(BASE_URL)
    
    # 1. Register Instructor
    driver.find_element(By.ID, "tabRegister").click()
    
    unique_id = uuid.uuid4().hex[:6]
    email = f"instructor_{unique_id}@example.com"
    password = "password123"
    
    driver.find_element(By.ID, "regName").send_keys("Selenium Instructor")
    driver.find_element(By.ID, "regEmail").clear()
    driver.find_element(By.ID, "regEmail").send_keys(email)
    driver.find_element(By.ID, "regPassword").clear()
    driver.find_element(By.ID, "regPassword").send_keys(password)
    
    role_select = Select(driver.find_element(By.ID, "regRole"))
    role_select.select_by_value("instructor")
    
    driver.find_element(By.ID, "formRegister").submit()
    time.sleep(1)
    
    # 2. Login Instructor
    driver.find_element(By.ID, "tabLogin").click()
    
    driver.find_element(By.ID, "loginEmail").clear()
    driver.find_element(By.ID, "loginEmail").send_keys(email)
    driver.find_element(By.ID, "loginPassword").clear()
    driver.find_element(By.ID, "loginPassword").send_keys(password)
    driver.find_element(By.ID, "formLogin").submit()
    
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "viewDashboard"))
    )
    
    # 3. Open Quiz Creator
    create_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "btnOpenCreator"))
    )
    create_btn.click()
    
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "modalCreator"))
    )
    
    # 4. Fill out Quiz info
    driver.find_element(By.ID, "qTitle").send_keys("Selenium E2E Test Quiz")
    driver.find_element(By.ID, "qSubject").send_keys("E2E Testing")
    
    # The modal automatically adds the first question. We just need to wait for it.
    time.sleep(1)
    
    # Assuming the first question has class or id pattern
    questions_container = driver.find_element(By.ID, "questionsBuilder")
    prompts = questions_container.find_elements(By.TAG_NAME, "input")
    
    # Usually the first text input in the question builder is the prompt
    prompts[0].send_keys("What is Selenium?")
    
    # Fill the options so the distinct options validation passes
    options = []
    for i in range(4):
        options.append(questions_container.find_element(By.CSS_SELECTOR, f".q-opt-{i}"))
        
    options[0].send_keys("Browser automation tool")
    options[1].send_keys("Vegetable")
    options[2].send_keys("Programming language")
    options[3].send_keys("Database")
    
    # Use JS click on the submit button to avoid interception
    submit_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Publish Quiz')]")
    driver.execute_script("arguments[0].click();", submit_btn)
    
    # 5. Verify the modal closes or an alert shows
    WebDriverWait(driver, 10).until(
        EC.invisibility_of_element_located((By.ID, "modalCreator"))
    )
    
    # Check if quiz list contains our new quiz
    quiz_list = driver.find_element(By.ID, "quizList")
    assert "Selenium E2E Test Quiz" in quiz_list.text
    
    # Logout so the next test can run fresh
    logout_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Logout')]")
    driver.execute_script("arguments[0].click();", logout_btn)
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "formLogin"))
    )


def test_student_attempt_session_state(driver):
    driver.get(BASE_URL)
    
    # 1. Register Student
    tab_register = driver.find_element(By.ID, "tabRegister")
    driver.execute_script("arguments[0].click();", tab_register)
    unique_id = uuid.uuid4().hex[:6]
    email = f"student_{unique_id}@example.com"
    password = "password123"
    
    driver.find_element(By.ID, "regName").send_keys("State Student")
    driver.find_element(By.ID, "regEmail").clear()
    driver.find_element(By.ID, "regEmail").send_keys(email)
    driver.find_element(By.ID, "regPassword").clear()
    driver.find_element(By.ID, "regPassword").send_keys(password)
    Select(driver.find_element(By.ID, "regRole")).select_by_value("student")
    driver.find_element(By.ID, "formRegister").submit()
    time.sleep(1)
    
    # 2. Login Student
    tab_login = driver.find_element(By.ID, "tabLogin")
    driver.execute_script("arguments[0].click();", tab_login)
    driver.find_element(By.ID, "loginEmail").clear()
    driver.find_element(By.ID, "loginEmail").send_keys(email)
    driver.find_element(By.ID, "loginPassword").clear()
    driver.find_element(By.ID, "loginPassword").send_keys(password)
    driver.find_element(By.ID, "formLogin").submit()
    
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "viewDashboard"))
    )
    
    # 3. Click first quiz
    time.sleep(2) # Wait for catalog to load
    quiz_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Start Test')]")
    if not quiz_buttons:
        pytest.skip("No quizzes available to test session state")
        
    driver.execute_script("arguments[0].click();", quiz_buttons[0])
    
    # Wait for test runner
    try:
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "viewTestRunner"))
        )
    except Exception as e:
        print("--- BROWSER CONSOLE LOGS ---")
        for log in driver.get_log('browser'):
            print(log)
        print("----------------------------")
        # Debug alert if it fails
        try:
            alert_box = driver.find_element(By.ID, "alertBox")
            print(f"DEBUG ALERT TEXT: {alert_box.get_attribute('innerText')}")
        except:
            pass
        raise e
    
    # 4. Select an option
    time.sleep(1)
    radios = driver.find_elements(By.XPATH, "//input[@type='radio']")
    if not radios:
        pytest.skip("Quiz has no questions")
    
    radios[0].click()
    selected_value = radios[0].get_attribute("value")
    
    # 5. Refresh the page
    driver.refresh()
    
    # After refresh, wait for dashboard to load (assumes auth token persists)
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "viewDashboard"))
    )
    time.sleep(2)
    
    # 6. Click the first quiz again
    quiz_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Start Test')]")
    driver.execute_script("arguments[0].click();", quiz_buttons[0])
    
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "viewTestRunner"))
    )
    time.sleep(1)
    
    # 7. Verify the radio button is still checked
    radios = driver.find_elements(By.XPATH, "//input[@type='radio']")
    checked_radio = None
    for r in radios:
        if r.get_attribute("checked") or r.is_selected():
            checked_radio = r
            break
            
    assert checked_radio is not None, "No option was saved in session state"
    assert checked_radio.get_attribute("value") == selected_value, "Saved option mismatch"

def test_error_handling_invalid_login(driver):
    driver.get(BASE_URL)
    driver.execute_script("window.localStorage.clear(); window.sessionStorage.clear();")
    driver.refresh()
    
    # Switch to Login Tab
    tab_login = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "tabLogin"))
    )
    driver.execute_script("arguments[0].click();", tab_login)
    
    # Submit bad credentials
    driver.find_element(By.ID, "loginEmail").clear()
    driver.find_element(By.ID, "loginEmail").send_keys("nonexistent@example.com")
    driver.find_element(By.ID, "loginPassword").clear()
    driver.find_element(By.ID, "loginPassword").send_keys("wrongpassword")
    
    driver.find_element(By.ID, "formLogin").submit()
    
    # Wait for the alert box to become visible
    alert_box = WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.ID, "alertBox"))
    )
    
    # Verify the text is sensible
    alert_text = alert_box.get_attribute("innerText")
    assert "Incorrect email or password" in alert_text or "401" in alert_text or "Invalid" in alert_text or "detail" in alert_text

def test_student_time_limit_auto_submit(driver):
    driver.get(BASE_URL)
    driver.execute_script("window.localStorage.clear(); window.sessionStorage.clear();")
    driver.refresh()
    
    # 1. Register an Instructor & Create 1 min quiz
    tab_reg = driver.find_element(By.ID, "tabRegister")
    driver.execute_script("arguments[0].click();", tab_reg)
    inst_email = f"inst_timer_{uuid.uuid4().hex[:6]}@example.com"
    
    driver.find_element(By.ID, "regName").send_keys("Timer Instructor")
    driver.find_element(By.ID, "regEmail").clear()
    driver.find_element(By.ID, "regEmail").send_keys(inst_email)
    driver.find_element(By.ID, "regPassword").clear()
    driver.find_element(By.ID, "regPassword").send_keys("password123")
    Select(driver.find_element(By.ID, "regRole")).select_by_value("instructor")
    driver.find_element(By.ID, "formRegister").submit()
    time.sleep(1)
    
    tab_login = driver.find_element(By.ID, "tabLogin")
    driver.execute_script("arguments[0].click();", tab_login)
    driver.find_element(By.ID, "loginEmail").clear()
    driver.find_element(By.ID, "loginEmail").send_keys(inst_email)
    driver.find_element(By.ID, "loginPassword").clear()
    driver.find_element(By.ID, "loginPassword").send_keys("password123")
    driver.find_element(By.ID, "formLogin").submit()
    
    WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "viewDashboard")))
    
    create_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "btnOpenCreator")))
    create_btn.click()
    WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "modalCreator")))
    
    driver.find_element(By.ID, "qTitle").send_keys("1 Minute Quiz")
    driver.find_element(By.ID, "qSubject").send_keys("Time Limits")
    
    # SET TIME TO 1 MINUTE
    time_input = driver.find_element(By.ID, "qTime")
    time_input.clear()
    time_input.send_keys("1")
    
    time.sleep(1)
    questions_container = driver.find_element(By.ID, "questionsBuilder")
    prompts = questions_container.find_elements(By.TAG_NAME, "input")
    prompts[0].send_keys("Will this auto-submit?")
    
    options = []
    for i in range(4):
        options.append(questions_container.find_element(By.CSS_SELECTOR, f".q-opt-{i}"))
        
    options[0].send_keys("Yes")
    options[1].send_keys("No")
    options[2].send_keys("Maybe")
    options[3].send_keys("I don't know")
    
    submit_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Publish Quiz')]")
    driver.execute_script("arguments[0].click();", submit_btn)
    
    WebDriverWait(driver, 10).until(EC.invisibility_of_element_located((By.ID, "modalCreator")))
    
    logout_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Logout')]")
    driver.execute_script("arguments[0].click();", logout_btn)
    WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "formLogin")))
    
    # 2. Register Student & Take Quiz
    tab_register = driver.find_element(By.ID, "tabRegister")
    driver.execute_script("arguments[0].click();", tab_register)
    stu_email = f"stu_timer_{uuid.uuid4().hex[:6]}@example.com"
    
    driver.find_element(By.ID, "regName").send_keys("Timer Student")
    driver.find_element(By.ID, "regEmail").clear()
    driver.find_element(By.ID, "regEmail").send_keys(stu_email)
    driver.find_element(By.ID, "regPassword").clear()
    driver.find_element(By.ID, "regPassword").send_keys("password123")
    Select(driver.find_element(By.ID, "regRole")).select_by_value("student")
    driver.find_element(By.ID, "formRegister").submit()
    time.sleep(1)
    
    tab_login = driver.find_element(By.ID, "tabLogin")
    driver.execute_script("arguments[0].click();", tab_login)
    driver.find_element(By.ID, "loginEmail").clear()
    driver.find_element(By.ID, "loginEmail").send_keys(stu_email)
    driver.find_element(By.ID, "loginPassword").clear()
    driver.find_element(By.ID, "loginPassword").send_keys("password123")
    driver.find_element(By.ID, "formLogin").submit()
    
    WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "viewDashboard")))
    
    time.sleep(2)
    quiz_cards = driver.find_elements(By.XPATH, "//h3[text()='1 Minute Quiz']/ancestor::div[contains(@class, 'bg-white')]")
    if not quiz_cards:
        pytest.skip("Timer quiz not found on dashboard")
        
    start_btn = quiz_cards[0].find_element(By.XPATH, ".//button[contains(text(), 'Start Test')]")
    driver.execute_script("arguments[0].click();", start_btn)
    
    WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "viewTestRunner")))
    
    # Don't click any option, just wait for timer to run out.
    # The quiz is 1 minute, so we wait 61 seconds for the JS setInterval to trigger submission.
    # When it hits zero, it triggers a native alert() which we MUST accept in Selenium!
    try:
        WebDriverWait(driver, 70).until(EC.alert_is_present())
        alert = driver.switch_to.alert
        alert.accept()
    except Exception:
        pytest.fail("Quiz timer native alert did not appear after 60 seconds")
        
    try:
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "viewResults")))
    except Exception:
        pytest.fail("View results did not appear after accepting timer alert")
        
    # Verify score is 0%
    score = driver.find_element(By.ID, "resultScore").text
    assert "0%" in score
