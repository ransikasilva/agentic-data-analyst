/**
 * AgentTimeline component - Completely revamped with modern UI/UX
 */

import { useEffect, useRef, useState } from 'react';
import { useAgentStore } from '../store/useAgentStore';
import {
  Brain,
  Code,
  AlertTriangle,
  Play,
  FileText,
  CheckCircle,
  XCircle,
  Loader2,
  ChevronDown,
  ChevronUp,
  Copy,
  Check,
} from 'lucide-react';
import { AgentNodeType, AgentStepStatus } from '../types/agent';

const nodeIcons: Record<AgentNodeType, typeof Brain> = {
  planner: Brain,
  coder: Code,
  critic: AlertTriangle,
  executor: Play,
  summarizer: FileText,
};

const statusIcons: Record<AgentStepStatus, typeof CheckCircle> = {
  success: CheckCircle,
  error: XCircle,
  running: Loader2,
};

const statusColors: Record<AgentStepStatus, string> = {
  success: 'text-green-600 bg-green-50 border-green-200',
  error: 'text-red-600 bg-red-50 border-red-200',
  running: 'text-blue-600 bg-blue-50 border-blue-200',
};

const nodeColors: Record<AgentNodeType, string> = {
  planner: 'bg-purple-500',
  coder: 'bg-blue-500',
  critic: 'bg-yellow-500',
  executor: 'bg-green-500',
  summarizer: 'bg-indigo-500',
};

export function AgentTimeline() {
  const { agentSteps } = useAgentStore();
  const bottomRef = useRef<HTMLDivElement>(null);
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set());
  const [copiedId, setCopiedId] = useState<string | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [agentSteps]);

  const toggleExpand = (stepId: string) => {
    setExpandedSteps((prev) => {
      const next = new Set(prev);
      if (next.has(stepId)) {
        next.delete(stepId);
      } else {
        next.add(stepId);
      }
      return next;
    });
  };

  const copyCode = async (code: string, stepId: string) => {
    await navigator.clipboard.writeText(code);
    setCopiedId(stepId);
    setTimeout(() => setCopiedId(null), 2000);
  };

  if (agentSteps.length === 0) {
    return (
      <div className="bg-gradient-to-br from-white to-gray-50 rounded-xl border-2 border-dashed border-gray-300 p-12 text-center shadow-sm">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-gray-100 rounded-full mb-4">
          <Brain className="w-8 h-8 text-gray-400" />
        </div>
        <p className="text-gray-500 font-medium">Waiting for analysis to start...</p>
        <p className="text-gray-400 text-sm mt-2">Agent execution steps will appear here</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-lg overflow-hidden">
      <div className="bg-gradient-to-r from-indigo-500 to-purple-600 px-6 py-4">
        <h3 className="text-lg font-bold text-white flex items-center gap-2">
          <Brain className="w-5 h-5" />
          Agent Execution Timeline
        </h3>
        <p className="text-indigo-100 text-sm mt-1">
          {agentSteps.length} step{agentSteps.length !== 1 ? 's' : ''} executed
        </p>
      </div>

      <div className="p-6 max-h-[700px] overflow-y-auto custom-scrollbar">
        <div className="space-y-6">
          {agentSteps.map((step, idx) => {
            const NodeIcon = nodeIcons[step.node] || Brain;
            const StatusIcon = statusIcons[step.status] || Loader2;
            const isLast = idx === agentSteps.length - 1;
            const isExpanded = expandedSteps.has(step.id);
            const hasCode = !!step.code;
            const hasResult = !!step.result;

            return (
              <div
                key={step.id}
                className={`relative transition-all duration-300 ${
                  isLast ? 'animate-fadeIn' : ''
                }`}
              >
                {/* Connection Line */}
                {!isLast && (
                  <div className="absolute left-6 top-14 bottom-0 w-0.5 bg-gradient-to-b from-gray-300 to-transparent" />
                )}

                {/* Step Card */}
                <div
                  className={`
                    relative bg-gradient-to-br from-white to-gray-50 rounded-xl border-2
                    transition-all duration-300 hover:shadow-md
                    ${statusColors[step.status].includes('green') ? 'border-green-200' : ''}
                    ${statusColors[step.status].includes('red') ? 'border-red-200' : ''}
                    ${statusColors[step.status].includes('blue') ? 'border-blue-200' : ''}
                  `}
                >
                  <div className="p-4">
                    <div className="flex items-start gap-4">
                      {/* Icon */}
                      <div
                        className={`
                          flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center
                          shadow-lg ${nodeColors[step.node]} text-white
                          ${isLast && step.status === 'running' ? 'animate-pulse' : ''}
                        `}
                      >
                        <NodeIcon className="w-6 h-6" />
                      </div>

                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        {/* Header */}
                        <div className="flex items-center gap-2 mb-2 flex-wrap">
                          <h4 className="font-bold text-gray-900 capitalize text-lg">
                            {step.node}
                          </h4>
                          <StatusIcon
                            className={`w-5 h-5 flex-shrink-0 ${
                              step.status === 'running' ? 'animate-spin' : ''
                            } ${statusColors[step.status].split(' ')[0]}`}
                          />
                          {step.retryCount && step.retryCount > 0 && (
                            <span className="text-xs bg-yellow-100 text-yellow-700 px-2.5 py-1 rounded-full font-semibold">
                              Retry #{step.retryCount}
                            </span>
                          )}
                          <span className="text-xs text-gray-400 ml-auto">
                            {new Date(step.timestamp).toLocaleTimeString()}
                          </span>
                        </div>

                        {/* Message */}
                        <p className="text-sm text-gray-600 mb-3">{step.message}</p>

                        {/* Expandable Sections */}
                        {(hasCode || hasResult) && (
                          <div className="space-y-2">
                            {/* Code Block */}
                            {hasCode && (
                              <div className="border border-gray-200 rounded-lg overflow-hidden">
                                <button
                                  onClick={() => toggleExpand(step.id)}
                                  className="w-full flex items-center justify-between bg-gray-800 px-4 py-2.5 text-left hover:bg-gray-700 transition-colors"
                                >
                                  <span className="text-sm font-semibold text-gray-100 flex items-center gap-2">
                                    <Code className="w-4 h-4" />
                                    Generated Code
                                  </span>
                                  <div className="flex items-center gap-2">
                                    <button
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        copyCode(step.code!, step.id);
                                      }}
                                      className="p-1.5 hover:bg-gray-600 rounded transition-colors"
                                      title="Copy code"
                                    >
                                      {copiedId === step.id ? (
                                        <Check className="w-4 h-4 text-green-400" />
                                      ) : (
                                        <Copy className="w-4 h-4 text-gray-300" />
                                      )}
                                    </button>
                                    {isExpanded ? (
                                      <ChevronUp className="w-5 h-5 text-gray-300" />
                                    ) : (
                                      <ChevronDown className="w-5 h-5 text-gray-300" />
                                    )}
                                  </div>
                                </button>
                                {isExpanded && (
                                  <div className="bg-gray-900 p-4 max-h-96 overflow-auto custom-scrollbar">
                                    <pre className="text-sm text-gray-100 font-mono leading-relaxed">
                                      <code>{step.code}</code>
                                    </pre>
                                  </div>
                                )}
                              </div>
                            )}

                            {/* Result Block */}
                            {hasResult && (
                              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                                <p className="text-xs font-bold text-green-900 mb-2 flex items-center gap-1">
                                  <CheckCircle className="w-3 h-3" />
                                  Execution Output
                                </p>
                                <pre className="text-xs text-green-800 font-mono whitespace-pre-wrap max-h-48 overflow-auto custom-scrollbar">
                                  {step.result}
                                </pre>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        <div ref={bottomRef} />
      </div>
    </div>
  );
}
