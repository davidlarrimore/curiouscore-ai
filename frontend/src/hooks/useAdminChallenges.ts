import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Challenge } from './useChallenges';

interface ChallengeListParams {
  page?: number;
  limit?: number;
  search?: string;
  difficulty?: string;
}

interface ChallengeWithCount extends Challenge {
  step_count?: number;
}

interface ChallengeListResponse {
  items: ChallengeWithCount[];
  total: number;
  page: number;
  pages: number;
  limit: number;
}

interface ChallengeStep {
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

interface Persona {
  id: string;
  name: string;
  role: string;
  temperament: string;
  communication_style: string;
  knowledge_scope: string;
  facts: Record<string, unknown>;
  avatar_url?: string;
  challenge_id?: string;
  created_at: string;
  updated_at: string;
}

interface Scene {
  id: string;
  challenge_id: string;
  scene_index: number;
  title: string;
  description: string;
  background_media_url?: string;
  ambient_audio_url?: string;
  theme_accents?: Record<string, unknown>;
  active_speakers: string[];
  created_at: string;
}

interface KnowledgeBase {
  id: string;
  title: string;
  content: string;
  content_type: string;
  tags: string[];
  external_url?: string;
  challenge_id?: string;
  created_at: string;
  updated_at: string;
}

export interface ChallengeDetailed extends Challenge {
  steps: ChallengeStep[];
  personas: Persona[];
  scenes: Scene[];
  knowledge_base: KnowledgeBase[];
}

export interface ChallengeCreatePayload {
  title: string;
  description: string;
  tags: string[];
  difficulty: string;
  system_prompt: string;
  estimated_time_minutes: number;
  xp_reward: number;
  passing_score: number;
  help_resources: unknown[];
  is_active: boolean;
}

export function useAdminChallenges(params?: ChallengeListParams) {
  return useQuery({
    queryKey: ['admin-challenges', params],
    queryFn: async () => {
      const searchParams = new URLSearchParams();
      if (params?.page) searchParams.append('page', params.page.toString());
      if (params?.limit) searchParams.append('limit', params.limit.toString());
      if (params?.search) searchParams.append('search', params.search);
      if (params?.difficulty) searchParams.append('difficulty', params.difficulty);

      const query = searchParams.toString();
      return api.get<ChallengeListResponse>(`/admin/challenges${query ? `?${query}` : ''}`);
    },
  });
}

export function useAdminChallengeDetailed(challengeId: string | null) {
  return useQuery({
    queryKey: ['admin-challenge-detailed', challengeId],
    queryFn: async () => {
      if (!challengeId) return null;
      return api.get<ChallengeDetailed>(`/admin/challenges/${challengeId}`);
    },
    enabled: !!challengeId,
    staleTime: 0, // Always fetch fresh data
    gcTime: 0, // Don't cache (formerly cacheTime in v4)
  });
}

export function useCreateChallenge() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ChallengeCreatePayload) => api.post<Challenge>('/admin/challenges', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-challenges'] });
    },
  });
}

export function useUpdateChallenge() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<ChallengeCreatePayload> }) =>
      api.patch<Challenge>(`/admin/challenges/${id}`, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['admin-challenges'] });
      queryClient.invalidateQueries({ queryKey: ['admin-challenge-detailed', variables.id] });
    },
  });
}

export function useDeleteChallenge() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/admin/challenges/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-challenges'] });
    },
  });
}

// ============================================================================
// Simple Challenge Verification
// ============================================================================

export interface VerificationPayload {
  system_prompt: string;
  title: string;
  difficulty: string;
  run_llm?: boolean;
}

export interface HeuristicResult {
  score: number;
  passed: boolean;
  issues: string[];
  warnings: string[];
}

export interface LLMValidationResult {
  feedback: string;
  suggestions: string[];
  confidence: number;
}

export interface VerificationResult {
  tier1_heuristics: HeuristicResult;
  tier2_llm?: LLMValidationResult;
  tier3_test_available: boolean;
  overall_recommendation: "approve" | "review" | "reject";
}

export interface TestRunPayload {
  test_message: string;
}

export interface TestRunResult {
  success: boolean;
  content: string;
  metadata: any;
  raw_response: string;
  metadata_found: boolean;
}

export function useVerifyPrompt() {
  return useMutation({
    mutationFn: async (payload: VerificationPayload) => {
      const response = await api.post<VerificationResult>("/admin/challenges/verify-prompt", payload);
      return response;
    },
  });
}

export function useTestChallenge() {
  return useMutation({
    mutationFn: async ({ challengeId, payload }: { challengeId: string; payload: TestRunPayload }) => {
      const response = await api.post<TestRunResult>(
        `/admin/challenges/${challengeId}/test-run`,
        payload
      );
      return response;
    },
  });
}
