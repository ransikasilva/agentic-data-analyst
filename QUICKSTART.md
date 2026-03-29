# Quick Start Guide

## Installation Complete! ✅

Both frontend and backend dependencies are now installed.

## Running the Application

### Option 1: Use the Start Script (Recommended)

```bash
./start.sh
```

This will start both the backend and frontend servers automatically.

### Option 2: Manual Start

#### Terminal 1 - Backend:
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

#### Terminal 2 - Frontend:
```bash
cd frontend
npm run dev
```

## Access the Application

- **Frontend UI**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## First Steps

1. **Upload a Dataset**
   - Drag and drop a CSV or Excel file
   - Maximum file size: 50MB
   - Supported formats: .csv, .xlsx, .xls

2. **Enter Your Analysis Goal**
   - Example: "Show me monthly revenue trends"
   - Example: "Find correlations between customer age and purchase amount"
   - Example: "Create a chart of sales by region"

3. **Watch the Magic**
   - The AI agent will:
     - Plan the analysis steps
     - Generate Python code
     - Execute the code
     - Fix any errors automatically (up to 3 retries)
     - Generate visualizations
     - Provide insights

## Project Structure

```
autonomous-data-analyst/
├── backend/          ← Python FastAPI server
│   ├── agent/        ← LangGraph agent nodes
│   ├── api/          ← REST + WebSocket endpoints
│   ├── models/       ← OpenAI + HuggingFace clients
│   └── utils/        ← File parsing, helpers
│
├── frontend/         ← React + TypeScript UI
│   └── src/
│       ├── components/  ← UI components
│       ├── hooks/       ← Custom React hooks
│       ├── store/       ← Zustand state management
│       └── types/       ← TypeScript interfaces
│
└── start.sh         ← One-command startup
```

## Tech Stack Summary

**Backend:**
- LangGraph 1.1 (agent orchestration)
- OpenAI GPT-4o (AI models)
- FastAPI (REST + WebSocket)
- Pandas, Matplotlib, Plotly (data & viz)

**Frontend:**
- React 18 + TypeScript
- Tailwind CSS
- Zustand (state)
- Vite (build tool)

## Troubleshooting

### Backend won't start
- Ensure virtual environment is activated: `source venv/bin/activate`
- Check .env file has OPENAI_API_KEY set
- Verify Python 3.11+ is installed: `python3 --version`

### Frontend won't start
- Try deleting node_modules and reinstalling: `rm -rf node_modules && npm install`
- Check Node version: `node --version` (should be 18+)

### WebSocket connection fails
- Make sure backend is running on port 8000
- Check browser console for errors
- Verify CORS settings in backend/.env

## Next Steps

- Try the example datasets in `/examples` (if available)
- Experiment with different analysis goals
- Check the README.md for full documentation
- Explore the API docs at http://localhost:8000/docs

## Support

For issues or questions, refer to:
- README.md - Full documentation
- CLAUDE.md - Complete technical specification
- backend/main.py - Backend entry point
- frontend/src/App.tsx - Frontend entry point

Happy analyzing! 🚀
