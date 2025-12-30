import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

export type Provider = "openai" | "anthropic" | "gemini";

export interface ModelOption {
  id: string;
  provider: Provider;
  description?: string | null;
}

export interface ChallengeModelMapping {
  challenge_id: string;
  provider: Provider;
  model: string;
}

export function useLLMModels(provider: Provider | null) {
  return useQuery({
    queryKey: ['llm-models', provider],
    queryFn: async () => {
      if (!provider) return [];
      return api.get<ModelOption[]>(`/llm/models?provider=${provider}`);
    },
    enabled: !!provider,
  });
}

export function useChallengeModels() {
  return useQuery({
    queryKey: ['challenge-models'],
    queryFn: async () => {
      return api.get<ChallengeModelMapping[]>('/admin/challenges/models');
    },
  });
}

export function useUpdateChallengeModel() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ challengeId, provider, model }: { challengeId: string; provider: Provider; model: string }) =>
      api.put<ChallengeModelMapping>(`/admin/challenges/${challengeId}/model`, { provider, model }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['challenge-models'] });
      queryClient.invalidateQueries({ queryKey: ['admin-challenge-detailed'] });
    },
  });
}
