import { useEffect, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import { Challenge } from "@/hooks/useChallenges";
import { useToast } from "@/hooks/use-toast";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { ThemeToggle } from "@/components/ThemeToggle";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Loader2, ArrowLeft, Shield, RefreshCw, Save } from "lucide-react";
import { api } from "@/lib/api";

type Provider = "openai" | "anthropic" | "gemini";

interface ModelOption {
  id: string;
  description?: string | null;
}

interface ChallengeModelSelection {
  provider?: Provider;
  model?: string;
}

interface ChallengeModelResponse {
  challenge_id: string;
  provider: Provider;
  model: string;
}

const providerLabels: Record<Provider, string> = {
  openai: "OpenAI",
  anthropic: "Anthropic",
  gemini: "Google Gemini",
};

const asMessage = (error: unknown) => {
  if (error instanceof Error) return error.message;
  if (typeof error === "string") return error;
  try {
    return JSON.stringify(error);
  } catch {
    return "Unknown error";
  }
};

export default function Admin() {
  const { user, loading, isAdmin } = useAuth();
  const [challenges, setChallenges] = useState<Challenge[]>([]);
  const [challengesLoading, setChallengesLoading] = useState(true);
  const { toast } = useToast();
  const navigate = useNavigate();

  const [challengeModels, setChallengeModels] = useState<Record<string, ChallengeModelSelection>>({});
  const [modelsByProvider, setModelsByProvider] = useState<Record<Provider, ModelOption[]>>({
    openai: [],
    anthropic: [],
    gemini: [],
  });
  const [loadingModels, setLoadingModels] = useState<Record<Provider, boolean>>({
    openai: false,
    anthropic: false,
    gemini: false,
  });
  const [challengePrompts, setChallengePrompts] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState<string | null>(null);

  useEffect(() => {
    if (!isAdmin) return;
    fetchChallenges();
    fetchChallengeModels();
  }, [isAdmin]);

  const fetchChallenges = async () => {
    setChallengesLoading(true);
    try {
      const data = await api.get<Challenge[]>("/admin/challenges");
      setChallenges(data);
      setChallengePrompts(
        data.reduce((acc, challenge) => {
          acc[challenge.id] = challenge.system_prompt || "";
          return acc;
        }, {} as Record<string, string>)
      );
    } catch (error) {
      console.error("Failed to load challenges", error);
      toast({
        title: "Error",
        description: `Could not load challenges: ${asMessage(error)}`,
        variant: "destructive",
      });
    } finally {
      setChallengesLoading(false);
    }
  };

  const fetchChallengeModels = async () => {
    try {
      const data = await api.get<ChallengeModelResponse[]>("/admin/challenges/models");
      const mapped: Record<string, ChallengeModelSelection> = {};
      data.forEach((item) => {
        mapped[item.challenge_id] = { provider: item.provider, model: item.model };
        void loadModels(item.provider);
      });
      setChallengeModels(mapped);
    } catch (error) {
      console.error("Failed to load challenge models", error);
      toast({
        title: "Error",
        description: `Could not load challenge model mappings: ${asMessage(error)}`,
        variant: "destructive",
      });
    }
  };

  const loadModels = async (provider: Provider) => {
    if (modelsByProvider[provider]?.length || loadingModels[provider]) return;
    setLoadingModels((prev) => ({ ...prev, [provider]: true }));
    try {
      const data = await api.get<ModelOption[]>(`/llm/models?provider=${provider}`);
      setModelsByProvider((prev) => ({ ...prev, [provider]: data }));
    } catch (error) {
      console.error(`Failed to load models for ${provider}`, error);
      toast({
        title: "Error",
        description: `Could not load models for ${providerLabels[provider]}: ${asMessage(error)}`,
        variant: "destructive",
      });
    } finally {
      setLoadingModels((prev) => ({ ...prev, [provider]: false }));
    }
  };

  const handleSelectionChange = (challengeId: string, updates: ChallengeModelSelection) => {
    setChallengeModels((prev) => ({
      ...prev,
      [challengeId]: { ...prev[challengeId], ...updates },
    }));
    if (updates.provider) {
      void loadModels(updates.provider);
    }
  };

  const handlePromptChange = (challengeId: string, value: string) => {
    setChallengePrompts((prev) => ({
      ...prev,
      [challengeId]: value,
    }));
  };

  const handleSave = async (challenge: Challenge) => {
    const selection = challengeModels[challenge.id];
    const prompt = challengePrompts[challenge.id] ?? challenge.system_prompt ?? "";

    setSaving(challenge.id);
    try {
      const updatedChallenge = await api.patch<Challenge>(`/admin/challenges/${challenge.id}/prompt`, {
        system_prompt: prompt,
      });
      setChallenges((prev) => prev.map((c) => (c.id === challenge.id ? updatedChallenge : c)));
      setChallengePrompts((prev) => ({ ...prev, [challenge.id]: updatedChallenge.system_prompt || "" }));

      if (selection?.provider && selection?.model) {
        try {
          await api.put<ChallengeModelResponse>(`/admin/challenges/${challenge.id}/model`, {
            provider: selection.provider,
            model: selection.model,
          });
          toast({
            title: "Saved",
            description: `${challenge.title} prompt updated and mapped to ${selection.model}.`,
          });
        } catch (modelError) {
          console.error("Failed to save model mapping", modelError);
          toast({
            title: "Partial error",
            description: `Prompt saved, but model mapping failed: ${asMessage(modelError)}`,
            variant: "destructive",
          });
        }
      } else {
        toast({
          title: "Prompt saved",
          description: `${challenge.title} system prompt was updated. Model mapping unchanged.`,
        });
      }
    } catch (error) {
      console.error("Failed to save mapping", error);
      toast({
        title: "Error",
        description: `Could not save changes: ${asMessage(error)}`,
        variant: "destructive",
      });
    } finally {
      setSaving(null);
    }
  };

  const toggleChallengeActive = async (challenge: Challenge) => {
    const nextValue = !challenge.is_active;
    setChallenges((prev) =>
      prev.map((c) => (c.id === challenge.id ? { ...c, is_active: nextValue } : c))
    );
    try {
      await api.patch<Challenge>(`/admin/challenges/${challenge.id}/activation`, { is_active: nextValue });
      toast({
        title: nextValue ? "Challenge activated" : "Challenge deactivated",
        description: `${challenge.title} is now ${nextValue ? "active" : "inactive"}.`,
      });
    } catch (error) {
      console.error("Failed to update activation", error);
      setChallenges((prev) =>
        prev.map((c) => (c.id === challenge.id ? { ...c, is_active: challenge.is_active } : c))
      );
      toast({
        title: "Error",
        description: `Could not update challenge activation: ${asMessage(error)}`,
        variant: "destructive",
      });
    }
  };

  if (loading || challengesLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!user) return <Navigate to="/auth" replace />;
  if (!isAdmin) return <Navigate to="/" replace />;

  return (
    <div className="min-h-screen bg-background">
      <div className="absolute inset-0 bg-grid-pattern opacity-5 pointer-events-none" />

      <header className="glass-dark border-b border-border/50 p-4">
        <div className="container mx-auto flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate("/")}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <Shield className="h-5 w-5 text-primary" />
          <h1 className="text-xl font-bold">Admin Panel</h1>
          <div className="ml-auto">
            <ThemeToggle />
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8 max-w-5xl space-y-6">
        <Card className="glass-dark border-border/50">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Challenge LLM Routing</CardTitle>
              <p className="text-sm text-muted-foreground mt-1">
                Map each challenge to a provider and model. Models load from your configured API keys.
              </p>
            </div>
            <Button variant="ghost" size="icon" onClick={() => {
              void fetchChallenges();
              void fetchChallengeModels();
            }}>
              <RefreshCw className="h-4 w-4" />
            </Button>
          </CardHeader>
          <CardContent className="space-y-4">
            {challenges.length === 0 ? (
              <p className="text-muted-foreground">No challenges available.</p>
            ) : (
              challenges.map((challenge) => {
                const selection = challengeModels[challenge.id] || {};
                const providerModels = selection.provider ? modelsByProvider[selection.provider] : [];

                return (
                  <div
                    key={challenge.id}
                    className="p-4 rounded-xl border border-border/50 glass-dark space-y-4"
                  >
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <h3 className="font-semibold">{challenge.title}</h3>
                        <p className="text-sm text-muted-foreground max-w-2xl">{challenge.description}</p>
                        <div className="flex items-center gap-2 mt-2">
                          <Switch
                            id={`active-${challenge.id}`}
                            checked={challenge.is_active}
                            onCheckedChange={() => toggleChallengeActive(challenge)}
                          />
                          <Label htmlFor={`active-${challenge.id}`} className="text-sm">
                            {challenge.is_active ? "Active" : "Inactive"}
                          </Label>
                        </div>
                      </div>
                      <Badge variant="secondary" className="self-start">
                        {challenge.difficulty}
                      </Badge>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor={`prompt-${challenge.id}`}>System prompt</Label>
                      <Textarea
                        id={`prompt-${challenge.id}`}
                        value={challengePrompts[challenge.id] ?? ""}
                        onChange={(event) => handlePromptChange(challenge.id, event.target.value)}
                        placeholder="Enter the system prompt the model should follow for this challenge"
                        className="min-h-[120px]"
                      />
                    </div>

                    <div className="grid gap-4 md:grid-cols-[1fr_1fr_auto] items-end">
                      <div className="space-y-2">
                        <Label>Provider</Label>
                        <Select
                          value={selection.provider}
                          onValueChange={(value: Provider) =>
                            handleSelectionChange(challenge.id, { provider: value, model: undefined })
                          }
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select a provider" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="openai">OpenAI</SelectItem>
                            <SelectItem value="anthropic">Anthropic</SelectItem>
                            <SelectItem value="gemini">Google Gemini</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      <div className="space-y-2">
                        <Label>Model</Label>
                        <Select
                          value={selection.model}
                          onValueChange={(value) => handleSelectionChange(challenge.id, { model: value })}
                          disabled={!selection.provider || loadingModels[selection.provider]}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder={selection.provider ? "Select a model" : "Choose a provider first"} />
                          </SelectTrigger>
                          <SelectContent>
                            {providerModels?.length ? (
                              providerModels.map((model) => (
                                <SelectItem key={model.id} value={model.id}>
                                  <div className="flex flex-col">
                                    <span>{model.id}</span>
                                    {model.description ? (
                                      <span className="text-xs text-muted-foreground">{model.description}</span>
                                    ) : null}
                                  </div>
                                </SelectItem>
                              ))
                            ) : (
                              <SelectItem value="__no_models" disabled>
                                {selection.provider ? "No models loaded yet." : "Choose a provider to load models."}
                              </SelectItem>
                            )}
                          </SelectContent>
                        </Select>
                      </div>

                      <Button
                        className="md:justify-self-end"
                        onClick={() => handleSave(challenge)}
                        disabled={saving === challenge.id}
                      >
                        {saving === challenge.id ? (
                          <>
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            Saving...
                          </>
                        ) : (
                          <>
                            <Save className="h-4 w-4 mr-2" />
                            Save
                          </>
                        )}
                      </Button>
                    </div>
                  </div>
                );
              })
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
