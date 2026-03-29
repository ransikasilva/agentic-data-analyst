/**
 * Analysis hook for managing the full analysis lifecycle.
 *
 * Handles file upload, analysis initiation, and session state management.
 */

import { useState, useCallback } from 'react';
import axios from 'axios';
import { useAgentStore } from '../store/useAgentStore';
import {
  UploadResponse,
  AnalysisRequest,
  AnalysisResponse,
  SessionResponse,
} from '../types/agent';
import toast from 'react-hot-toast';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function useAnalysis() {
  const [isUploading, setIsUploading] = useState(false);
  const [isStarting, setIsStarting] = useState(false);

  const {
    sessionId,
    setSessionId,
    setFilename,
    setStatus,
    setDataPreview,
    setError,
    reset,
  } = useAgentStore();

  const uploadFile = useCallback(
    async (file: File): Promise<UploadResponse | null> => {
      if (!file) {
        toast.error('No file selected');
        return null;
      }

      // Validate file type
      const allowedExtensions = ['.csv', '.xlsx', '.xls'];
      const fileExtension = file.name.toLowerCase().slice(file.name.lastIndexOf('.'));

      if (!allowedExtensions.includes(fileExtension)) {
        toast.error(`Invalid file type. Allowed: ${allowedExtensions.join(', ')}`);
        return null;
      }

      // Validate file size (50MB max)
      const maxSizeMB = 50;
      const fileSizeMB = file.size / (1024 * 1024);

      if (fileSizeMB > maxSizeMB) {
        toast.error(`File too large. Maximum size: ${maxSizeMB}MB`);
        return null;
      }

      setIsUploading(true);
      setStatus('uploading');
      setError(null);

      try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await axios.post<UploadResponse>(
          `${API_BASE_URL}/api/upload`,
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
            timeout: 60000, // 60 second timeout for large files
          }
        );

        const data = response.data;

        // Update store
        setSessionId(data.session_id);
        setFilename(data.filename);
        setDataPreview(data.dataset_preview);
        setStatus('idle');

        toast.success(`File uploaded: ${data.filename}`);

        return data;
      } catch (error: unknown) {
        console.error('[Analysis] Upload failed:', error);

        let errorMessage = 'Failed to upload file';

        if (axios.isAxiosError(error)) {
          errorMessage = error.response?.data?.detail || error.message;
        } else if (error instanceof Error) {
          errorMessage = error.message;
        }

        setError(errorMessage);
        setStatus('error');
        toast.error(errorMessage);

        return null;
      } finally {
        setIsUploading(false);
      }
    },
    [setSessionId, setFilename, setDataPreview, setStatus, setError]
  );

  const startAnalysis = useCallback(
    async (goal: string): Promise<AnalysisResponse | null> => {
      if (!sessionId) {
        toast.error('No active session. Please upload a file first.');
        return null;
      }

      if (!goal.trim()) {
        toast.error('Please provide an analysis goal');
        return null;
      }

      setIsStarting(true);
      setError(null);

      try {
        const request: AnalysisRequest = {
          session_id: sessionId,
          goal: goal.trim(),
        };

        const response = await axios.post<AnalysisResponse>(
          `${API_BASE_URL}/api/analyze`,
          request,
          {
            headers: {
              'Content-Type': 'application/json',
            },
            timeout: 10000,
          }
        );

        const data = response.data;

        setStatus('analyzing');
        toast.success('Analysis started');

        return data;
      } catch (error: unknown) {
        console.error('[Analysis] Start failed:', error);

        let errorMessage = 'Failed to start analysis';

        if (axios.isAxiosError(error)) {
          errorMessage = error.response?.data?.detail || error.message;
        } else if (error instanceof Error) {
          errorMessage = error.message;
        }

        setError(errorMessage);
        setStatus('error');
        toast.error(errorMessage);

        return null;
      } finally {
        setIsStarting(false);
      }
    },
    [sessionId, setStatus, setError]
  );

  const getSessionStatus = useCallback(
    async (sid?: string): Promise<SessionResponse | null> => {
      const targetSessionId = sid || sessionId;

      if (!targetSessionId) {
        return null;
      }

      try {
        const response = await axios.get<SessionResponse>(
          `${API_BASE_URL}/api/session/${targetSessionId}`,
          {
            timeout: 5000,
          }
        );

        return response.data;
      } catch (error: unknown) {
        console.error('[Analysis] Get session failed:', error);

        if (axios.isAxiosError(error) && error.response?.status === 404) {
          return null;
        }

        let errorMessage = 'Failed to get session status';

        if (axios.isAxiosError(error)) {
          errorMessage = error.response?.data?.detail || error.message;
        } else if (error instanceof Error) {
          errorMessage = error.message;
        }

        toast.error(errorMessage);
        return null;
      }
    },
    [sessionId]
  );

  const resetAnalysis = useCallback(() => {
    reset();
    toast.success('Session reset');
  }, [reset]);

  return {
    // State
    sessionId,
    isUploading,
    isStarting,

    // Actions
    uploadFile,
    startAnalysis,
    getSessionStatus,
    resetAnalysis,
  };
}
