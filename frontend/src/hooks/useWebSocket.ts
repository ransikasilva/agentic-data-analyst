/**
 * WebSocket hook for real-time agent communication.
 *
 * Manages WebSocket connection, message handling, and automatic reconnection.
 */

import { useEffect, useRef, useCallback } from 'react';
import { useAgentStore } from '../store/useAgentStore';
import {
  WebSocketMessage,
  AgentStepMessage,
  AnalysisCompleteMessage,
  AnalysisErrorMessage,
} from '../types/agent';

const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

interface UseWebSocketOptions {
  sessionId: string | null;
  onConnected?: () => void;
  onDisconnected?: () => void;
  onError?: (error: Event) => void;
}

export function useWebSocket(options: UseWebSocketOptions) {
  const { sessionId, onConnected, onDisconnected, onError } = options;

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const pingIntervalRef = useRef<number | null>(null);
  const shouldReconnectRef = useRef<boolean>(true);

  const { addAgentStep, setInsights, setError, setStatus } = useAgentStore();

  const handleMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);

        switch (message.type) {
          case 'connected':
            console.log('[WS] Connected to server');
            onConnected?.();
            break;

          case 'agent_step': {
            const stepMsg = message as AgentStepMessage;
            const step = {
              id: `${stepMsg.node}-${Date.now()}`,
              node: stepMsg.node,
              status: stepMsg.status,
              message: stepMsg.data.message,
              code: stepMsg.data.code,
              result: stepMsg.data.result,
              retryCount: stepMsg.data.retryCount || 0,
              timestamp: stepMsg.timestamp,
            };

            addAgentStep(step);
            break;
          }

          case 'analysis_started':
            console.log('[WS] Analysis started');
            setStatus('analyzing');
            break;

          case 'analysis_complete': {
            const completeMsg = message as AnalysisCompleteMessage;
            console.log('[WS] Analysis complete - waiting for polling to fetch results');
            // Don't set status to 'done' yet - let polling fetch the final results
            // The polling will set status to 'done' once it gets the insights
            break;
          }

          case 'analysis_error': {
            const errorMsg = message as AnalysisErrorMessage;
            console.error('[WS] Analysis error:', errorMsg.message);
            setError(errorMsg.message);
            setStatus('error');
            break;
          }

          case 'pong':
            // Heartbeat response
            break;

          default:
            console.warn('[WS] Unknown message type:', message.type);
        }
      } catch (error) {
        console.error('[WS] Failed to parse message:', error);
      }
    },
    [addAgentStep, setInsights, setError, setStatus, onConnected]
  );

  const connect = useCallback(() => {
    if (!sessionId) {
      console.log('[WS] No session ID, skipping connection');
      return;
    }

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('[WS] Already connected');
      return;
    }

    const wsUrl = `${WS_BASE_URL}/ws/${sessionId}`;
    console.log('[WS] Connecting to:', wsUrl);

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('[WS] Connection opened');

      // Start ping interval for keepalive
      pingIntervalRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }));
        }
      }, 30000); // Ping every 30 seconds
    };

    ws.onmessage = handleMessage;

    ws.onerror = (error) => {
      console.error('[WS] WebSocket error:', error);
      onError?.(error);
    };

    ws.onclose = () => {
      console.log('[WS] Connection closed');
      onDisconnected?.();

      // Clear ping interval
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
        pingIntervalRef.current = null;
      }

      // Only reconnect if we should and if we have a session
      if (sessionId && shouldReconnectRef.current) {
        reconnectTimeoutRef.current = window.setTimeout(() => {
          console.log('[WS] Attempting reconnection...');
          connect();
        }, 3000);
      }
    };

    wsRef.current = ws;
  }, [sessionId, handleMessage, onConnected, onDisconnected, onError]);

  const disconnect = useCallback(() => {
    console.log('[WS] Manually disconnecting');

    // Disable auto-reconnect
    shouldReconnectRef.current = false;

    // Clear reconnection timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    // Clear ping interval
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }

    // Close WebSocket
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const sendMessage = useCallback((message: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('[WS] Cannot send message: WebSocket not open');
    }
  }, []);

  // Connect when sessionId changes
  useEffect(() => {
    if (sessionId) {
      shouldReconnectRef.current = true;
      connect();
    }

    return () => {
      disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]); // Only reconnect when sessionId changes

  return {
    isConnected: wsRef.current?.readyState === WebSocket.OPEN,
    sendMessage,
    disconnect,
  };
}
