/**
 * Challenge Page - Game Master Architecture
 *
 * Session-based challenge interface with UI mode switching.
 * Backend declares which input mode to show (MCQ, CHAT, CONTINUE_GATE, etc.).
 */

import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, Navigate, useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { useGameSession } from '@/hooks/useGameSession';
import { useChallenges } from '@/hooks/useChallenges';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { ThemeToggle } from '@/components/ThemeToggle';
import { ChatMessage } from '@/components/ChatMessage';
import { MCQSingleSelect } from '@/components/MCQSingleSelect';
import { MCQMultiSelect } from '@/components/MCQMultiSelect';
import { TrueFalseToggle } from '@/components/TrueFalseToggle';
import { useToast } from '@/hooks/use-toast';
import { Loader2, Send, ArrowLeft, Sparkles, Lightbulb, ArrowRight, LayoutDashboard, User, Shield, LogOut, Bot, Info, RefreshCw, BookOpen } from 'lucide-react';
import { api } from '@/lib/api';
import ReactMarkdown from 'react-markdown';

export default function ChallengeNew() {
  const { id: challengeId } = useParams<{ id: string }>();
  const { user, loading: authLoading, signOut, isAdmin } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  const { challenges } = useChallenges();

  const {
    session,
    uiResponse,
    isLoading,
    error,
    createAndStartSession,
    submitAnswer,
    submitAction,
    requestHint,
    isCreating,
    isStarting,
    isSubmitting,
  } = useGameSession(challengeId || '');

  const [textInput, setTextInput] = useState('');
  const [optimisticMessage, setOptimisticMessage] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [sidebarInsight, setSidebarInsight] = useState('');
  const [isSidebarInsightLoading, setIsSidebarInsightLoading] = useState(false);
  const [sidebarInsightError, setSidebarInsightError] = useState<string | null>(null);
  const [insightUpdatedAt, setInsightUpdatedAt] = useState<string | null>(null);
  const challenge = challenges.find((c) => c.id === challengeId);

  const progressPercentage = uiResponse?.total_steps
    ? ((uiResponse.step_index + 1) / uiResponse.total_steps) * 100
    : 0;

  const fetchSidebarInsight = useCallback(async () => {
    if (!uiResponse || !challengeId) return;

    setIsSidebarInsightLoading(true);
    setSidebarInsightError(null);

    const conversation = [
      ...uiResponse.messages.map((m) => `${m.role === 'assistant' ? 'Instructor' : 'Trainee'}: ${m.content}`),
      ...(optimisticMessage ? [`Trainee (pending): ${optimisticMessage}`] : []),
    ]
      .slice(-8)
      .join('\n');

    const resourceNotes = challenge?.help_resources
      ?.map((resource) => `${resource.title}: ${resource.description}`)
      .join('\n');

    try {
      const { content } = await api.post<{ content: string }>('/chat', {
        messages: [
          {
            role: 'user' as const,
            timestamp: new Date().toISOString(),
            content: [
              `Challenge: ${challenge?.title || 'Challenge'}`,
              `Description: ${challenge?.description || ''}`,
              `Step: ${uiResponse.step_title} (Step ${uiResponse.step_index + 1} of ${uiResponse.total_steps})`,
              `Instruction: ${uiResponse.step_instruction}`,
              `Status: ${uiResponse.status} | Session: ${session?.status || 'unknown'} | Score ${uiResponse.score}/${uiResponse.max_score} | Progress ${Math.round(progressPercentage)}%`,
              `Resource catalog:\n${resourceNotes || 'No resources provided.'}`,
              'Recent conversation:',
              conversation || 'No conversation yet. Provide starter guidance to help them begin.',
            ].join('\n\n'),
          },
        ],
        systemPrompt:
          'You are the right-sidebar coach for a trainee working on this challenge. Use the provided step instructions plus the recent conversation to teach the user how to answer the current question or task. Respond in markdown with three sections: Status Check (1 sentence), Recommended Actions (3 short bullets focused on what to do next), and Quick References (2 bullets citing provided resources or concrete tips). Be direct, concise, and stay under 120 words.',
        challengeTitle: challenge?.title || uiResponse.step_title,
        challengeId,
        currentPhase: uiResponse.step_index + 1,
      });

      setSidebarInsight(content);
      setInsightUpdatedAt(new Date().toISOString());
    } catch (err) {
      console.error('Sidebar insight error:', err);
      setSidebarInsightError(err instanceof Error ? err.message : 'Failed to load guidance');
    } finally {
      setIsSidebarInsightLoading(false);
    }
  }, [challenge?.description, challenge?.help_resources, challenge?.title, challengeId, optimisticMessage, progressPercentage, session?.status, uiResponse]);

  // Auto-create and start session on mount
  useEffect(() => {
    if (!session && !isLoading && !isCreating && challengeId) {
      createAndStartSession();
    }
  }, []);

  // Clear optimistic message when backend responds with new messages
  useEffect(() => {
    if (!isSubmitting && optimisticMessage) {
      setOptimisticMessage(null);
    }
  }, [isSubmitting, uiResponse?.messages.length]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [uiResponse?.messages, optimisticMessage, isSubmitting]);

  // Handle errors
  useEffect(() => {
    if (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Something went wrong',
        variant: 'destructive',
      });
    }
  }, [error]);

  useEffect(() => {
    if (!uiResponse) return;

    const timeoutId = setTimeout(() => {
      if (!isSubmitting) {
        fetchSidebarInsight();
      }
    }, 600);

    return () => clearTimeout(timeoutId);
  }, [fetchSidebarInsight, isSubmitting, uiResponse]);

  if (authLoading || isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!user) return <Navigate to="/auth" replace />;
  if (!challengeId) return <Navigate to="/" replace />;

  // Show loading during session creation
  if (isCreating || isStarting || !uiResponse) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-background">
        <div className="w-16 h-16 rounded-2xl gradient-primary flex items-center justify-center mb-4 animate-float">
          <Sparkles className="h-8 w-8 text-primary-foreground" />
        </div>
        <h2 className="text-xl font-bold mb-2">Preparing Challenge...</h2>
        <Loader2 className="h-6 w-6 animate-spin text-primary mt-2" />
      </div>
    );
  }

  // Render input based on UI mode
  const renderInput = () => {
    const { ui_mode, options } = uiResponse;

    if (session?.status === 'completed') {
      return (
        <Card className="p-6 text-center">
          <h3 className="text-lg font-semibold text-success mb-2">Challenge Complete! 🎉</h3>
          <p className="text-muted-foreground mb-4">
            Final Score: {uiResponse.score}/{uiResponse.max_score}
          </p>
          <Button onClick={() => navigate('/')} className="gradient-primary">
            Back to Dashboard
          </Button>
        </Card>
      );
    }

    switch (ui_mode) {
      case 'MCQ_SINGLE':
        return (
          <MCQSingleSelect
            options={options || []}
            onSubmit={submitAnswer}
            isSubmitting={isSubmitting}
          />
        );

      case 'MCQ_MULTI':
        return (
          <MCQMultiSelect
            options={options || []}
            onSubmit={submitAnswer}
            isSubmitting={isSubmitting}
          />
        );

      case 'TRUE_FALSE':
        return (
          <TrueFalseToggle
            onSubmit={submitAnswer}
            isSubmitting={isSubmitting}
          />
        );

      case 'CHAT':
        return (
          <Card className="p-6">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (textInput.trim() && !isSubmitting) {
                  // Show user's message optimistically
                  setOptimisticMessage(textInput);
                  submitAnswer(textInput);
                  setTextInput('');
                }
              }}
              className="space-y-3"
            >
              <div className="flex gap-2">
                <Input
                  value={textInput}
                  onChange={(e) => setTextInput(e.target.value)}
                  placeholder="Type your answer..."
                  disabled={isSubmitting}
                  className="flex-1"
                />
                <Button
                  type="submit"
                  disabled={!textInput.trim() || isSubmitting}
                  size="icon"
                  className="gradient-primary flex-shrink-0"
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
              <div className="flex justify-end">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    if (!isSubmitting) {
                      requestHint();
                    }
                  }}
                  disabled={isSubmitting}
                  className="text-muted-foreground hover:text-foreground"
                >
                  <Lightbulb className="h-4 w-4 mr-2" />
                  Request Hint
                </Button>
              </div>
            </form>
          </Card>
        );

      case 'CONTINUE_GATE':
        return (
          <Card className="p-6">
            <div className="flex flex-col items-center gap-4">
              <p className="text-sm text-muted-foreground text-center">
                {uiResponse.step_instruction || 'Ready to continue?'}
              </p>
              <div className="flex gap-3">
                <Button
                  onClick={() => submitAction('continue')}
                  disabled={isSubmitting}
                  className="gradient-primary"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Continuing...
                    </>
                  ) : (
                    <>
                      Continue
                      <ArrowRight className="h-4 w-4 ml-2" />
                    </>
                  )}
                </Button>
              </div>
            </div>
          </Card>
        );

      default:
        return (
          <Card className="p-6 text-center text-muted-foreground">
            Unknown UI mode: {ui_mode}
          </Card>
        );
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <header className="sticky top-0 z-40 border-b border-border/50 bg-card/70 backdrop-blur-xl flex-shrink-0">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={() => navigate('/')} className="flex-shrink-0 gap-2">
            <ArrowLeft className="h-4 w-4" />
            Back
          </Button>

          <div className="w-10 h-10 rounded-xl gradient-primary flex items-center justify-center shadow-md">
            <Sparkles className="h-5 w-5 text-primary-foreground" />
          </div>
          <div className="min-w-0">
            <p className="text-[11px] uppercase tracking-wide text-muted-foreground">Challenge</p>
            <h1 className="font-semibold text-base truncate">{challenge?.title || uiResponse.step_title}</h1>
            <p className="text-xs text-muted-foreground truncate">{challenge?.description || uiResponse.step_instruction}</p>
          </div>

          <div className="ml-auto flex items-center gap-2 flex-shrink-0">
            <Button variant="ghost" size="icon" onClick={() => navigate('/')} title="Dashboard">
              <LayoutDashboard className="h-4 w-4" />
            </Button>
            {isAdmin && (
              <Button variant="ghost" size="icon" onClick={() => navigate('/admin')} title="Admin">
                <Shield className="h-4 w-4" />
              </Button>
            )}
            <ThemeToggle />
            <Button variant="ghost" size="icon" onClick={signOut} title="Sign out">
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden min-h-0">
        <div className="flex-1 flex flex-col min-w-0 min-h-0">
          <div className="px-4 py-2 bg-card/30 border-b border-border/50">
            <div className="max-w-5xl mx-auto flex items-center gap-3">
              <Progress value={progressPercentage} className="h-2 flex-1" />
              <span className="text-xs text-muted-foreground font-mono">{Math.round(progressPercentage)}%</span>
            </div>
          </div>

          <ScrollArea className="flex-1">
            <div className="max-w-5xl mx-auto px-6 py-6 space-y-4">
              {!(uiResponse.ui_mode === 'CONTINUE_GATE' && uiResponse.messages.length > 0) && (
                <Card className="p-6 bg-accent/20 border-accent/40">
                  <h2 className="font-semibold mb-2">Step Instructions</h2>
                  <p className="text-sm text-muted-foreground">
                    {uiResponse.step_instruction}
                  </p>
                </Card>
              )}

              {uiResponse.messages.map((msg, i) => (
                <ChatMessage
                  key={msg.timestamp || i}
                  role={msg.role}
                  content={msg.content}
                  timestamp={msg.timestamp}
                />
              ))}

              {optimisticMessage && (
                <ChatMessage
                  role="user"
                  content={optimisticMessage}
                  timestamp={new Date().toISOString()}
                />
              )}

              {isSubmitting && (
                <div className="flex gap-3">
                  <div className="h-8 w-8 rounded-full bg-accent flex items-center justify-center flex-shrink-0">
                    <Loader2 className="h-4 w-4 animate-spin text-accent-foreground" />
                  </div>
                  <div className="bg-muted rounded-2xl rounded-tl-sm px-4 py-2.5 border border-border/50">
                    <div className="flex gap-1">
                      <span
                        className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce"
                        style={{ animationDelay: '0ms' }}
                      />
                      <span
                        className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce"
                        style={{ animationDelay: '150ms' }}
                      />
                      <span
                        className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce"
                        style={{ animationDelay: '300ms' }}
                      />
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>

          <div className="border-t border-border/50 bg-card/30 backdrop-blur-sm p-4 flex-shrink-0">
            <div className="max-w-4xl mx-auto">{renderInput()}</div>
          </div>
        </div>

        <aside className="w-80 border-l border-border/50 bg-card/40 backdrop-blur-sm hidden lg:flex flex-col flex-shrink-0 h-[calc(100vh-72px)] max-h-[calc(100vh-72px)] sticky top-[72px]">
          <div className="p-4 border-b border-border/50 space-y-3">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-[11px] uppercase tracking-wide text-muted-foreground">Status</p>
                <div className="flex items-center gap-2 mt-1">
                  <Badge
                    variant="outline"
                    className={`text-xs ${
                      uiResponse.status === 'completed'
                        ? 'bg-success/15 text-success border-success/30'
                        : uiResponse.status === 'in_progress'
                        ? 'bg-primary/10 text-primary border-primary/30'
                        : 'bg-muted text-muted-foreground border-border'
                    }`}
                  >
                    {uiResponse.status || 'Not Started'}
                  </Badge>
                  <Badge variant="secondary" className="text-xs bg-secondary/40">
                    Step {uiResponse.step_index + 1}/{uiResponse.total_steps}
                  </Badge>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-xs mb-1.5">
                  <span className="text-muted-foreground">Completion</span>
                  <span className="font-mono font-medium">{Math.round(progressPercentage)}%</span>
                </div>
                <Progress value={progressPercentage} className="h-1.5" />
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="rounded-lg border border-border/50 bg-background/50 p-2">
                  <p className="text-[11px] uppercase text-muted-foreground mb-0.5">Score</p>
                  <p className="font-semibold text-foreground">{uiResponse.score}/{uiResponse.max_score}</p>
                </div>
                <div className="rounded-lg border border-border/50 bg-background/50 p-2">
                  <p className="text-[11px] uppercase text-muted-foreground mb-0.5">Reward</p>
                  <p className="font-semibold text-foreground">{challenge?.xp_reward ? `${challenge.xp_reward} XP` : 'N/A'}</p>
                </div>
              </div>
            </div>
          </div>

          <ScrollArea className="flex-1">
            <div className="p-4 space-y-4">
              <div className="rounded-lg border border-border/50 bg-background/60 p-3 shadow-sm">
                <div className="flex items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2">
                    <div className="h-8 w-8 rounded-full bg-primary/15 text-primary flex items-center justify-center">
                      <Bot className="h-4 w-4" />
                    </div>
                    <div>
                      <p className="font-semibold text-sm leading-tight">AI Guidance</p>
                      <p className="text-[11px] text-muted-foreground">Reads your chat + instructions</p>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8"
                    onClick={fetchSidebarInsight}
                    disabled={isSidebarInsightLoading || isSubmitting}
                  >
                    {isSidebarInsightLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                  </Button>
                </div>
                <div className="text-[11px] text-muted-foreground mb-2">
                  {insightUpdatedAt ? `Updated ${new Date(insightUpdatedAt).toLocaleTimeString()}` : 'Waiting for context...'}
                </div>
                {sidebarInsightError ? (
                  <div className="text-xs text-destructive bg-destructive/10 border border-destructive/30 rounded-md p-2">
                    {sidebarInsightError}
                  </div>
                ) : (
                  <div className="prose prose-sm prose-invert max-w-none text-foreground text-xs leading-snug">
                    {isSidebarInsightLoading ? (
                      <p className="text-muted-foreground text-[11px] leading-snug">Analyzing your conversation...</p>
                    ) : sidebarInsight ? (
                      <ReactMarkdown
                        components={{
                          p: ({ children }) => <p className="text-xs leading-snug mb-2 last:mb-0">{children}</p>,
                          li: ({ children }) => <li className="text-xs leading-snug mb-1 last:mb-0">{children}</li>,
                          ul: ({ children }) => <ul className="list-disc ml-4 space-y-1">{children}</ul>,
                        }}
                      >
                        {sidebarInsight}
                      </ReactMarkdown>
                    ) : (
                      <p className="text-muted-foreground text-[11px] leading-snug">Send a message to get tailored guidance.</p>
                    )}
                  </div>
                )}
              </div>

              <div className="rounded-lg border border-border/50 bg-background/60 p-3 shadow-sm space-y-3">
                <div className="flex items-center gap-2">
                  <BookOpen className="h-4 w-4 text-accent" />
                  <div>
                    <p className="font-semibold text-sm leading-tight">Reference Library</p>
                    <p className="text-[11px] text-muted-foreground">Dive deeper with curated links</p>
                  </div>
                </div>
                <div className="space-y-2">
                  {(challenge?.help_resources || []).map((resource, i) => (
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
                        <ArrowRight className="h-3 w-3 text-muted-foreground flex-shrink-0 mt-0.5" />
                      </div>
                    </a>
                  ))}
                </div>

                <div className="rounded-md border border-border/50 bg-muted/30 p-2 flex items-start gap-2">
                  <Info className="h-4 w-4 text-muted-foreground mt-0.5" />
                  <p className="text-[11px] text-muted-foreground">
                    Use the chat to ask targeted questions. The sidebar refreshes with context-aware tips pulled from your latest conversation and instructions.
                  </p>
                </div>
              </div>
            </div>
          </ScrollArea>
        </aside>
      </div>
    </div>
  );
}
