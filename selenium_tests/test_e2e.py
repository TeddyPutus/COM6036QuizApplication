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
    
    # Add a question
    add_q_btn = driver.find_element(By.XPATH, "//button[contains(text(), '+ Add Question')]")
    add_q_btn.click()
    
    # Wait for question fields to appear
    time.sleep(1)
    
    # Assuming the first question has class or id pattern
    # It might be dynamic, so let's find input with placeholder or name
    # In pure JS, inputs might just be appended. We will search by class/tags.
    questions_container = driver.find_element(By.ID, "questionsBuilder")
    prompts = questions_container.find_elements(By.TAG_NAME, "input")
    
    # Usually the first text input in the question builder is the prompt
    prompts[0].send_keys("What is Selenium?")
    
    driver.find_element(By.ID, "formCreateQuiz").submit()
    
    # 5. Verify the modal closes or an alert shows
    WebDriverWait(driver, 10).until(
        EC.invisibility_of_element_located((By.ID, "modalCreator"))
    )
    
    # Check if quiz list contains our new quiz
    quiz_list = driver.find_element(By.ID, "quizList")
    assert "Selenium E2E Test Quiz" in quiz_list.text
