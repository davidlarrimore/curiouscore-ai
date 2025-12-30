import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

export interface ChallengeStep {
  id: string;
  challenge_id: string;
  step_index: number;
  step_type: string;
  title: string;
  instruction: string;
  options?: string[];
  correct_answer?: number;
  correct_answers?: number[];
  points_possible: number;
  passing_threshold: number;
  rubric?: Record<string, unknown>;
  gm_context?: string;
  auto_narrate: boolean;
  created_at: string;
}

export interface StepCreatePayload {
  challenge_id: string;
  step_index: number;
  step_type: string;
  title: string;
  instruction: string;
  options?: string[];
  correct_answer?: number;
  correct_answers?: number[];
  points_possible: number;
  passing_threshold: number;
  rubric?: Record<string, unknown>;
  gm_context?: string;
  auto_narrate: boolean;
}

export function useAdminSteps(challengeId: string | null) {
  return useQuery({
    queryKey: ['admin-steps', challengeId],
    queryFn: async () => {
      if (!challengeId) return [];
      return api.get<ChallengeStep[]>(`/admin/challenges/${challengeId}/steps`);
    },
    enabled: !!challengeId,
  });
}

export function useCreateStep() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ challengeId, data }: { challengeId: string; data: StepCreatePayload }) =>
      api.post<ChallengeStep>(`/admin/challenges/${challengeId}/steps`, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['admin-steps', variables.challengeId] });
      queryClient.invalidateQueries({ queryKey: ['admin-challenge-detailed', variables.challengeId] });
    },
  });
}

export function useUpdateStep() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      challengeId,
      stepId,
      data,
    }: {
      challengeId: string;
      stepId: string;
      data: Partial<StepCreatePayload>;
    }) => api.patch<ChallengeStep>(`/admin/challenges/${challengeId}/steps/${stepId}`, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['admin-steps', variables.challengeId] });
      queryClient.invalidateQueries({ queryKey: ['admin-challenge-detailed', variables.challengeId] });
    },
  });
}

export function useDeleteStep() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ challengeId, stepId }: { challengeId: string; stepId: string }) =>
      api.delete(`/admin/challenges/${challengeId}/steps/${stepId}`),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['admin-steps', variables.challengeId] });
      queryClient.invalidateQueries({ queryKey: ['admin-challenge-detailed', variables.challengeId] });
    },
  });
}

export function useReorderSteps() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ challengeId, stepIds }: { challengeId: string; stepIds: string[] }) =>
      api.patch<ChallengeStep[]>(`/admin/challenges/${challengeId}/steps/reorder`, { step_ids: stepIds }),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['admin-steps', variables.challengeId] });
      queryClient.invalidateQueries({ queryKey: ['admin-challenge-detailed', variables.challengeId] });
    },
  });
}
