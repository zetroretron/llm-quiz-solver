import os
import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

class QuizRequest(BaseModel):
    email: str
    secret: str
    url: HttpUrl
    # Allow extra fields
    model_config = {
        "extra": "allow"
    }

from solver_v2 import run_solver

# Load secret from environment variable
STUDENT_SECRET = os.getenv("STUDENT_SECRET", "default_secret_for_testing")

async def solve_quiz_task(email: str, secret: str, start_url: str):
    """
    Background task to solve the quiz.
    """
    logger.info(f"Starting quiz solver v2.0 for {email} at {start_url}")
    await run_solver(start_url, email, secret)

@app.post("/run")
async def run_quiz(request: QuizRequest, background_tasks: BackgroundTasks):
    """
    Endpoint to trigger the quiz solver.
    """
    # Verify secret
    if request.secret != STUDENT_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")

    # Dispatch background task
    background_tasks.add_task(solve_quiz_task, request.email, request.secret, str(request.url))

    return {"message": "Quiz solver started", "status": "processing"}

@app.get("/")
async def root():
    return {"message": "LLM Analysis Quiz Solver is running"}

# Add exception handler for validation errors (invalid JSON)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"detail": "Invalid JSON payload"}
    )
