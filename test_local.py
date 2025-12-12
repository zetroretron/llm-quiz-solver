import requests
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_URL = "https://zetroretro-llm-analysis-quiz-solver.hf.space"
SECRET = "My_Secret_Key"  # Must match STUDENT_SECRET in Hugging Face
EMAIL = "23f2004645@ds.study.iitm.ac.in"

TEST_URLS = [
    "https://tds-llm-analysis.s-anand.net/project2",
    # "https://tds-llm-analysis.s-anand.net/demo",
    # "https://tds-llm-analysis.s-anand.net/demo2",
    # "https://p2testingone.vercel.app/q1.html",
    # "https://tdsbasictest.vercel.app/quiz/1",
]

def test_root():
    print("Testing Root Endpoint...")
    try:
        response = requests.get(f"{API_URL}/")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Failed to connect: {e}")

def test_run_quiz(url):
    print(f"\nTesting /run Endpoint with {url}...")
    payload = {
        "email": EMAIL,
        "secret": SECRET,
        "url": url
    }
    
    try:
        response = requests.post(f"{API_URL}/run", json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Failed to trigger quiz: {e}")

if __name__ == "__main__":
    print("Ensure the server is running (uvicorn main:app --reload)")
    time.sleep(1)
    test_root()
    
    for url in TEST_URLS:
        test_run_quiz(url)
