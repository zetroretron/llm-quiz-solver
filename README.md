# LLM Quiz Solver

**Autonomous AI agent that solves data analysis quizzes using FastAPI, Playwright, and OpenAI.**

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Playwright](https://img.shields.io/badge/Playwright-2EAD33?style=flat&logo=playwright&logoColor=white)](https://playwright.dev/)
[![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=flat&logo=openai&logoColor=white)](https://openai.com/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat)](LICENSE)

> A multi-handler agentic system that navigates quiz pages, classifies tasks, solves them using deterministic heuristics first, and falls back to LLM reasoning only when needed — minimizing API costs while maximizing accuracy.

---

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                        QUIZ SOLVER AGENT                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐    ┌──────────┐    ┌───────────┐    ┌──────────┐  │
│  │ Navigate │───▶│ Extract  │───▶│ Classify  │───▶│ Heuristic│  │
│  │  (URL)   │    │ Content  │    │ Task Type │    │  Solver  │  │
│  └──────────┘    └──────────┘    └───────────┘    └────┬─────┘  │
│       ▲                                                │         │
│       │                                          ┌─────▼─────┐  │
│       │                                          │  Success? │  │
│       │                                          └─────┬─────┘  │
│       │                                          Yes   │   No   │
│       │                                          ┌─────▼─────┐  │
│       │                                          │  Handler  │  │
│       │                                          │  Registry │  │
│       │                                          └─────┬─────┘  │
│       │                                          ┌─────▼─────┐  │
│       │                                          │   LLM     │  │
│       │                                          │  Fallback │  │
│       │                                          └─────┬─────┘  │
│       │                                                │         │
│       │                                          ┌─────▼─────┐  │
│       └──────────────────────────────────────────│  Submit   │  │
│                                                  │  Answer   │  │
│                                                  └───────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Agent Flow

1. **Navigate** — Playwright opens the quiz URL and waits for page load
2. **Extract** — Page text and HTML are parsed for task clues
3. **Classify** — Regex patterns match the page content to one of 20+ task types
4. **Heuristic Solver** — Deterministic, zero-cost solutions for known patterns
5. **Handler Registry** — Specialized handlers attempt the task in priority order
6. **LLM Fallback** — Only if all heuristics and handlers fail, GPT-4 is invoked
7. **Submit** — Answer posted to the quiz endpoint; correct → next URL, wrong → retry or stop

### Cost Optimization Strategy

```
Heuristic (deterministic, $0)
    │
    ├── Success → Submit (no LLM call)
    │
    └── Fail
        │
        Handler Registry (specialized logic, $0)
            │
            ├── Success → Submit (no LLM call)
            │
            └── Fail
                │
                LLM Handler (GPT-4, costs tokens)
                    │
                    └── Submit
```

**Result:** Most quiz steps are solved without any LLM API calls, keeping costs near zero.

---

## Architecture

### Handler Registry Pattern

The system uses a **priority-based handler registry** where each handler specializes in a specific task domain:

| Priority | Handler | Domain | Example Tasks |
|----------|---------|--------|---------------|
| 1 | `DataHandler` | CSV, JSON, log files | Normalize CSV, sort JSON, parse logs |
| 2 | `PDFHandler` | PDF extraction | Invoice totals, table extraction |
| 3 | `AudioHandler` | Audio transcription | Transcribe passphrase from .opus |
| 4 | `ImageHandler` | Image analysis | Dominant color, heatmap values |
| 5 | `APIHandler` | REST API interaction | Custom headers, rate limits |
| 6 | `MLHandler` | ML tasks | Regression, classification, F1 score |
| 7 | `ChartHandler` | Data visualization | Generate plots, base64 charts |
| 8 | `DOMHandler` | JavaScript/DOM manipulation | innerHTML, querySelector, atob |
| 9 | `DiffHandler` | Text comparison | Count changed lines between files |
| 10 | `EmbeddingHandler` | Vector similarity | RAG, semantic search, embeddings |
| 11 | `LLMHandler` | General reasoning | Fallback for unknown task types |

### Task Classification Engine

The agent classifies incoming pages using **pattern matching** against 20+ task types:

```python
# Example: Task classification patterns
TASK_PATTERNS = {
    'audio':    [r'audio', r'transcribe', r'\.opus', r'\.mp3'],
    'image':    [r'heatmap', r'rgb color', r'hex string'],
    'pdf':      [r'\.pdf', r'invoice', r'sum of.*column'],
    'github':   [r'github\s*api', r'/repos/\{owner\}', r'count.*\.md'],
    'ml':       [r'predict', r'train', r'regression', r'weather'],
    'embedding':[r'embed', r'rag', r'similarity', r'vector'],
    # ... 15+ more task types
}
```

### Key Components

```
llm-quiz-solver/
├── main.py              # FastAPI server + /run endpoint
├── solver_v2.py         # Agent orchestration + task classification
├── tools.py             # File download + Python code execution utilities
├── handlers/            # Specialized task handlers (11 total)
│   ├── base.py          # HandlerRegistry + TaskContext
│   ├── data_handler.py  # CSV/JSON/log processing
│   ├── pdf_handler.py   # PDF extraction
│   ├── audio_handler.py # Audio transcription
│   ├── image_handler.py # Image analysis
│   ├── api_handler.py   # REST API interaction
│   ├── ml_handler.py    # ML model training/prediction
│   ├── chart_handler.py # Chart generation
│   ├── dom_handler.py   # DOM manipulation
│   ├── diff_handler.py  # Text diffing
│   ├── embedding_handler.py  # Vector similarity
│   └── llm_handler.py   # GPT-4 fallback
├── Dockerfile           # Containerized deployment
├── requirements.txt     # Python dependencies
└── .env.example         # Environment template
```

---

## Supported Tasks

| Category | Task Type | Description |
|----------|-----------|-------------|
| **CLI** | `uv_command` | Construct uv http commands with auth |
| **CLI** | `git_command` | Git add/commit operations |
| **CLI** | `file_path` | Identify correct file paths |
| **Data** | `csv` | Normalize, clean, transform CSV data |
| **Data** | `json_sort` | Sort JSON by fields, ascending/descending |
| **Data** | `logs` | Parse log files, sum bytes, count events |
| **Data** | `orders` | Top customers, running totals |
| **Data** | `shards` | Calculate optimal shard/replica configuration |
| **Data** | `rate` | Compute minimum time under rate limits |
| **Data** | `tweets` | Count tweets by sentiment |
| **API** | `github` | GitHub API tree traversal, count files |
| **API** | `api` | Custom headers, REST interaction |
| **Media** | `audio` | Transcribe audio files (.opus, .mp3) |
| **Media** | `image` | Analyze images (dominant color, heatmaps) |
| **Media** | `pdf` | Extract data from PDFs (invoices, tables) |
| **ML** | `ml` | Regression, classification, prediction |
| **ML** | `f1` | Calculate F1 score from predictions |
| **ML** | `embedding` | Vector similarity, RAG retrieval |
| **ML** | `tools` | Function calling, tool schema compliance |
| **Web** | `chart` | Generate plots, base64 visualization |
| **Web** | `dom` | JavaScript execution, DOM manipulation |
| **Web** | `diff` | Compare files, count changed lines |
| **Web** | `cache` | Cache-aware request handling |

---

## Quick Start

### Prerequisites
- Python 3.10+
- OpenAI API key

### Setup

```bash
# 1. Clone
git clone https://github.com/zetroretron/llm-quiz-solver.git
cd llm-quiz-solver

# 2. Install dependencies
pip install -r requirements.txt
playwright install

# 3. Configure environment
cp .env.example .env
# Edit .env with your OPENAI_API_KEY and STUDENT_SECRET
```

### Run

```bash
# Start the FastAPI server
uvicorn main:app --host 0.0.0.0 --port 8000

# Trigger a quiz solve
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "secret": "your_secret",
    "url": "https://quiz-url.com/task"
  }'
```

---

## API Reference

### `POST /run`

Trigger the quiz solver for a given quiz URL.

**Request Body:**

```json
{
  "email": "student@example.com",
  "secret": "your_defined_secret",
  "url": "https://quiz-url.com/task"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | Yes | Student email (used for personalization) |
| `secret` | string | Yes | Authentication secret (must match `STUDENT_SECRET`) |
| `url` | string (URL) | Yes | Quiz start URL |

**Response:**

```json
{
  "message": "Quiz solver started",
  "status": "processing"
}
```

### `GET /`

Health check endpoint.

**Response:**

```json
{
  "message": "LLM Analysis Quiz Solver is running"
}
```

---

## Deployment

### Docker

```bash
# Build
docker build -t quiz-solver .

# Run
docker run -p 8000:8000 --env-file .env quiz-solver
```

### Hugging Face Spaces

1. Create a new Space with **Docker** SDK
2. Upload: `Dockerfile`, `requirements.txt`, `main.py`, `solver_v2.py`, `tools.py`, `handlers/`
3. Add secrets: `OPENAI_API_KEY`, `STUDENT_SECRET`
4. Set hardware to **CPU Basic (Free)**
5. Your API endpoint: `https://<username>-<space-name>.hf.space/run`

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

---

## License

MIT License — see [LICENSE](LICENSE) for details.
