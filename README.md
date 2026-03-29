# Autonomous Data Analyst Agent

A production-grade multi-agent AI system that autonomously analyzes data through planning, code generation, execution, self-healing error recovery, and insight generation.

## Features

- **Autonomous Planning**: AI planner breaks down analysis goals into executable steps
- **Code Generation**: GPT-4o writes Python code for each analysis task
- **Sandboxed Execution**: Secure subprocess execution with timeout protection
- **Self-Healing**: Automatic error detection and retry with debugger agent
- **Visualization**: Auto-generates matplotlib/plotly charts
- **Real-Time Streaming**: WebSocket updates during analysis
- **Insight Generation**: Natural language summary of findings

## Tech Stack

### Backend
- **LangGraph** - Stateful agent orchestration
- **OpenAI GPT-4o** - Planning, coding, debugging, summarization
- **HuggingFace** - Embeddings & fallback LLM
- **FastAPI** - REST API & WebSocket
- **Pandas/Matplotlib** - Data processing & visualization

### Frontend
- **React 18 + TypeScript**
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Zustand** - State management
- **Axios** - HTTP client

## Quick Start

### Option 1: Docker (Recommended)

```bash
# 1. Clone and navigate
cd autonomous-data-analyst

# 2. Set up backend environment
cp backend/.env.example backend/.env
# Edit backend/.env and add your OPENAI_API_KEY

# 3. Run with Docker Compose
docker-compose up --build

# Backend: http://localhost:8000
# Frontend: http://localhost:5173
# API Docs: http://localhost:8000/docs
```

### Option 2: Manual Setup

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Run server
uvicorn main:app --reload --port 8000
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Set up environment (optional)
cp .env.example .env

# Run development server
npm run dev
```

## Usage

1. **Upload Dataset**: Drag and drop a CSV or Excel file
2. **Enter Goal**: Describe what you want to analyze in natural language
3. **Watch Agent Work**: Real-time timeline shows planning, coding, execution
4. **Review Results**: Charts and insights appear automatically

### Example Goals

- "Show me monthly revenue trends and identify the top 3 products"
- "Find correlations between customer age and purchase amount"
- "Create a geographic distribution of sales by region"
- "Identify outliers in the pricing data and explain them"

## Architecture

### Agent Flow

```
START → Planner → Coder → Executor → [Success?]
                                        ├─ Yes → Next Step/Summarizer → END
                                        └─ No → Critic → [Retry < 3?]
                                                          ├─ Yes → Coder (retry)
                                                          └─ No → END (error)
```

### Key Components

- **Planner Node**: Analyzes dataset schema, creates step-by-step plan
- **Coder Node**: Generates Python code for current task
- **Executor Node**: Runs code in sandboxed subprocess
- **Critic Node**: Debugs errors, decides retry strategy
- **Summarizer Node**: Generates natural language insights

## Configuration

### Backend (.env)

```env
OPENAI_API_KEY=sk-...           # Required
HF_TOKEN=hf_...                 # Optional (for HuggingFace fallback)
MAX_EXECUTION_SECONDS=30        # Code execution timeout
MAX_RETRY_ATTEMPTS=3            # Max retries per step
```

### Frontend (.env)

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## Security

- Code execution in isolated subprocess with timeout
- File writes restricted to session-specific output directory
- No network access from executed code
- 50MB file size limit
- Input validation on all API endpoints

## Development

### Run Tests

```bash
cd backend
pytest

cd frontend
npm test
```

### Code Formatting

```bash
# Backend
black backend/

# Frontend
npm run lint
```

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

- `POST /api/upload` - Upload dataset
- `POST /api/analyze` - Start analysis
- `GET /api/session/{session_id}` - Get session state
- `WS /ws/{session_id}` - Real-time updates

## Troubleshooting

### Backend Issues

**OpenAI API Errors**
- Verify `OPENAI_API_KEY` is set correctly
- Check API quota and rate limits

**Import Errors**
- Ensure all dependencies installed: `pip install -r requirements.txt`
- Check Python version (3.11+ recommended)

### Frontend Issues

**Connection Refused**
- Verify backend is running on port 8000
- Check CORS settings in backend/.env

**Build Errors**
- Clear node_modules: `rm -rf node_modules && npm install`
- Update npm: `npm install -g npm@latest`

## Contributing

This is a portfolio/CV project demonstrating:
- Multi-agent systems with LangGraph
- Production-grade error handling and retry logic
- Real-time streaming architectures
- Secure code execution sandboxing
- Modern React/TypeScript patterns

## License

MIT License - See LICENSE file for details

## Contact

Built to demonstrate advanced agentic AI architecture for CV/portfolio purposes.

For questions about implementation details or architectural decisions, refer to the inline documentation in the codebase.

---

**Tech Stack Summary for CV:**
LangGraph 0.2+ • OpenAI GPT-4o • HuggingFace Transformers • FastAPI • React 18 • TypeScript • Zustand • WebSocket • Pandas • Docker
