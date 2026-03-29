/**
 * Main App component that wires everything together.
 */

import { useEffect } from 'react';
import { Toaster } from 'react-hot-toast';
import { useAgentStore } from './store/useAgentStore';
import { useWebSocket } from './hooks/useWebSocket';
import { useAnalysis } from './hooks/useAnalysis';
import { FileUpload } from './components/FileUpload';
import { PromptInput } from './components/PromptInput';
import { StatusBadge } from './components/StatusBadge';
import { AgentTimeline } from './components/AgentTimeline';
import { ChartPanel } from './components/ChartPanel';
import { InsightCard } from './components/InsightCard';
import { Brain } from 'lucide-react';

function App() {
  const { sessionId, status, setInsights, setCharts, setStatus } = useAgentStore();
  const { getSessionStatus } = useAnalysis();

  // Connect to WebSocket when session is active
  useWebSocket({
    sessionId,
    onConnected: () => {},
    onDisconnected: () => {},
    onError: (error) => console.error('[App] WebSocket error:', error),
  });

  // Poll for results every 5 seconds when analyzing
  // This is a fallback in case WebSocket messages are lost
  useEffect(() => {
    if (!sessionId || status !== 'analyzing') {
      return;
    }

    const pollInterval = setInterval(async () => {
      const sessionData = await getSessionStatus(sessionId);

      if (sessionData) {
        // Update insights if available
        if (sessionData.insights) {
          setInsights(sessionData.insights);
          setStatus('done');
          clearInterval(pollInterval);
        }

        // Update charts if available
        if (sessionData.charts && sessionData.charts.length > 0) {
          setCharts(sessionData.charts);
        }
      }
    }, 5000); // Poll every 5 seconds

    return () => {
      clearInterval(pollInterval);
    };
  }, [sessionId, status, getSessionStatus, setInsights, setCharts, setStatus]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 flex flex-col">
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#fff',
            color: '#1f2937',
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
            border: '1px solid #e5e7eb',
          },
        }}
      />

      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-50 backdrop-blur-md bg-white/95">
        <div className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 py-5">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="p-2.5 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl shadow-md">
                <Brain className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 tracking-tight">
                  Autonomous Data Analyst
                </h1>
                <p className="text-sm text-gray-600 mt-0.5 font-medium">
                  AI-powered analysis with self-healing code generation
                </p>
              </div>
            </div>

            <StatusBadge />
          </div>
        </div>

        {/* Subtle accent line */}
        <div className="h-0.5 bg-gradient-to-r from-blue-500/50 via-indigo-500/50 to-purple-500/50"></div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-[1600px] w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 lg:py-12">
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 lg:gap-8">
          {/* Left Column: Input & Controls */}
          <div className="xl:col-span-5 space-y-6">
            {/* Upload Card */}
            <div className="bg-white rounded-xl shadow-md border border-gray-200 overflow-hidden hover:shadow-lg transition-shadow duration-300 animate-fadeIn">
              <div className="bg-gradient-to-r from-blue-50 to-indigo-50 px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-bold text-gray-900">Upload Dataset</h2>
                <p className="text-xs text-gray-600 mt-1">Upload CSV or Excel file to begin analysis</p>
              </div>
              <div className="p-6">
                <FileUpload />
              </div>
            </div>

            {/* Analysis Goal Card */}
            <div className="bg-white rounded-xl shadow-md border border-gray-200 overflow-hidden hover:shadow-lg transition-shadow duration-300 animate-fadeIn" style={{ animationDelay: '0.1s' }}>
              <div className="bg-gradient-to-r from-purple-50 to-pink-50 px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-bold text-gray-900">Analysis Goal</h2>
                <p className="text-xs text-gray-600 mt-1">Describe what you want to discover</p>
              </div>
              <div className="p-6">
                <PromptInput />
              </div>
            </div>

            {/* Insights Card - shown after analysis */}
            <div className="animate-fadeIn" style={{ animationDelay: '0.2s' }}>
              <InsightCard />
            </div>
          </div>

          {/* Right Column: Timeline & Results */}
          <div className="xl:col-span-7 space-y-6">
            <div className="animate-fadeIn" style={{ animationDelay: '0.15s' }}>
              <AgentTimeline />
            </div>

            <div className="animate-fadeIn" style={{ animationDelay: '0.25s' }}>
              <ChartPanel />
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="mt-auto bg-gradient-to-r from-gray-900 via-slate-800 to-gray-900 border-t border-gray-700 shadow-2xl">
        <div className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            {/* Left side - Branding */}
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <div>
                <p className="text-white font-bold text-sm">Autonomous Data Analyst</p>
                <p className="text-gray-400 text-xs">Intelligent insights, autonomously</p>
              </div>
            </div>

            {/* Center - Tech stack */}
            <div className="flex flex-wrap items-center justify-center gap-4">
              <div className="flex items-center gap-2 px-3 py-1.5 bg-white/5 rounded-lg border border-white/10">
                <div className="w-2 h-2 rounded-full bg-blue-400"></div>
                <span className="text-xs text-gray-300 font-medium">LangGraph</span>
              </div>
              <div className="flex items-center gap-2 px-3 py-1.5 bg-white/5 rounded-lg border border-white/10">
                <div className="w-2 h-2 rounded-full bg-green-400"></div>
                <span className="text-xs text-gray-300 font-medium">GPT-4o</span>
              </div>
              <div className="flex items-center gap-2 px-3 py-1.5 bg-white/5 rounded-lg border border-white/10">
                <div className="w-2 h-2 rounded-full bg-purple-400"></div>
                <span className="text-xs text-gray-300 font-medium">HuggingFace</span>
              </div>
            </div>

            {/* Right side - Status */}
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 px-4 py-2 bg-green-500/10 rounded-lg border border-green-500/20">
                <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                <span className="text-xs text-green-400 font-semibold">System Online</span>
              </div>
            </div>
          </div>

          {/* Bottom copyright */}
          <div className="mt-6 pt-6 border-t border-gray-700">
            <p className="text-center text-xs text-gray-500">
              © 2024 Autonomous Data Analyst. Production-grade agentic AI system.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
