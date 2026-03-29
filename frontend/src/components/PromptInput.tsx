/**
 * PromptInput component for entering analysis goals.
 */

import { useState } from 'react';
import { Send } from 'lucide-react';
import { useAnalysis } from '../hooks/useAnalysis';
import { useAgentStore } from '../store/useAgentStore';

export function PromptInput() {
  const [goal, setGoal] = useState('');
  const { startAnalysis, isStarting, sessionId } = useAnalysis();
  const { status } = useAgentStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!goal.trim() || !sessionId || isStarting) {
      return;
    }

    await startAnalysis(goal);
  };

  const isDisabled = !sessionId || isStarting || status === 'analyzing';

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1 relative">
          <input
            type="text"
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            placeholder="What would you like to analyze? (e.g., 'Show me monthly revenue trends and identify top products')"
            disabled={isDisabled}
            className="w-full px-5 py-4 pr-4 border-2 border-gray-300 rounded-xl
                     focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-100
                     disabled:bg-gray-100 disabled:cursor-not-allowed disabled:border-gray-200
                     transition-all duration-200 text-gray-800 placeholder:text-gray-400
                     shadow-sm hover:shadow-md hover:border-gray-400"
          />
          {goal.trim() && !isDisabled && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2">
              <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            </div>
          )}
        </div>
        <button
          type="submit"
          disabled={isDisabled || !goal.trim()}
          className="px-8 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl
                   hover:from-blue-700 hover:to-indigo-700 hover:shadow-lg
                   disabled:from-gray-300 disabled:to-gray-300 disabled:cursor-not-allowed disabled:shadow-none
                   transition-all duration-200 flex items-center justify-center gap-2 font-bold text-base
                   shadow-md active:scale-95 whitespace-nowrap"
        >
          {isStarting ? (
            <>
              <div className="relative w-5 h-5">
                <div className="animate-spin rounded-full h-5 w-5 border-2 border-white/30" />
                <div className="absolute inset-0 animate-spin rounded-full h-5 w-5 border-2 border-transparent border-t-white" style={{ animationDuration: '0.8s' }} />
              </div>
              Starting...
            </>
          ) : (
            <>
              <Send className="w-5 h-5" />
              Analyze
            </>
          )}
        </button>
      </div>
      {!sessionId && (
        <div className="mt-3 px-4 py-2.5 bg-amber-50 border border-amber-200 rounded-lg flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-amber-500" />
          <p className="text-sm text-amber-800 font-medium">Upload a dataset first to enable analysis</p>
        </div>
      )}
    </form>
  );
}
