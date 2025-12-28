import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { useAuth } from "./useAuth";

export interface Challenge {
  id: string;
  title: string;
  description: string;
  tags: string[];
  difficulty: "beginner" | "intermediate" | "advanced" | "expert";
  system_prompt: string;
  estimated_time_minutes: number;
  xp_reward: number;
  passing_score: number;
  help_resources: HelpResource[];
  is_active: boolean;
  created_at: string;
}

export interface HelpResource {
  title: string;
  url: string;
  description: string;
}

export interface UserProgress {
  id: string;
  user_id: string;
  challenge_id: string;
  progress_percent: number;
  score: number;
  status: "not_started" | "in_progress" | "completed" | "failed";
  messages: ChatMessage[];
  current_phase: number;
  mistakes_count: number;
  started_at: string | null;
  completed_at: string | null;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  metadata?: MessageMetadata;
}

export interface MessageMetadata {
  questionType: "text" | "mcq";
  options: string[] | null;
  correctAnswer: number | null;
  phase: number;
  progressIncrement: number;
  scoreChange: number;
  hint: string | null;
  isComplete: boolean;
}

export function useChallenges() {
  const [challenges, setChallenges] = useState<Challenge[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchChallenges();
  }, []);

  const fetchChallenges = async () => {
    try {
      const data = await api.get<Challenge[]>("/challenges");
      setChallenges(data);
    } catch (e) {
      console.error("Error fetching challenges:", e);
      setError("Failed to load challenges");
    } finally {
      setLoading(false);
    }
  };

  return { challenges, loading, error, refetch: fetchChallenges };
}

export function useUserProgress(challengeId?: string) {
  const { user } = useAuth();
  const [progress, setProgress] = useState<UserProgress | null>(null);
  const [allProgress, setAllProgress] = useState<UserProgress[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) {
      setLoading(false);
      return;
    }

    if (challengeId) {
      fetchProgress();
    } else {
      fetchAllProgress();
    }
  }, [user, challengeId]);

  const fetchProgress = async () => {
    if (!user || !challengeId) return;

    try {
      const data = await api.get<UserProgress | null>(`/progress/${challengeId}`);
      if (data) setProgress(data);
    } catch (e) {
      console.error("Error fetching progress:", e);
    } finally {
      setLoading(false);
    }
  };

  const fetchAllProgress = async () => {
    if (!user) return;

    try {
      const data = await api.get<UserProgress[]>("/progress");
      setAllProgress(data);
    } catch (e) {
      console.error("Error fetching all progress:", e);
    } finally {
      setLoading(false);
    }
  };

  const startChallenge = async (challengeId: string) => {
    if (!user) return null;

    try {
      const data = await api.post<UserProgress>(`/progress/${challengeId}/start`);
      setProgress(data);
      return data;
    } catch (e) {
      console.error("Error starting challenge:", e);
      return null;
    }
  };

  const updateProgress = async (updates: Partial<UserProgress>, targetChallengeId?: string) => {
    if (!user) return;

    try {
      const challengeId = targetChallengeId || progress?.challenge_id;
      if (!challengeId) return;
      const updated = await api.patch<UserProgress>(`/progress/${challengeId}`, updates);
      setProgress(updated);
    } catch (e) {
      console.error("Error updating progress:", e);
    }
  };

  const resetChallenge = async (challengeId: string) => {
    if (!user) return null;

    try {
      const data = await api.post<UserProgress>(`/progress/${challengeId}/reset`);
      setProgress(data);
      return data;
    } catch (e) {
      console.error("Error resetting challenge:", e);
      return null;
    }
  };

  return { progress, allProgress, loading, startChallenge, updateProgress, resetChallenge, refetch: challengeId ? fetchProgress : fetchAllProgress };
}
