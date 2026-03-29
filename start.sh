#!/bin/bash

# Startup script for Autonomous Data Analyst Agent

echo "🚀 Starting Autonomous Data Analyst Agent..."
echo ""

# Check if .env exists
if [ ! -f backend/.env ]; then
    echo "❌ Error: backend/.env file not found!"
    echo "Please copy backend/.env.example to backend/.env and add your OPENAI_API_KEY"
    exit 1
fi

# Check if OPENAI_API_KEY is set
if ! grep -q "OPENAI_API_KEY=sk-" backend/.env; then
    echo "⚠️  Warning: OPENAI_API_KEY not set in backend/.env"
    echo "Please add your OpenAI API key to backend/.env"
    exit 1
fi

echo "✅ Environment validated"
echo ""

# Start backend
echo "📦 Starting backend server..."
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

echo "✅ Backend started (PID: $BACKEND_PID)"
echo "   API: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
echo ""

# Wait a bit for backend to start
sleep 3

# Start frontend
echo "🎨 Starting frontend server..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo "✅ Frontend started (PID: $FRONTEND_PID)"
echo "   App: http://localhost:5173"
echo ""

echo "═══════════════════════════════════════════════════"
echo "✨ Autonomous Data Analyst Agent is running!"
echo "═══════════════════════════════════════════════════"
echo ""
echo "  Frontend: http://localhost:5173"
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for user interrupt
trap "echo ''; echo '🛑 Stopping services...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo '✅ Services stopped'; exit 0" INT

# Keep script running
wait
