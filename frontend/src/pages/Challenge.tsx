import { useState, useRef, useEffect } from "react";
import { useParams, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import { useChallenges, useUserProgress, ChatMessage as ChatMessageType, MessageMetadata, UserProgress } from "@/hooks/useChallenges";
import { useProfile } from "@/hooks/useProfile";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ThemeToggle } from "@/components/ThemeToggle";
import { ChatMessage } from "@/components/ChatMessage";
import { useToast } from "@/hooks/use-toast";
import { Loader2, Send, ArrowLeft, Sparkles, BookOpen, Lightbulb, ExternalLink, CheckCircle2, XCircle, RotateCcw, ArrowDown } from "lucide-react";
import { api } from "@/lib/api";

export default function Challenge() {
  const { id } = useParams<{ id: string }>();
  const { user, loading: authLoading } = useAuth();
  const { challenges, loading: challengesLoading } = useChallenges();
  const { progress, startChallenge, updateProgress, resetChallenge } = useUserProgress(id);
  const { addXP } = useProfile();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [currentMetadata, setCurrentMetadata] = useState<MessageMetadata | null>(null);
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Track scroll position and unread messages
  const [isNearBottom, setIsNearBottom] = useState(true);
  const [unreadCount, setUnreadCount] = useState(0);

  const challenge = challenges.find((c) => c.id === id);

  // Check if user is near bottom of scroll
  const checkScrollPosition = () => {
    const viewport = document.querySelector('[data-radix-scroll-area-viewport]') as HTMLDivElement;
    if (!viewport) return;

    const { scrollTop, scrollHeight, clientHeight } = viewport;
    const distanceFromBottom = scrollHeight - scrollTop - clientHeight;
    const nearBottom = distanceFromBottom < 100; // 100px threshold

    setIsNearBottom(nearBottom);
    if (nearBottom) setUnreadCount(0);
  };

  useEffect(() => {
    if (progress?.messages) {
      setMessages(progress.messages);
    }
  }, [progress]);

  // Smart auto-scroll - only when user is near bottom
  useEffect(() => {
    const viewport = document.querySelector('[data-radix-scroll-area-viewport]') as HTMLDivElement;
    if (!viewport) return;

    if (isNearBottom) {
      viewport.scrollTo({
        top: viewport.scrollHeight,
        behavior: "smooth"
      });
    } else {
      // User scrolled up - track unread messages
      const lastMessage = messages[messages.length - 1];
      if (lastMessage?.role === "assistant") {
        setUnreadCount(prev => prev + 1);
      }
    }
  }, [messages, isNearBottom]);

  // Monitor scroll position
  useEffect(() => {
    const viewport = document.querySelector('[data-radix-scroll-area-viewport]') as HTMLDivElement;
    if (!viewport) return;

    let timeoutId: NodeJS.Timeout;
    const throttledScroll = () => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(checkScrollPosition, 100);
    };

    viewport.addEventListener("scroll", throttledScroll);
    checkScrollPosition(); // Initial check

    return () => {
      viewport.removeEventListener("scroll", throttledScroll);
      clearTimeout(timeoutId);
    };
  }, []);

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
      sendMessage("Start Challenge", true, newProgress);
    }
  };

  const handleReset = async () => {
    if (!resetChallenge) return;

    const resetProgress = await resetChallenge(challenge.id);
    if (resetProgress) {
      setMessages([]);
      setCurrentMetadata(null);
      setSelectedOption(null);
      setInput("");
      setIsStreaming(false);
      toast({
        title: "Challenge Reset",
        description: "Your progress has been reset. Starting fresh!",
      });
    }
  };

  const sendMessage = async (userMessage: string, isStart = false, startProgress?: UserProgress) => {
    if (isStreaming) return;

    const timestamp = new Date().toISOString();
    const newMessages: ChatMessageType[] = isStart
      ? userMessage
        ? [{ role: "user" as const, content: userMessage, timestamp }]
        : []
      : [...messages, { role: "user" as const, content: userMessage, timestamp }];

    if (!isStart || userMessage) {
      setMessages(newMessages);
    }

    setInput("");
    setSelectedOption(null);

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

      const finalMessages: ChatMessageType[] = [
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
    <div className="min-h-screen bg-background flex flex-col">
      {/* Compact Header */}
      <header className="border-b border-border/50 bg-card/50 backdrop-blur-sm px-4 py-2 flex-shrink-0">
        <div className="flex items-center gap-3 max-w-full">
          <Button variant="ghost" size="sm" onClick={() => navigate("/")} className="flex-shrink-0">
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div className="flex-1 min-w-0">
            <h1 className="font-semibold text-base truncate">{challenge.title}</h1>
            <p className="text-xs text-muted-foreground truncate">{challenge.description}</p>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            <Badge variant="outline" className="text-xs">
              Phase {progress?.current_phase || 1}/5
            </Badge>
            <div className="text-xs text-muted-foreground">
              Score: <span className="font-semibold text-foreground">{progress?.score || 0}</span>
            </div>
            <ThemeToggle />
          </div>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        {/* Main Chat Area */}
        <div className={`flex-1 flex flex-col min-w-0 transition-colors ${!isStarted ? "bg-muted/40" : ""}`}>
          {/* Messages */}
          <ScrollArea className="flex-1">
            <div className="px-6 py-4 space-y-4 max-w-5xl mx-auto w-full">
              {!isStarted ? (
                <div className="flex flex-col items-center justify-center py-16 text-center">
                  <div className="w-16 h-16 rounded-2xl gradient-primary flex items-center justify-center mb-4 animate-float">
                    <Sparkles className="h-8 w-8 text-primary-foreground" />
                  </div>
                  <h2 className="text-xl font-bold mb-2">Ready to Begin?</h2>
                  <p className="text-muted-foreground mb-4 max-w-md text-sm">
                    Your AI instructor will guide you through this challenge interactively.
                  </p>
                  <Button onClick={handleStart} className="gradient-primary glow-primary">
                    Start Challenge
                  </Button>
                </div>
              ) : (
                messages.map((msg, i) => (
                  <ChatMessage key={msg.timestamp || i} role={msg.role} content={msg.content} timestamp={msg.timestamp} />
                ))
              )}

              {isStreaming && (
                <div className="flex gap-3">
                  <div className="h-8 w-8 rounded-full bg-accent flex items-center justify-center flex-shrink-0">
                    <Loader2 className="h-4 w-4 animate-spin text-accent-foreground" />
                  </div>
                  <div className="bg-muted rounded-2xl rounded-tl-sm px-4 py-2.5 border border-border/50">
                    <div className="flex gap-1">
                      <span className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                      <span className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                      <span className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Scroll to bottom button */}
            {!isNearBottom && (
              <div className="fixed bottom-24 right-8 z-10 lg:right-80">
                <Button
                  onClick={() => {
                    const viewport = document.querySelector('[data-radix-scroll-area-viewport]') as HTMLDivElement;
                    if (viewport) {
                      viewport.scrollTo({ top: viewport.scrollHeight, behavior: "smooth" });
                    }
                  }}
                  size="sm"
                  className="gradient-primary glow-primary shadow-lg rounded-full h-10 px-4 gap-2"
                >
                  <ArrowDown className="h-4 w-4" />
                  {unreadCount > 0 && (
                    <Badge variant="secondary" className="bg-background text-foreground px-1.5 py-0.5 text-xs">
                      {unreadCount}
                    </Badge>
                  )}
                  <span className="text-sm">New messages</span>
                </Button>
              </div>
            )}
          </ScrollArea>

          {/* Compact Input Area */}
          {isStarted && progress?.status !== "completed" && (
            <div className="border-t border-border/50 bg-card/30 backdrop-blur-sm p-3 flex-shrink-0">
              <div className="max-w-5xl mx-auto w-full">
                {showMCQ ? (
                  <div className="grid grid-cols-2 gap-2">
                    {currentMetadata.options?.map((option, i) => (
                      <Button
                        key={i}
                        variant="outline"
                        className={`h-auto py-2 px-3 text-left justify-start text-sm ${
                          selectedOption === i ? "border-primary bg-primary/10" : ""
                        }`}
                        onClick={() => handleOptionSelect(i)}
                        disabled={isStreaming}
                      >
                        <span className="font-mono mr-2 text-primary text-xs">{String.fromCharCode(65 + i)}.</span>
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
                    <Button type="submit" disabled={!input.trim() || isStreaming} size="icon" className="gradient-primary flex-shrink-0">
                      <Send className="h-4 w-4" />
                    </Button>
                  </form>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Compact Right Sidebar */}
        <aside className="w-72 border-l border-border/50 bg-card/30 backdrop-blur-sm hidden lg:flex flex-col flex-shrink-0">
          {/* Progress Section */}
          <div className="p-3 border-b border-border/50">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-sm flex items-center gap-2">
                <CheckCircle2 className="h-3.5 w-3.5 text-primary" />
                Progress
              </h3>
              {isStarted && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleReset}
                  disabled={isStreaming}
                  className="h-7 px-2 text-xs gap-1"
                >
                  <RotateCcw className="h-3 w-3" />
                  Reset
                </Button>
              )}
            </div>
            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-xs mb-1.5">
                  <span className="text-muted-foreground">Completion</span>
                  <span className="font-mono font-medium">{progress?.progress_percent || 0}%</span>
                </div>
                <Progress value={progress?.progress_percent || 0} className="h-1.5" />
              </div>
              {progress && (
                <Badge
                  variant="outline"
                  className={`w-full justify-center text-xs ${
                    progress.score >= 70
                      ? "bg-success/20 text-success border-success/30"
                      : progress.score >= 40
                      ? "bg-warning/20 text-warning border-warning/30"
                      : "bg-destructive/20 text-destructive border-destructive/30"
                  }`}
                >
                  {progress.score >= 70 ? "Great Progress!" : progress.score >= 40 ? "Keep Going!" : "Needs Improvement"}
                </Badge>
              )}
            </div>
          </div>

          {/* Help Resources */}
          <ScrollArea className="flex-1">
            <div className="p-3">
              <h3 className="font-semibold text-sm mb-3 flex items-center gap-2">
                <BookOpen className="h-3.5 w-3.5 text-accent" />
                Resources
              </h3>
              <div className="space-y-2">
                {challenge.help_resources.map((resource, i) => (
                  <a
                    key={i}
                    href={resource.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block p-2 rounded-lg bg-secondary/30 hover:bg-secondary/50 transition-colors border border-border/30"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <p className="font-medium text-xs truncate">{resource.title}</p>
                        <p className="text-xs text-muted-foreground line-clamp-2">{resource.description}</p>
                      </div>
                      <ExternalLink className="h-3 w-3 text-muted-foreground flex-shrink-0 mt-0.5" />
                    </div>
                  </a>
                ))}
              </div>

              {currentMetadata?.hint && (
                <div className="mt-3 p-2 rounded-lg bg-warning/10 border border-warning/30">
                  <div className="flex items-start gap-2">
                    <Lightbulb className="h-3.5 w-3.5 text-warning flex-shrink-0 mt-0.5" />
                    <div className="min-w-0">
                      <p className="font-medium text-xs text-warning">Hint</p>
                      <p className="text-xs text-muted-foreground">{currentMetadata.hint}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>
        </aside>
      </div>
    </div>
  );
}
