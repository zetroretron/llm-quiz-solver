# LLM Quiz Solver

Autonomous AI agent that solves data analysis quizzes using FastAPI, Playwright, and OpenAI.

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   playwright install
   ```

2. **Environment Variables**:
   Copy `.env.example` to `.env` and fill in your details:
   ```bash
   cp .env.example .env
   ```
   - `OPENAI_API_KEY`: Your OpenAI API Key.
   - `STUDENT_SECRET`: A secret string you create.

3. **Run the Server**:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

## Deployment (Docker)

1. **Build Image**:
   ```bash
   docker build -t quiz-solver .
   ```

2. **Run Container**:
   ```bash
   docker run -p 8000:8000 --env-file .env quiz-solver
   ```

## API Endpoint

- **URL**: `POST /run`
- **Payload**:
  ```json
  {
    "email": "student@example.com",
    "secret": "your_defined_secret",
    "url": "https://example.com/quiz-task"
  }
  ```

## Project Structure

- `main.py`: FastAPI application entry point.
- `solver.py`: Core logic using Playwright and LLM to solve tasks.
- `tools.py`: Helper functions for file downloads and code execution.
- `Dockerfile`: Configuration for containerized deployment.
