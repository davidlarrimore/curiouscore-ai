import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { api, getToken, setToken } from "@/lib/api";

export interface AuthUser {
  id: string;
  email: string;
  username?: string | null;
  avatar_url?: string | null;
  role: "admin" | "user";
  xp: number;
  level: number;
  created_at: string;
}

interface AuthContextType {
  user: AuthUser | null;
  token: string | null;
  loading: boolean;
  signUp: (email: string, password: string, username?: string) => Promise<{ error: Error | null }>;
  signIn: (email: string, password: string) => Promise<{ error: Error | null }>;
  signOut: () => Promise<void>;
  isAdmin: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setTokenState] = useState<string | null>(getToken());
  const [loading, setLoading] = useState(true);

  const isAdmin = user?.role === "admin";

  useEffect(() => {
    const savedToken = getToken();
    if (!savedToken) {
      setLoading(false);
      return;
    }
    fetchMe(savedToken);
  }, []);

  const fetchMe = async (authToken: string) => {
    try {
      const me = await api.get<AuthUser>("/auth/me");
      setUser(me);
      setTokenState(authToken);
    } catch (e) {
      console.error("Failed to fetch current user:", e);
      clearSession();
    } finally {
      setLoading(false);
    }
  };

  const saveSession = (newToken: string) => {
    setToken(newToken);
    setTokenState(newToken);
  };

  const clearSession = () => {
    setToken(null);
    setTokenState(null);
    setUser(null);
  };

  const signUp = async (email: string, password: string, username?: string) => {
    try {
      const res = await api.post<{ access_token: string }>("/auth/register", { email, password, username });
      saveSession(res.access_token);
      await fetchMe(res.access_token);
      return { error: null };
    } catch (error) {
      return { error: error as Error };
    }
  };

  const signIn = async (email: string, password: string) => {
    try {
      const res = await api.post<{ access_token: string }>("/auth/login", { email, password });
      saveSession(res.access_token);
      await fetchMe(res.access_token);
      return { error: null };
    } catch (error) {
      return { error: error as Error };
    }
  };

  const signOut = async () => {
    clearSession();
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, signUp, signIn, signOut, isAdmin }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
