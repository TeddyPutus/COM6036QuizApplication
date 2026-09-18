import requests
import uuid

def before_all(context):
    context.base_url = "http://localhost:8000/api/v1"
    context.session = requests.Session()
    # Ensure a fresh user suffix for every run to avoid conflicts
    context.run_id = uuid.uuid4().hex[:6]

def before_scenario(context, scenario):
    # Reset auth headers before every scenario
    context.session.headers.clear()
    context.session.headers.update({"Content-Type": "application/json"})
