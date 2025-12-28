import { useState, useRef, useEffect } from "react";
import { useParams, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import { useChallenges, useUserProgress, ChatMessage, MessageMetadata } from "@/hooks/useChallenges";
import { useProfile } from "@/hooks/useProfile";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ThemeToggle } from "@/components/ThemeToggle";
import { useToast } from "@/hooks/use-toast";
import { Loader2, Send, ArrowLeft, Sparkles, BookOpen, Lightbulb, ExternalLink, CheckCircle2, XCircle } from "lucide-react";
import { api } from "@/lib/api";

export default function Challenge() {
  const { id } = useParams<{ id: string }>();
  const { user, loading: authLoading } = useAuth();
  const { challenges, loading: challengesLoading } = useChallenges();
  const { progress, startChallenge, updateProgress } = useUserProgress(id);
  const { addXP } = useProfile();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentMetadata, setCurrentMetadata] = useState<MessageMetadata | null>(null);
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const challenge = challenges.find((c) => c.id === id);

  useEffect(() => {
    if (progress?.messages) {
      setMessages(progress.messages);
    }
  }, [progress]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (authLoading || challengesLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!user) return <Navigate to="/auth" replace />;
  if (!challenge) return <Navigate to="/" replace />;

  const handleStart = async () => {
    const newProgress = await startChallenge(challenge.id);
    if (newProgress) {
      sendMessage("", true, newProgress);
    }
  };

  const sendMessage = async (userMessage: string, isStart = false, startProgress?: UserProgress) => {
    if (isStreaming) return;

    const newMessages: ChatMessage[] = isStart
      ? []
      : [...messages, { role: "user" as const, content: userMessage, timestamp: new Date().toISOString() }];

    if (!isStart) {
      setMessages(newMessages);
      setInput("");
      setSelectedOption(null);
    }

    setIsStreaming(true);
    setCurrentMetadata(null);

    try {
      const response = await api.post<{ content: string; metadata?: MessageMetadata }>("/chat", {
        messages: newMessages.map((m) => ({ role: m.role, content: m.content, timestamp: m.timestamp, metadata: m.metadata })),
        systemPrompt: challenge.system_prompt,
        challengeTitle: challenge.title,
        challengeId: challenge.id,
        currentPhase: startProgress?.current_phase || progress?.current_phase || 1,
      });

      const assistantMessage = response.content;
      const metadata = response.metadata || null;

      if (metadata) {
        setCurrentMetadata(metadata);
      }

      const finalMessages: ChatMessage[] = [
        ...newMessages,
        { role: "assistant", content: assistantMessage, timestamp: new Date().toISOString(), metadata: metadata || undefined },
      ];

      setMessages(finalMessages);

      // Update progress
      const progressState = startProgress || progress;
      if (progressState) {
        const newProgressValue = Math.min(100, (progressState.progress_percent || 0) + (metadata?.progressIncrement || 0));
        const newScore = Math.max(0, (progressState.score || 0) + (metadata?.scoreChange || 0));

        await updateProgress(
          {
            messages: finalMessages,
            progress_percent: newProgressValue,
            score: newScore,
            current_phase: metadata?.phase || progressState.current_phase,
            status: metadata?.isComplete ? "completed" : "in_progress",
            completed_at: metadata?.isComplete ? new Date().toISOString() : null,
          },
          challenge.id
        );

        if (metadata?.isComplete) {
          const earnedXP = Math.floor(challenge.xp_reward * (newScore / 100));
          await addXP(earnedXP);
          toast({
            title: "Challenge Complete! 🎉",
            description: `You earned ${earnedXP} XP!`,
          });
        }
      }
    } catch (error) {
      console.error("Chat error:", error);
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to send message",
        variant: "destructive",
      });
    } finally {
      setIsStreaming(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;
    sendMessage(input);
  };

  const handleOptionSelect = (index: number) => {
    if (isStreaming) return;
    setSelectedOption(index);
    const optionText = currentMetadata?.options?.[index];
    if (optionText) {
      sendMessage(`My answer: ${optionText}`);
    }
  };

  const isStarted = progress?.status === "in_progress" || progress?.status === "completed";
  const showMCQ = currentMetadata?.questionType === "mcq" && currentMetadata?.options;

  return (
    <div className="min-h-screen bg-background flex">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="glass-dark border-b border-border/50 p-4">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => navigate("/")}>
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div className="flex-1">
              <h1 className="font-bold text-lg">{challenge.title}</h1>
              <p className="text-sm text-muted-foreground">{challenge.description}</p>
            </div>
            <ThemeToggle />
          </div>
        </header>

        {/* Messages */}
        <ScrollArea className="flex-1 p-4">
          <div className="max-w-3xl mx-auto space-y-4">
            {!isStarted ? (
              <div className="flex flex-col items-center justify-center py-20 text-center">
                <div className="w-20 h-20 rounded-2xl gradient-primary flex items-center justify-center mb-6 animate-float">
                  <Sparkles className="h-10 w-10 text-primary-foreground" />
                </div>
                <h2 className="text-2xl font-bold mb-2">Ready to Begin?</h2>
                <p className="text-muted-foreground mb-6 max-w-md">
                  Your AI instructor will guide you through this challenge interactively.
                </p>
                <Button onClick={handleStart} className="gradient-primary glow-primary">
                  Start Challenge
                </Button>
              </div>
            ) : (
              messages.map((msg, i) => (
                <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div
                    className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                      msg.role === "user"
                        ? "bg-primary text-primary-foreground"
                        : "glass-dark border border-border/50"
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                  </div>
                </div>
              ))
            )}

            {isStreaming && (
              <div className="flex justify-start">
                <div className="glass-dark border border-border/50 rounded-2xl px-4 py-3">
                  <Loader2 className="h-5 w-5 animate-spin text-primary" />
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>

        {/* Input Area */}
        {isStarted && progress?.status !== "completed" && (
          <div className="p-4 border-t border-border/50 glass-dark">
            <div className="max-w-3xl mx-auto">
              {showMCQ ? (
                <div className="grid grid-cols-2 gap-3">
                  {currentMetadata.options?.map((option, i) => (
                    <Button
                      key={i}
                      variant="outline"
                      className={`h-auto py-3 px-4 text-left justify-start ${
                        selectedOption === i ? "border-primary bg-primary/10" : ""
                      }`}
                      onClick={() => handleOptionSelect(i)}
                      disabled={isStreaming}
                    >
                      <span className="font-mono mr-2 text-primary">{String.fromCharCode(65 + i)}.</span>
                      {option}
                    </Button>
                  ))}
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="flex gap-2">
                  <Input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Type your answer..."
                    disabled={isStreaming}
                    className="flex-1"
                  />
                  <Button type="submit" disabled={!input.trim() || isStreaming} className="gradient-primary">
                    <Send className="h-4 w-4" />
                  </Button>
                </form>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Right Sidebar */}
      <aside className="w-80 border-l border-border/50 glass-dark hidden lg:flex flex-col">
        {/* Progress Section */}
        <div className="p-4 border-b border-border/50">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-primary" />
            Progress
          </h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span>Completion</span>
                <span className="font-mono">{progress?.progress_percent || 0}%</span>
              </div>
              <Progress value={progress?.progress_percent || 0} className="h-2" />
            </div>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-muted-foreground">Phase</p>
                <p className="font-semibold">{progress?.current_phase || 1} / 5</p>
              </div>
              <div>
                <p className="text-muted-foreground">Score</p>
                <p className="font-semibold">{progress?.score || 0}</p>
              </div>
            </div>
            {progress && (
              <Badge
                variant="outline"
                className={
                  progress.score >= 70
                    ? "bg-success/20 text-success border-success/30"
                    : progress.score >= 40
                    ? "bg-warning/20 text-warning border-warning/30"
                    : "bg-destructive/20 text-destructive border-destructive/30"
                }
              >
                {progress.score >= 70 ? "Great Progress!" : progress.score >= 40 ? "Keep Going!" : "Needs Improvement"}
              </Badge>
            )}
          </div>
        </div>

        {/* Help Resources */}
        <div className="flex-1 p-4 overflow-auto">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <BookOpen className="h-4 w-4 text-accent" />
            Resources
          </h3>
          <div className="space-y-3">
            {challenge.help_resources.map((resource, i) => (
              <a
                key={i}
                href={resource.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block p-3 rounded-lg bg-secondary/50 hover:bg-secondary transition-colors"
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="font-medium text-sm">{resource.title}</p>
                    <p className="text-xs text-muted-foreground">{resource.description}</p>
                  </div>
                  <ExternalLink className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                </div>
              </a>
            ))}
          </div>

          {currentMetadata?.hint && (
            <div className="mt-4 p-3 rounded-lg bg-warning/10 border border-warning/30">
              <div className="flex items-start gap-2">
                <Lightbulb className="h-4 w-4 text-warning flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-sm text-warning">Hint</p>
                  <p className="text-xs text-muted-foreground">{currentMetadata.hint}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </aside>
    </div>
  );
}
