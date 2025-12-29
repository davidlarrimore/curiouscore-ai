/**
 * Challenge Page - Game Master Architecture
 *
 * Session-based challenge interface with UI mode switching.
 * Backend declares which input mode to show (MCQ, CHAT, CONTINUE_GATE, etc.).
 */

import { useEffect, useState } from 'react';
import { useParams, Navigate, useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { useGameSession } from '@/hooks/useGameSession';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { ThemeToggle } from '@/components/ThemeToggle';
import { ChatMessage } from '@/components/ChatMessage';
import { MCQSingleSelect } from '@/components/MCQSingleSelect';
import { MCQMultiSelect } from '@/components/MCQMultiSelect';
import { TrueFalseToggle } from '@/components/TrueFalseToggle';
import { useToast } from '@/hooks/use-toast';
import { Loader2, Send, ArrowLeft, Sparkles } from 'lucide-react';

export default function ChallengeNew() {
  const { id: challengeId } = useParams<{ id: string }>();
  const { user, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();

  const {
    session,
    uiResponse,
    isLoading,
    error,
    createAndStartSession,
    submitAnswer,
    isCreating,
    isStarting,
    isSubmitting,
  } = useGameSession(challengeId || '');

  const [textInput, setTextInput] = useState('');
  const [optimisticMessage, setOptimisticMessage] = useState<string | null>(null);

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
              className="flex gap-2"
            >
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
            </form>
          </Card>
        );

      case 'CONTINUE_GATE':
        return (
          <Card className="p-6 text-center">
            <Button
              onClick={() => submitAnswer(true)}
              disabled={isSubmitting}
              className="gradient-primary"
            >
              {isSubmitting ? 'Continuing...' : 'Continue'}
            </Button>
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

  const progressPercentage =
    uiResponse.total_steps > 0
      ? ((uiResponse.step_index + 1) / uiResponse.total_steps) * 100
      : 0;

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="border-b border-border/50 bg-card/50 backdrop-blur-sm px-4 py-3 flex-shrink-0">
        <div className="max-w-5xl mx-auto flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => navigate('/')}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div className="flex-1">
            <h1 className="font-semibold text-lg">{uiResponse.step_title}</h1>
            <p className="text-sm text-muted-foreground">
              Step {uiResponse.step_index + 1} of {uiResponse.total_steps}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant="outline">
              Score: {uiResponse.score}/{uiResponse.max_score}
            </Badge>
            <ThemeToggle />
          </div>
        </div>
      </header>

      {/* Progress Bar */}
      <div className="px-4 py-2 bg-card/30 border-b border-border/50">
        <div className="max-w-5xl mx-auto">
          <Progress value={progressPercentage} className="h-2" />
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        <div className="max-w-5xl mx-auto h-full flex flex-col">
          {/* Messages */}
          <ScrollArea className="flex-1 px-6 py-6">
            <div className="space-y-4">
              {/* Step Instruction */}
              <Card className="p-6 bg-accent/30 border-accent/50">
                <h2 className="font-semibold mb-2">Instructions</h2>
                <p className="text-sm text-muted-foreground">
                  {uiResponse.step_instruction}
                </p>
              </Card>

              {/* Display Messages */}
              {uiResponse.messages.map((msg, i) => (
                <ChatMessage
                  key={msg.timestamp || i}
                  role={msg.role}
                  content={msg.content}
                  timestamp={msg.timestamp}
                />
              ))}

              {/* Optimistic User Message */}
              {optimisticMessage && (
                <ChatMessage
                  role="user"
                  content={optimisticMessage}
                  timestamp={new Date().toISOString()}
                />
              )}

              {/* Loading State */}
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
            </div>
          </ScrollArea>

          {/* Input Area */}
          <div className="border-t border-border/50 bg-card/30 backdrop-blur-sm p-4 flex-shrink-0">
            <div className="max-w-3xl mx-auto">{renderInput()}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
