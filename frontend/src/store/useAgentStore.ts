/**
 * Zustand store for global agent state management.
 *
 * This store manages the application state including session data,
 * agent steps, status, and results.
 */

import { create } from 'zustand';
import { AgentStep, DataPreview, AnalysisStatus } from '../types/agent';

interface AgentStore {
  // Session state
  sessionId: string | null;
  status: AnalysisStatus;
  filename: string | null;

  // Agent execution state
  agentSteps: AgentStep[];
  charts: string[];
  insights: string;
  dataPreview: DataPreview | null;
  error: string | null;

  // Actions
  setSessionId: (id: string) => void;
  setFilename: (name: string) => void;
  setStatus: (status: AnalysisStatus) => void;
  setDataPreview: (preview: DataPreview) => void;
  addAgentStep: (step: AgentStep) => void;
  updateAgentStep: (id: string, updates: Partial<AgentStep>) => void;
  setCharts: (charts: string[]) => void;
  addChart: (chart: string) => void;
  setInsights: (text: string) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

const initialState = {
  sessionId: null,
  status: 'idle' as AnalysisStatus,
  filename: null,
  agentSteps: [],
  charts: [],
  insights: '',
  dataPreview: null,
  error: null,
};

export const useAgentStore = create<AgentStore>((set) => ({
  ...initialState,

  setSessionId: (id) => set({ sessionId: id }),

  setFilename: (name) => set({ filename: name }),

  setStatus: (status) => set({ status }),

  setDataPreview: (preview) => set({ dataPreview: preview }),

  addAgentStep: (step) =>
    set((state) => ({
      agentSteps: [...state.agentSteps, step],
    })),

  updateAgentStep: (id, updates) =>
    set((state) => ({
      agentSteps: state.agentSteps.map((step) =>
        step.id === id ? { ...step, ...updates } : step
      ),
    })),

  setCharts: (charts) => set({ charts }),

  addChart: (chart) =>
    set((state) => ({
      charts: [...state.charts, chart],
    })),

  setInsights: (text) => set({ insights: text }),

  setError: (error) => set({ error }),

  reset: () => set(initialState),
}));
