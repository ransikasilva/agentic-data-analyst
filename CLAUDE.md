# CLAUDE.md — Autonomous Data Analyst Agent

> This file is the single source of truth for Claude Code when building this project.
> Read every section before writing any code. Follow these rules strictly.

---

## Project Overview

An **Autonomous Data Analyst Agent** that accepts a CSV/Excel file and a natural language goal,
then autonomously plans, writes Python code, executes it, debugs errors in a self-healing retry
loop, generates visualizations, and surfaces everything in a React frontend.

**Core value proposition for the CV:** This demonstrates a full agentic loop —
planning → code generation → execution → error recovery → visualization — using the
latest production frameworks (LangGraph, OpenAI, HuggingFace), not just a simple chatbot.

---

## Tech Stack

### Backend
| Layer | Technology | Version | Purpose |
|---|---|---|---|
| Agent orchestration | `langgraph` | >=0.2.0 | Stateful graph, checkpointing, retry loops |
| LLM (primary) | `openai` | >=1.30.0 | GPT-4o for planning, coding, debugging |
| LLM (fallback/embeddings) | `transformers` + `huggingface_hub` | latest | Open-source model fallback, embeddings |
| Code execution | `RestrictedPython` + subprocess sandbox | latest | Safe Python execution |
| Data tools | `pandas`, `numpy`, `sqlalchemy` | latest | Data manipulation |
| Visualization | `matplotlib`, `plotly` | latest | Chart generation |
| API server | `fastapi` | >=0.110.0 | REST + WebSocket endpoints |
| WebSocket | `websockets` via FastAPI | built-in | Real-time agent streaming to frontend |
| File parsing | `openpyxl`, `python-multipart` | latest | CSV and Excel ingestion |
| State persistence | `langgraph-checkpoint-sqlite` | latest | Session memory across requests |
| Environment | `python-dotenv` | latest | Secrets management |

### Frontend
| Layer | Technology | Purpose |
|---|---|---|
| Framework | React 18 + TypeScript | Component UI |
| Build tool | Vite | Fast dev server |
| Styling | Tailwind CSS v3 | Utility-first styling |
| Charts | Recharts | Render Plotly/Matplotlib outputs |
| File upload | react-dropzone | Drag-and-drop CSV/Excel upload |
| State management | Zustand | Lightweight global state |
| WebSocket client | native browser WebSocket | Real-time agent step streaming |
| HTTP client | axios | REST calls to FastAPI |
| Icons | lucide-react | Clean icon set |
| Notifications | react-hot-toast | Agent status toasts |

---

## Project Structure

```
autonomous-data-analyst/
├── CLAUDE.md                        ← this file
│
├── backend/
│   ├── main.py                      ← FastAPI app entry point
│   ├── requirements.txt             ← all Python deps pinned
│   ├── .env.example                 ← env var template
│   │
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── graph.py                 ← LangGraph state graph definition
│   │   ├── state.py                 ← AgentState TypedDict
│   │   ├── nodes/
│   │   │   ├── __init__.py
│   │   │   ├── planner.py           ← Planner agent node
│   │   │   ├── coder.py             ← Coder agent node
│   │   │   ├── critic.py            ← Critic/Debugger agent node
│   │   │   └── summarizer.py        ← Final insight summarizer node
│   │   └── tools/
│   │       ├── __init__.py
│   │       ├── executor.py          ← sandboxed Python code runner
│   │       ├── data_tools.py        ← pandas/numpy helpers
│   │       └── viz_tools.py         ← chart generation helpers
│   │
│   ├── models/
│   │   ├── openai_client.py         ← OpenAI wrapper with retry + cost tracking
│   │   └── hf_client.py             ← HuggingFace client for embeddings/fallback
│   │
│   ├── api/
│   │   ├── routes.py                ← REST endpoints
│   │   └── websocket.py             ← WebSocket streaming handler
│   │
│   └── utils/
│       ├── file_parser.py           ← CSV/Excel → pandas DataFrame
│       └── session.py               ← Session management helpers
│
├── frontend/
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── package.json
│   │
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       │
│       ├── components/
│       │   ├── FileUpload.tsx        ← drag-and-drop upload zone
│       │   ├── PromptInput.tsx       ← natural language goal input
│       │   ├── AgentTimeline.tsx     ← real-time agent step stream
│       │   ├── CodeBlock.tsx         ← syntax-highlighted generated code
│       │   ├── ChartPanel.tsx        ← renders returned charts
│       │   ├── InsightCard.tsx       ← final insight summary card
│       │   └── StatusBadge.tsx       ← running / success / error badge
│       │
│       ├── store/
│       │   └── useAgentStore.ts      ← Zustand store
│       │
│       ├── hooks/
│       │   ├── useWebSocket.ts       ← WS connection + message handling
│       │   └── useAnalysis.ts        ← analysis session lifecycle
│       │
│       └── types/
│           └── agent.ts              ← shared TypeScript interfaces
│
└── docker-compose.yml               ← optional: spin up backend + frontend together
```

---

## Environment Variables

Create `backend/.env` based on `backend/.env.example`:

```env
# Required
OPENAI_API_KEY=sk-...

# Optional — HuggingFace (for embeddings + fallback model)
HF_TOKEN=hf_...
HF_FALLBACK_MODEL=mistralai/Mistral-7B-Instruct-v0.2

# Server
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=http://localhost:5173

# LangGraph checkpointing
SQLITE_DB_PATH=./sessions.db

# Code execution limits
MAX_EXECUTION_SECONDS=30
MAX_RETRY_ATTEMPTS=3
```

Never commit `.env`. Only commit `.env.example` with empty values.

---

## Agent Architecture — LangGraph State Graph

### AgentState (backend/agent/state.py)

```python
from typing import TypedDict, Annotated, List, Optional
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # Core inputs
    dataset_path: str               # path to uploaded file
    user_goal: str                  # natural language analysis goal
    session_id: str

    # Planning
    plan: List[str]                 # ordered list of sub-tasks from planner
    current_step: int               # which step we are on

    # Coding
    generated_code: str             # latest code written by coder
    code_history: List[str]         # all code versions (for debugging context)

    # Execution
    execution_result: Optional[str] # stdout from code execution
    execution_error: Optional[str]  # stderr / traceback if failed
    retry_count: int                # how many times critic has retried

    # Outputs
    charts: List[str]               # base64-encoded chart images
    insights: str                   # final natural language summary

    # Streaming
    messages: Annotated[list, add_messages]  # for real-time WS streaming
```

### Graph Flow (backend/agent/graph.py)

```
START
  │
  ▼
[planner_node]          → reads dataset schema + user goal → outputs plan[]
  │
  ▼
[coder_node]            → takes plan[current_step] → writes Python code
  │
  ▼
[executor_tool]         → runs code in sandbox → returns result or error
  │
  ├─ success ──────────► [next_step_router]
  │                           │
  │                           ├─ more steps → back to [coder_node]
  │                           └─ all done  → [summarizer_node] → END
  │
  └─ error ────────────► [critic_node]
                              │
                              ├─ retry_count < MAX → back to [coder_node]
                              └─ retry_count >= MAX → [error_handler] → END
```

This graph must be built with `StateGraph(AgentState)`. Use `.add_node()`,
`.add_edge()`, and `.add_conditional_edges()`. Compile with a SQLite checkpointer
so sessions survive restarts.

---

## Agent Nodes — Detailed Spec

### 1. Planner Node (`backend/agent/nodes/planner.py`)

**Input:** `dataset_path`, `user_goal`
**Output:** `plan: List[str]`

- First, read the dataset using pandas and extract: shape, column names, dtypes, first 5 rows, and null counts.
- Send a structured prompt to GPT-4o with this schema info + user goal.
- Ask GPT-4o to return a JSON array of 3-6 specific, executable sub-tasks.
- Each task must be a concrete Python operation (not vague like "analyze data").
- Example output: `["Load the CSV and print shape", "Drop rows where Revenue is null", "Group by Month and sum Revenue", "Plot a bar chart of monthly revenue", "Find the top 3 months"]`
- Parse and validate the JSON. Retry once if malformed.

### 2. Coder Node (`backend/agent/nodes/coder.py`)

**Input:** `plan`, `current_step`, `execution_error` (if retrying), `code_history`
**Output:** `generated_code: str`

- Prompt GPT-4o with: current sub-task, dataset path, previous error (if any), previous code (if retrying).
- System prompt must specify: use pandas/matplotlib/plotly, save charts to `./output/chart_{n}.png`, print final result, use the exact dataset path provided.
- If retrying after an error, include the full traceback in the prompt and instruct it to fix specifically that error.
- Return only the Python code block, no markdown fences.
- Append to `code_history` for debugging context.

### 3. Critic / Debugger Node (`backend/agent/nodes/critic.py`)

**Input:** `execution_error`, `generated_code`, `retry_count`
**Output:** Decision to retry or escalate. Increments `retry_count`.

- If `execution_error` is not None, check `retry_count < MAX_RETRY_ATTEMPTS`.
- If can retry: set `execution_error` to a cleaned version of the traceback, route back to coder.
- If max retries reached: write a human-readable error message to `insights` and route to END.
- Log every retry attempt with the error type for observability.

### 4. Summarizer Node (`backend/agent/nodes/summarizer.py`)

**Input:** All `execution_result` outputs, `charts`, `user_goal`
**Output:** `insights: str`

- Prompt GPT-4o with all execution outputs and the original user goal.
- Ask for a concise, non-technical summary: key findings, anomalies, and actionable recommendations.
- Format as markdown with bullet points.
- Include references to which chart shows what.

---

## Code Executor Tool (`backend/agent/tools/executor.py`)

This is the most critical and dangerous component. Follow these rules exactly:

```python
# Execution must:
# 1. Run in a subprocess with a timeout (MAX_EXECUTION_SECONDS)
# 2. Capture both stdout and stderr separately
# 3. Kill the process if timeout exceeded
# 4. Never allow file system writes outside ./output/
# 5. Never allow network calls from inside executed code
# 6. Return (stdout, stderr, exit_code) tuple

import subprocess, tempfile, os

def execute_code(code: str, dataset_path: str, session_id: str) -> tuple[str, str, int]:
    output_dir = f"./output/{session_id}"
    os.makedirs(output_dir, exist_ok=True)

    # Prepend safety header to every code block
    safe_header = f"""
import os, sys
os.chdir("{output_dir}")
DATASET_PATH = "{dataset_path}"
"""
    full_code = safe_header + code

    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write(full_code)
        tmp_path = f.name

    try:
        result = subprocess.run(
            ["python", tmp_path],
            capture_output=True, text=True,
            timeout=int(os.getenv("MAX_EXECUTION_SECONDS", 30))
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "TimeoutError: code exceeded execution limit", 1
    finally:
        os.unlink(tmp_path)
```

---

## HuggingFace Integration (`backend/models/hf_client.py`)

Use HuggingFace for two things:

1. **Embeddings** — embed the dataset column descriptions for semantic search later.
   Use `sentence-transformers/all-MiniLM-L6-v2` (free, fast, no GPU needed).

2. **LLM Fallback** — if OpenAI API fails or cost is a concern, fall back to
   `mistralai/Mistral-7B-Instruct-v0.2` via `huggingface_hub.InferenceClient`.

```python
from huggingface_hub import InferenceClient
from sentence_transformers import SentenceTransformer

embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def get_embeddings(texts: list[str]) -> list[list[float]]:
    return embedding_model.encode(texts).tolist()

def hf_fallback_completion(prompt: str) -> str:
    client = InferenceClient(token=os.getenv("HF_TOKEN"))
    response = client.text_generation(
        prompt,
        model=os.getenv("HF_FALLBACK_MODEL"),
        max_new_tokens=1024,
        temperature=0.2
    )
    return response
```

---

## FastAPI Backend (`backend/main.py` + `backend/api/`)

### REST Endpoints

```
POST   /api/upload              → upload CSV/Excel, returns session_id + dataset_preview
POST   /api/analyze             → start analysis (session_id + goal), returns job_id
GET    /api/session/{session_id} → get full session state + results
GET    /api/health              → health check
```

### WebSocket Endpoint

```
WS     /ws/{session_id}         → streams agent steps in real-time
```

WebSocket message format (JSON):
```json
{
  "type": "agent_step",
  "node": "planner | coder | critic | executor | summarizer",
  "status": "running | success | error",
  "data": {
    "message": "human-readable description",
    "code": "generated code if applicable",
    "result": "execution output if applicable",
    "retry_count": 0
  },
  "timestamp": "ISO8601"
}
```

Every LangGraph node must emit a WebSocket message at start AND completion.
Use `asyncio.Queue` to bridge the sync LangGraph execution with async FastAPI WebSocket.

### CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## React Frontend — Component Spec

### App Layout

```
┌─────────────────────────────────────────┐
│  Header: "Autonomous Data Analyst"      │
├──────────────┬──────────────────────────┤
│              │  AgentTimeline           │
│  FileUpload  │  (real-time steps)       │
│              │                          │
│  PromptInput ├──────────────────────────┤
│              │  ChartPanel              │
│  [Analyze]   │  (generated charts)      │
│              │                          │
│  StatusBadge ├──────────────────────────┤
│              │  InsightCard             │
│              │  (final summary)         │
└──────────────┴──────────────────────────┘
```

### Zustand Store (`src/store/useAgentStore.ts`)

```typescript
interface AgentStore {
  sessionId: string | null
  status: 'idle' | 'uploading' | 'analyzing' | 'done' | 'error'
  agentSteps: AgentStep[]
  charts: string[]           // base64 image strings
  insights: string           // markdown string
  dataPreview: DataPreview | null

  // Actions
  setSessionId: (id: string) => void
  addAgentStep: (step: AgentStep) => void
  setCharts: (charts: string[]) => void
  setInsights: (text: string) => void
  reset: () => void
}
```

### AgentTimeline Component

- Shows each agent node (Planner, Coder, Executor, Critic, Summarizer) as a vertical timeline.
- Each step has: icon, node name, status badge, expandable code block or result text.
- Steps stream in via WebSocket in real-time — animate each step entering with a fade-in.
- Retry steps shown with a warning color and retry count badge.
- Auto-scroll to latest step.

### ChartPanel Component

- Grid of chart images returned from the backend.
- Each chart is base64 PNG — render with `<img src={`data:image/png;base64,${chart}`} />`.
- Click to expand full-screen modal.
- Download button per chart.

### FileUpload Component

- Use `react-dropzone` for drag-and-drop.
- Accept `.csv`, `.xlsx`, `.xls` only.
- Show file name + size after upload.
- On upload success, show a data preview table (first 5 rows from API response).
- Max file size: 50MB — show error if exceeded.

---

## TypeScript Interfaces (`src/types/agent.ts`)

```typescript
export interface AgentStep {
  id: string
  node: 'planner' | 'coder' | 'critic' | 'executor' | 'summarizer'
  status: 'running' | 'success' | 'error'
  message: string
  code?: string
  result?: string
  retryCount?: number
  timestamp: string
}

export interface DataPreview {
  columns: string[]
  dtypes: Record<string, string>
  rows: Record<string, unknown>[]
  shape: [number, number]
  nullCounts: Record<string, number>
}

export interface AnalysisRequest {
  sessionId: string
  goal: string
}

export interface AnalysisResponse {
  jobId: string
  status: string
}
```

---

## Coding Standards

### Python
- Use type hints everywhere — no untyped functions.
- Use `async/await` for all FastAPI route handlers.
- All agent nodes must be `async def`.
- Use `loguru` for logging — not `print()`.
- Every function must have a docstring.
- Handle all OpenAI API errors: `RateLimitError`, `APIConnectionError`, `AuthenticationError`.
- Use `pydantic` models for all API request/response bodies.

### TypeScript / React
- Functional components only — no class components.
- All props must have explicit TypeScript interfaces.
- Use `async/await` — no `.then()` chains.
- No `any` types. Use `unknown` and narrow it.
- Custom hooks for all side effects (WebSocket, API calls).
- Tailwind only for styling — no inline styles, no CSS modules.
- All user-facing strings in constants — no magic strings in JSX.

### General
- No hardcoded API keys anywhere in source code.
- All secrets via environment variables only.
- Git ignore: `.env`, `*.db`, `output/`, `__pycache__/`, `node_modules/`, `dist/`.

---

## Error Handling Strategy

| Error Type | Where | How to Handle |
|---|---|---|
| OpenAI rate limit | `openai_client.py` | Exponential backoff, max 3 retries, then HF fallback |
| Code execution timeout | `executor.py` | Kill subprocess, return timeout error to critic node |
| Code execution error | `executor.py` | Capture stderr, pass to critic for retry |
| Max retries exceeded | `critic.py` | Write graceful error to `insights`, end graph |
| File parse error | `file_parser.py` | Return 400 with specific message (bad encoding, empty file, etc.) |
| WebSocket disconnect | `websocket.py` | Log and clean up session, don't crash server |
| HF API error | `hf_client.py` | Log and return None — caller decides fallback |

---

## Running the Project

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # fill in your OPENAI_API_KEY
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev                     # starts on http://localhost:5173
```

### Both together (Docker)
```bash
docker-compose up --build
```

---

## Build Order — Follow This Sequence

Claude Code should build in this exact order. Do not skip ahead.

```
Step 1  backend/agent/state.py              ← AgentState TypedDict
Step 2  backend/utils/file_parser.py        ← CSV/Excel → DataFrame
Step 3  backend/agent/tools/executor.py     ← sandboxed code runner
Step 4  backend/agent/nodes/planner.py      ← Planner node
Step 5  backend/agent/nodes/coder.py        ← Coder node
Step 6  backend/agent/nodes/critic.py       ← Critic node
Step 7  backend/agent/nodes/summarizer.py   ← Summarizer node
Step 8  backend/agent/graph.py              ← wire up LangGraph
Step 9  backend/models/openai_client.py     ← OpenAI wrapper
Step 10 backend/models/hf_client.py         ← HuggingFace client
Step 11 backend/api/websocket.py            ← WS streaming handler
Step 12 backend/api/routes.py               ← REST endpoints
Step 13 backend/main.py                     ← FastAPI app
Step 14 backend/requirements.txt            ← pin all deps

Step 15 frontend/src/types/agent.ts         ← TypeScript interfaces
Step 16 frontend/src/store/useAgentStore.ts ← Zustand store
Step 17 frontend/src/hooks/useWebSocket.ts  ← WS hook
Step 18 frontend/src/hooks/useAnalysis.ts   ← analysis lifecycle hook
Step 19 frontend/src/components/FileUpload.tsx
Step 20 frontend/src/components/PromptInput.tsx
Step 21 frontend/src/components/StatusBadge.tsx
Step 22 frontend/src/components/CodeBlock.tsx
Step 23 frontend/src/components/AgentTimeline.tsx
Step 24 frontend/src/components/ChartPanel.tsx
Step 25 frontend/src/components/InsightCard.tsx
Step 26 frontend/src/App.tsx                ← wire everything together
Step 27 docker-compose.yml                  ← optional containerization
```

---

## CV / Portfolio Presentation Tips

When describing this project on your CV:

> **Autonomous Data Analyst Agent** — Built a production-grade multi-agent AI system using
> LangGraph (stateful graph orchestration), OpenAI GPT-4o, and HuggingFace transformers.
> The system autonomously plans analysis tasks, generates and executes Python code in a
> sandboxed environment, self-heals from errors via a Critic/Debugger retry loop, and
> renders insights and charts in a React/TypeScript UI via real-time WebSocket streaming.

**Key talking points in interviews:**
- Why LangGraph over CrewAI → stateful checkpointing, durable execution, precise control flow
- How the retry loop works → critic reads traceback, patches code, re-executes, max N attempts
- Why HuggingFace is included → cost optimization, embeddings, fallback model strategy
- Security → sandboxed subprocess execution, no network access from generated code
- Real-time streaming → WebSocket + asyncio.Queue bridging sync LangGraph with async FastAPI

---

*Last updated: March 2026 | Stack versions verified against LangGraph 1.0.x, OpenAI SDK 1.x, React 18*