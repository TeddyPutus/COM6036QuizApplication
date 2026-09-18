import requests
import csv
import uuid
import os
import concurrent.futures

BASE_URL = "http://localhost:8000/api/v1"

def create_student_attempt(i, quiz_id):
    stu_email = f"student_{uuid.uuid4().hex[:8]}@example.com"
    
    # Register
    requests.post(f"{BASE_URL}/auth/register", json={
        "email": stu_email,
        "password": "password123",
        "full_name": f"LoadTest Student {i}",
        "role": "student"
    })
    
    # Login
    res = requests.post(f"{BASE_URL}/auth/login", json={
        "email": stu_email,
        "password": "password123"
    })
    stu_token = res.json()["access_token"]
    
    # Take Quiz (get questions)
    res = requests.get(f"{BASE_URL}/quizzes/{quiz_id}/take", 
                       headers={"Authorization": f"Bearer {stu_token}"})
    quiz_take_data = res.json()
    question_id = quiz_take_data["questions"][0]["id"]
    option_id = quiz_take_data["questions"][0]["options"][0]["id"] # picking first option

    # Start Attempt
    res = requests.post(f"{BASE_URL}/attempts/start", json={
        "quiz_id": quiz_id
    }, headers={"Authorization": f"Bearer {stu_token}"})
    attempt_id = res.json()["attempt_id"]
    
    return {
        "token": stu_token,
        "attempt_id": attempt_id,
        "question_id": question_id,
        "option_id": option_id
    }

def main():
    print("Starting setup script for Gatling tests...")
    
    # 1. Register instructor
    inst_email = f"instructor_{uuid.uuid4().hex[:8]}@example.com"
    res = requests.post(f"{BASE_URL}/auth/register", json={
        "email": inst_email,
        "password": "password123",
        "full_name": "Gatling Instructor",
        "role": "instructor"
    })
    
    if res.status_code != 201:
        print(f"Failed to register instructor: {res.text}")
        return
        
    # 2. Login instructor
    res = requests.post(f"{BASE_URL}/auth/login", json={
        "email": inst_email,
        "password": "password123"
    })
    inst_token = res.json()["access_token"]
    
    # 3. Create quiz
    res = requests.post(f"{BASE_URL}/quizzes", json={
        "title": f"Gatling Load Test Quiz {uuid.uuid4().hex[:4]}",
        "subject": "Load Testing",
        "time_limit_minutes": 60,
        "passing_score_percentage": 50,
        "questions": [
            {
                "prompt": "What is the optimal load testing tool?",
                "points": 1,
                "options": [
                    {"text": "Gatling", "is_correct": True},
                    {"text": "A physical Gatling gun", "is_correct": False}
                ]
            }
        ]
    }, headers={"Authorization": f"Bearer {inst_token}"})
    
    if res.status_code != 201:
        print(f"Failed to create quiz: {res.text}")
        return
        
    quiz_id = res.json()["id"]
    print(f"Quiz created: {quiz_id}")

    # 4. Create Students & attempt data
    students_data = []
    num_students = 50
    
    print(f"Generating {num_students} students and their attempts concurrently...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(create_student_attempt, i, quiz_id) for i in range(num_students)]
        for future in concurrent.futures.as_completed(futures):
            try:
                data = future.result()
                students_data.append(data)
            except Exception as exc:
                print(f"Student generation generated an exception: {exc}")

    # Save to CSV
    # Ensure directory exists
    os.makedirs("src/test/resources/feeders", exist_ok=True)
    
    csv_path = "src/test/resources/feeders/users.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["token", "attempt_id", "question_id", "option_id"])
        writer.writeheader()
        writer.writerows(students_data)
        
    print(f"Setup complete. Data saved to {csv_path}")

if __name__ == "__main__":
    main()
