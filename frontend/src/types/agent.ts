/**
 * TypeScript type definitions for the Autonomous Data Analyst Agent.
 *
 * These interfaces define the structure of data exchanged between
 * the frontend and backend.
 */

export type AgentNodeType = 'planner' | 'coder' | 'critic' | 'executor' | 'summarizer';
export type AgentStepStatus = 'running' | 'success' | 'error';
export type AnalysisStatus = 'idle' | 'uploading' | 'analyzing' | 'done' | 'error';

/**
 * Represents a single step in the agent execution timeline.
 */
export interface AgentStep {
  id: string;
  node: AgentNodeType;
  status: AgentStepStatus;
  message: string;
  code?: string;
  result?: string;
  retryCount?: number;
  timestamp: string;
}

/**
 * Dataset preview information returned after file upload.
 */
export interface DataPreview {
  columns: string[];
  dtypes: Record<string, string>;
  rows: Record<string, unknown>[];
  shape: [number, number];
  null_counts: Record<string, number>;
}

/**
 * Request body for starting an analysis.
 */
export interface AnalysisRequest {
  session_id: string;
  goal: string;
}

/**
 * Response from the analyze endpoint.
 */
export interface AnalysisResponse {
  job_id: string;
  status: string;
  message: string;
}

/**
 * Response from the upload endpoint.
 */
export interface UploadResponse {
  session_id: string;
  filename: string;
  dataset_preview: DataPreview;
  message: string;
}

/**
 * Response from the session status endpoint.
 */
export interface SessionResponse {
  session_id: string;
  status: string;
  plan: string[] | null;
  insights: string | null;
  charts: string[] | null;
  error: string | null;
}

/**
 * WebSocket message types from the backend.
 */
export type WebSocketMessageType =
  | 'connected'
  | 'agent_step'
  | 'analysis_started'
  | 'analysis_complete'
  | 'analysis_error'
  | 'pong';

/**
 * Base WebSocket message structure.
 */
export interface WebSocketMessage {
  type: WebSocketMessageType;
  timestamp: string;
  [key: string]: unknown;
}

/**
 * Agent step WebSocket message.
 */
export interface AgentStepMessage extends WebSocketMessage {
  type: 'agent_step';
  node: AgentNodeType;
  status: AgentStepStatus;
  data: {
    message: string;
    code?: string;
    result?: string;
    retryCount?: number;
  };
}

/**
 * Analysis started WebSocket message.
 */
export interface AnalysisStartedMessage extends WebSocketMessage {
  type: 'analysis_started';
  message: string;
}

/**
 * Analysis complete WebSocket message.
 */
export interface AnalysisCompleteMessage extends WebSocketMessage {
  type: 'analysis_complete';
  message: string;
}

/**
 * Analysis error WebSocket message.
 */
export interface AnalysisErrorMessage extends WebSocketMessage {
  type: 'analysis_error';
  message: string;
}

/**
 * Connection confirmation WebSocket message.
 */
export interface ConnectedMessage extends WebSocketMessage {
  type: 'connected';
  session_id: string;
  message: string;
}

/**
 * Pong response WebSocket message.
 */
export interface PongMessage extends WebSocketMessage {
  type: 'pong';
}
