/**
 * StatusBadge component - Enhanced with better visual feedback
 */

import { CheckCircle, XCircle, Upload, FileText, Sparkles } from 'lucide-react';
import { useAgentStore } from '../store/useAgentStore';

interface StatusConfig {
  icon: typeof FileText;
  text: string;
  className: string;
  iconColor: string;
  animated?: boolean;
  pulseRing?: boolean;
  successAnimation?: boolean;
  shake?: boolean;
}

export function StatusBadge() {
  const { status } = useAgentStore();

  const statusConfig: Record<string, StatusConfig> = {
    idle: {
      icon: FileText,
      text: 'Ready to Analyze',
      className: 'bg-gradient-to-r from-gray-100 to-gray-200 text-gray-700 border-gray-300 shadow-sm',
      iconColor: 'text-gray-600',
    },
    uploading: {
      icon: Upload,
      text: 'Uploading File',
      className: 'bg-gradient-to-r from-blue-100 to-blue-200 text-blue-700 border-blue-300 shadow-md',
      iconColor: 'text-blue-600',
      animated: true,
      pulseRing: true,
    },
    analyzing: {
      icon: Sparkles,
      text: 'AI Analyzing',
      className: 'bg-gradient-to-r from-purple-100 to-indigo-200 text-indigo-700 border-indigo-300 shadow-md',
      iconColor: 'text-indigo-600',
      animated: true,
      pulseRing: true,
    },
    done: {
      icon: CheckCircle,
      text: 'Analysis Complete',
      className: 'bg-gradient-to-r from-green-100 to-emerald-200 text-green-700 border-green-300 shadow-md',
      iconColor: 'text-green-600',
      successAnimation: true,
    },
    error: {
      icon: XCircle,
      text: 'Error Occurred',
      className: 'bg-gradient-to-r from-red-100 to-red-200 text-red-700 border-red-300 shadow-md',
      iconColor: 'text-red-600',
      shake: true,
    },
  };

  const config = statusConfig[status];
  const Icon = config.icon;

  return (
    <div className="relative inline-flex">
      {/* Pulse ring for active states */}
      {config.pulseRing && (
        <span className="absolute inset-0 rounded-full bg-blue-400 opacity-75 animate-ping"></span>
      )}

      {/* Main badge */}
      <div
        className={`
          relative inline-flex items-center gap-2.5 px-5 py-2.5 rounded-full border-2
          font-bold text-sm transition-all duration-300 hover:scale-105
          ${config.className}
          ${config.shake ? 'animate-shake' : ''}
          ${config.successAnimation ? 'animate-scaleIn' : ''}
        `}
      >
        <Icon
          className={`
            w-5 h-5 ${config.iconColor}
            ${config.animated && status === 'uploading' ? 'animate-bounce' : ''}
            ${config.animated && status === 'analyzing' ? 'animate-spin' : ''}
          `}
        />
        <span className="tracking-wide">{config.text}</span>

        {/* Progress dots for analyzing */}
        {status === 'analyzing' && (
          <div className="flex gap-1 ml-1">
            <span className="w-1.5 h-1.5 bg-indigo-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
            <span className="w-1.5 h-1.5 bg-indigo-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
            <span className="w-1.5 h-1.5 bg-indigo-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
          </div>
        )}
      </div>
    </div>
  );
}
