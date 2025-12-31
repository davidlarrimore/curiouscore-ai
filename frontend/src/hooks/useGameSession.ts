/**
 * useGameSession Hook
 *
 * Manages game session lifecycle for the new Game Master architecture.
 * Handles session creation, starting, answer submission, and state management.
 */

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

// Types
export interface GameSession {
  id: string;
  user_id: string;
  challenge_id: string;
  status: string;
  current_step_index: number;
  total_score: number;
  max_possible_score: number;
  mistakes_count: number;
  hints_used: number;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface DisplayMessage {
  role: string;
  content: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface UIResponse {
  ui_mode: string;
  step_index: number;
  total_steps: number;
  step_title: string;
  step_instruction: string;
  messages: DisplayMessage[];
  score: number;
  max_score: number;
  status: string;
  progress_percentage: number;
  options?: string[];  // For MCQ steps
}

export interface SessionStateResponse {
  session: GameSession;
  ui_response: UIResponse;
}

/**
 * Custom hook for managing game sessions
 */
export function useGameSession(challengeId: string) {
  const queryClient = useQueryClient();
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);

  // Fetch session state
  const { data: sessionState, isLoading, error, refetch } = useQuery<SessionStateResponse>({
    queryKey: ['session', currentSessionId],
    queryFn: async () => {
      if (!currentSessionId) throw new Error('No active session');
      const response = await api.get(`/sessions/${currentSessionId}/state`);
      return response as SessionStateResponse;
    },
    enabled: !!currentSessionId,
  });

  // Create session
  const createSessionMutation = useMutation({
    mutationFn: async () => {
      // API client returns unwrapped response directly
      const session = await api.post('/sessions', { challenge_id: challengeId });
      return session as GameSession;
    },
    onSuccess: (session) => {
      setCurrentSessionId(session.id);
    },
  });

  // Start session
  const startSessionMutation = useMutation({
    mutationFn: async (sessionId: string) => {
      // Execute narration for now to maintain existing UX
      // In future, can defer narration for faster initial load
      const response = await api.post(`/sessions/${sessionId}/start?execute_narration=true`);
      return response as SessionStateResponse;
    },
    onSuccess: (data) => {
      queryClient.setQueryData(['session', currentSessionId], data);
    },
  });

  // Submit answer
  const submitAnswerMutation = useMutation({
    mutationFn: async (answer: number | string | number[]) => {
      if (!currentSessionId) throw new Error('No active session');
      const response = await api.post(`/sessions/${currentSessionId}/attempt`, { answer });
      return response as SessionStateResponse;
    },
    onSuccess: (data) => {
      queryClient.setQueryData(['session', currentSessionId], data);
    },
  });

  // Submit action (continue, hint, etc.)
  const submitActionMutation = useMutation({
    mutationFn: async (action: string) => {
      if (!currentSessionId) throw new Error('No active session');
      const response = await api.post(`/sessions/${currentSessionId}/action`, { action });
      return response as SessionStateResponse;
    },
    onSuccess: (data) => {
      queryClient.setQueryData(['session', currentSessionId], data);
    },
  });

  // Helper functions
  const createAndStartSession = async () => {
    const session = await createSessionMutation.mutateAsync();
    await startSessionMutation.mutateAsync(session.id);
  };

  const submitAnswer = async (answer: number | string | number[]) => {
    await submitAnswerMutation.mutateAsync(answer);
  };

  const submitAction = async (action: string) => {
    await submitActionMutation.mutateAsync(action);
  };

  const requestHint = async () => {
    await submitAction('hint');
  };

  const resetSession = () => {
    setCurrentSessionId(null);
    queryClient.removeQueries({ queryKey: ['session'] });
  };

  return {
    // State
    session: sessionState?.session,
    uiResponse: sessionState?.ui_response,
    isLoading,
    error,

    // Session lifecycle
    createAndStartSession,
    submitAnswer,
    submitAction,
    requestHint,
    resetSession,
    refetch,

    // Mutations (for granular control)
    createSession: createSessionMutation.mutateAsync,
    startSession: startSessionMutation.mutateAsync,

    // Mutation states
    isCreating: createSessionMutation.isPending,
    isStarting: startSessionMutation.isPending,
    isSubmitting: submitAnswerMutation.isPending || submitActionMutation.isPending,
  };
}
