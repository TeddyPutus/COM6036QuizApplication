# Online Assessment Platform (Quiz Application)

A comprehensive, multi-tier web application designed to allow instructors to create quizzes and students to take them in a time-enforced environment. 

The application architecture is separated into a RESTful backend API and a static client frontend, fully containerized for easy deployment.

## Tech Stack
* **Backend:** Python, FastAPI, PostgreSQL
* **Frontend:** Vanilla HTML/JS, TailwindCSS, NGINX
* **Containerization:** Docker / Podman
* **Testing:** Behave (BDD), Selenium (E2E), Gatling (Load Testing)

---

## 🛠 Prerequisites

Before running the application or its tests, ensure you have the following installed on your machine:

1. **Docker** or **Podman** (with `docker-compose` or `podman-compose`) for running the application stack.
2. **Python 3.10+** (for running the BDD and Selenium testing scripts).
3. **Java 17** and **Apache Maven** (strictly required if you wish to run the Gatling Load Tests).
4. **Google Chrome** (required for the headless Selenium UI tests).

---

## 🚀 Running the Application

The entire application stack (Frontend, Backend API, PostgreSQL Database, and Adminer DB viewer) is defined in `compose.yaml`.

To start the application, open your terminal in the root directory and run:

```bash
# Using Docker
docker compose up --build
```

OR

```bash
# Using Podman
podman compose up --build
```

Once the containers are successfully running, the services will be available at:
* **Frontend UI:** [http://localhost:3000](http://localhost:3000)
* **Backend API Docs (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)
* **Adminer (Database Viewer):** [http://localhost:8080](http://localhost:8080) *(Login with System: PostgreSQL, Server: database, User: postgres, Password: postgres)*

---

## 🧪 Running the Tests

This repository contains three different test suites to ensure system reliability across all layers. **Make sure the application is actively running via compose before executing the tests.**

### 1. BDD API Tests (Behave)
These test the backend endpoints directly using Behavior-Driven Development (Gherkin syntax).

```bash
cd bdd_tests
# Install dependencies
pip install -r requirements.txt
# Run the test suite
behave
```

### 2. End-to-End UI Tests (Selenium)
These tests spin up a headless Chrome browser to simulate a real user clicking through the frontend interface, testing both the Student and Instructor workflows.

```bash
cd selenium_tests
# Install dependencies
pip install -r requirements.txt
# Run the test suite
pytest test_e2e.py -v
```

### 3. Load Testing (Gatling)
These tests bombard the system with concurrent attempts to ensure the backend and database can handle high traffic.

```bash
cd gatling_tests
# Install requests for the setup script
pip install requests

# 1. Run the Python script to pre-load 50 mock students and active attempts into the DB
python setup_data.py

# 2. Run the Gatling simulation via Maven
mvn gatling:test
```
*Once finished, Maven will output a link to an interactive HTML report located in the `target/gatling/` directory.*
