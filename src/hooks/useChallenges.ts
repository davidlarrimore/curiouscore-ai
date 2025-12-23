import { useState, useEffect } from "react";
import { supabase } from "@/integrations/supabase/client";
import { useAuth } from "./useAuth";
import { Json } from "@/integrations/supabase/types";

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
      const { data, error } = await supabase
        .from("challenges")
        .select("*")
        .eq("is_active", true)
        .order("created_at", { ascending: true });

      if (error) throw error;

      const mapped = (data || []).map((c) => ({
        ...c,
        difficulty: c.difficulty as Challenge["difficulty"],
        help_resources: parseHelpResources(c.help_resources),
      }));

      setChallenges(mapped);
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
      const { data, error } = await supabase
        .from("user_progress")
        .select("*")
        .eq("user_id", user.id)
        .eq("challenge_id", challengeId)
        .maybeSingle();

      if (error) throw error;

      if (data) {
        setProgress({
          ...data,
          status: data.status as UserProgress["status"],
          messages: parseMessages(data.messages),
        });
      }
    } catch (e) {
      console.error("Error fetching progress:", e);
    } finally {
      setLoading(false);
    }
  };

  const fetchAllProgress = async () => {
    if (!user) return;

    try {
      const { data, error } = await supabase
        .from("user_progress")
        .select("*")
        .eq("user_id", user.id);

      if (error) throw error;

      const mapped = (data || []).map((p) => ({
        ...p,
        status: p.status as UserProgress["status"],
        messages: parseMessages(p.messages),
      }));

      setAllProgress(mapped);
    } catch (e) {
      console.error("Error fetching all progress:", e);
    } finally {
      setLoading(false);
    }
  };

  const startChallenge = async (challengeId: string) => {
    if (!user) return null;

    try {
      const { data, error } = await supabase
        .from("user_progress")
        .upsert({
          user_id: user.id,
          challenge_id: challengeId,
          status: "in_progress",
          started_at: new Date().toISOString(),
          messages: [],
        })
        .select()
        .single();

      if (error) throw error;

      const mapped: UserProgress = {
        ...data,
        status: data.status as UserProgress["status"],
        messages: [],
      };

      setProgress(mapped);
      return mapped;
    } catch (e) {
      console.error("Error starting challenge:", e);
      return null;
    }
  };

  const updateProgress = async (updates: Partial<UserProgress>) => {
    if (!user || !progress) return;

    try {
      const { error } = await supabase
        .from("user_progress")
        .update({
          ...updates,
          messages: updates.messages as unknown as Json,
          updated_at: new Date().toISOString(),
        })
        .eq("id", progress.id);

      if (error) throw error;

      setProgress((prev) => (prev ? { ...prev, ...updates } : null));
    } catch (e) {
      console.error("Error updating progress:", e);
    }
  };

  return { progress, allProgress, loading, startChallenge, updateProgress, refetch: challengeId ? fetchProgress : fetchAllProgress };
}

function parseHelpResources(resources: Json): HelpResource[] {
  if (!resources || !Array.isArray(resources)) return [];
  return resources as unknown as HelpResource[];
}

function parseMessages(messages: Json): ChatMessage[] {
  if (!messages || !Array.isArray(messages)) return [];
  return messages as unknown as ChatMessage[];
}
