/**
 * InsightCard component for displaying final analysis insights.
 */

import { useAgentStore } from '../store/useAgentStore';
import { Lightbulb } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

export function InsightCard() {
  const { insights } = useAgentStore();

  if (!insights) {
    return null;
  }

  return (
    <div className="bg-gradient-to-br from-amber-50 via-yellow-50 to-orange-50 rounded-xl border-2 border-amber-200 shadow-xl overflow-hidden animate-scaleIn">
      <div className="bg-gradient-to-r from-amber-100 to-yellow-100 px-6 py-4 border-b-2 border-amber-200">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-gradient-to-br from-amber-500 to-orange-500 rounded-xl shadow-lg">
            <Lightbulb className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-gray-900">Analysis Insights</h3>
            <p className="text-xs text-gray-600 mt-0.5">Key findings from your data</p>
          </div>
        </div>
      </div>

      <div className="p-6 bg-white/50 backdrop-blur-sm">
        <div className="prose prose-sm max-w-none">
          <ReactMarkdown
            components={{
              h2: ({ node, ...props }) => (
                <h2 className="text-lg font-bold text-gray-900 mt-5 mb-3 pb-2 border-b-2 border-amber-200" {...props} />
              ),
              h3: ({ node, ...props }) => (
                <h3 className="text-base font-bold text-gray-800 mt-4 mb-2" {...props} />
              ),
              p: ({ node, ...props }) => (
                <p className="text-gray-700 mb-4 leading-relaxed text-base" {...props} />
              ),
              ul: ({ node, ...props }) => (
                <ul className="space-y-2 mb-4 ml-1" {...props} />
              ),
              ol: ({ node, ...props }) => (
                <ol className="space-y-2 mb-4 ml-1" {...props} />
              ),
              li: ({ node, ...props }) => (
                <li className="text-gray-700 pl-2 flex items-start gap-2 before:content-['→'] before:text-amber-600 before:font-bold before:mr-1" {...props} />
              ),
              code: ({ node, ...props }) => (
                <code className="bg-amber-100 text-amber-900 px-2 py-1 rounded-md text-sm font-mono border border-amber-200" {...props} />
              ),
              strong: ({ node, ...props }) => (
                <strong className="font-bold text-gray-900 bg-amber-100 px-1 rounded" {...props} />
              ),
            }}
          >
            {insights}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
}
