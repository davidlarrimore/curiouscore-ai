import { useState, useEffect } from "react";
import { supabase } from "@/integrations/supabase/client";
import { useAuth } from "./useAuth";

export interface Profile {
  id: string;
  username: string | null;
  avatar_url: string | null;
  xp: number;
  level: number;
  created_at: string;
}

export interface Badge {
  id: string;
  name: string;
  description: string;
  icon: string;
  badge_type: "milestone" | "category_mastery" | "streak" | "achievement";
  xp_reward: number;
}

export interface UserBadge {
  id: string;
  badge_id: string;
  earned_at: string;
  badge: Badge;
}

export function useProfile() {
  const { user } = useAuth();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [badges, setBadges] = useState<UserBadge[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) {
      setLoading(false);
      return;
    }

    fetchProfile();
    fetchBadges();
  }, [user]);

  const fetchProfile = async () => {
    if (!user) return;

    try {
      const { data, error } = await supabase
        .from("profiles")
        .select("*")
        .eq("id", user.id)
        .single();

      if (error) throw error;
      setProfile(data);
    } catch (e) {
      console.error("Error fetching profile:", e);
    } finally {
      setLoading(false);
    }
  };

  const fetchBadges = async () => {
    if (!user) return;

    try {
      const { data, error } = await supabase
        .from("user_badges")
        .select(`
          id,
          badge_id,
          earned_at,
          badges (
            id,
            name,
            description,
            icon,
            badge_type,
            xp_reward
          )
        `)
        .eq("user_id", user.id);

      if (error) throw error;

      const mapped = (data || []).map((ub) => ({
        id: ub.id,
        badge_id: ub.badge_id,
        earned_at: ub.earned_at,
        badge: ub.badges as unknown as Badge,
      }));

      setBadges(mapped);
    } catch (e) {
      console.error("Error fetching badges:", e);
    }
  };

  const updateProfile = async (updates: Partial<Profile>) => {
    if (!user) return;

    try {
      const { error } = await supabase
        .from("profiles")
        .update(updates)
        .eq("id", user.id);

      if (error) throw error;

      setProfile((prev) => (prev ? { ...prev, ...updates } : null));
    } catch (e) {
      console.error("Error updating profile:", e);
    }
  };

  const addXP = async (amount: number) => {
    if (!user || !profile) return;

    const newXP = profile.xp + amount;
    const newLevel = calculateLevel(newXP);

    await updateProfile({ xp: newXP, level: newLevel });
  };

  return { profile, badges, loading, updateProfile, addXP, refetch: fetchProfile };
}

function calculateLevel(xp: number): number {
  // Simple level calculation: level = 1 + floor(xp / 500)
  return Math.floor(xp / 500) + 1;
}

export function useAllBadges() {
  const [badges, setBadges] = useState<Badge[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBadges();
  }, []);

  const fetchBadges = async () => {
    try {
      const { data, error } = await supabase
        .from("badges")
        .select("*")
        .order("created_at", { ascending: true });

      if (error) throw error;

      const mapped = (data || []).map((b) => ({
        ...b,
        badge_type: b.badge_type as Badge["badge_type"],
      }));

      setBadges(mapped);
    } catch (e) {
      console.error("Error fetching all badges:", e);
    } finally {
      setLoading(false);
    }
  };

  return { badges, loading };
}
