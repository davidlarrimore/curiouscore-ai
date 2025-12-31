/**
 * ChallengeLoadingProgress Component
 *
 * Displays detailed loading progress for challenge initialization.
 * Uses timer-based progression to show activity during backend operations.
 */

import { useEffect, useState } from 'react';
import { Progress } from '@/components/ui/progress';
import { Card } from '@/components/ui/card';
import { Loader2, CheckCircle2, Circle, Sparkles, Database, Cpu, Bot, CheckCheck } from 'lucide-react';

interface LoadingStep {
  id: string;
  label: string;
  description: string;
  icon: typeof Database;
  estimatedDuration: number; // milliseconds
}

const LOADING_STEPS: LoadingStep[] = [
  {
    id: 'creating',
    label: 'Creating Session',
    description: 'Initializing your challenge session...',
    icon: Database,
    estimatedDuration: 300,
  },
  {
    id: 'loading-data',
    label: 'Loading Challenge',
    description: 'Fetching challenge data and steps...',
    icon: Database,
    estimatedDuration: 500,
  },
  {
    id: 'initializing',
    label: 'Preparing Game Engine',
    description: 'Setting up game state and rules...',
    icon: Cpu,
    estimatedDuration: 400,
  },
  {
    id: 'ai-narration',
    label: 'Generating AI Narration',
    description: 'AI instructor is preparing your introduction...',
    icon: Bot,
    estimatedDuration: 3000, // This is the slow part
  },
  {
    id: 'finalizing',
    label: 'Finalizing Setup',
    description: 'Almost ready to begin...',
    icon: CheckCheck,
    estimatedDuration: 200,
  },
];

interface ChallengeLoadingProgressProps {
  isCreating: boolean;
  isStarting: boolean;
  hasResponse: boolean;
}

export function ChallengeLoadingProgress({
  isCreating,
  isStarting,
  hasResponse,
}: ChallengeLoadingProgressProps) {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set());
  const [timersInitialized, setTimersInitialized] = useState(false);

  // Reset when creating
  useEffect(() => {
    if (isCreating) {
      setCurrentStepIndex(0);
      setCompletedSteps(new Set());
      setTimersInitialized(false);
    }
  }, [isCreating]);

  // Start timer-based progression when starting phase begins
  useEffect(() => {
    if (!isStarting || timersInitialized || isCreating) {
      return;
    }

    // Mark that we've initialized timers to prevent re-running
    setTimersInitialized(true);

    // Session created, start the progression through backend operations
    setCompletedSteps(new Set([0]));
    setCurrentStepIndex(1);

    const timers: NodeJS.Timeout[] = [];

    // Stage 1: Loading data (after 500ms)
    timers.push(setTimeout(() => {
      setCompletedSteps(prev => new Set([...prev, 1]));
      setCurrentStepIndex(2);
    }, LOADING_STEPS[1].estimatedDuration));

    // Stage 2: Initializing engine (after 500ms + 400ms = 900ms)
    timers.push(setTimeout(() => {
      setCompletedSteps(prev => new Set([...prev, 2]));
      setCurrentStepIndex(3);
    }, LOADING_STEPS[1].estimatedDuration + LOADING_STEPS[2].estimatedDuration));

    // Stage 3: AI Narration (after 900ms + 3000ms = 3900ms) - the long wait
    timers.push(setTimeout(() => {
      setCompletedSteps(prev => new Set([...prev, 3]));
      setCurrentStepIndex(4);
    }, LOADING_STEPS[1].estimatedDuration + LOADING_STEPS[2].estimatedDuration + LOADING_STEPS[3].estimatedDuration));

    return () => {
      timers.forEach(timer => clearTimeout(timer));
    };
  }, [isStarting, timersInitialized, isCreating]);

  // Mark everything complete when we have a response
  useEffect(() => {
    if (hasResponse) {
      setCompletedSteps(new Set([0, 1, 2, 3, 4]));
      setCurrentStepIndex(4);
    }
  }, [hasResponse]);

  const progressPercentage = ((currentStepIndex + 1) / LOADING_STEPS.length) * 100;
  const currentStep = LOADING_STEPS[currentStepIndex];

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-background p-4">
      {/* Animated Icon */}
      <div className="w-16 h-16 rounded-2xl gradient-primary flex items-center justify-center mb-6 animate-float">
        <Sparkles className="h-8 w-8 text-primary-foreground" />
      </div>

      {/* Main Title */}
      <h2 className="text-2xl font-bold mb-2">Preparing Challenge</h2>
      <p className="text-muted-foreground mb-8">Please wait while we set everything up</p>

      {/* Progress Card */}
      <Card className="w-full max-w-md p-6">
        {/* Progress Bar */}
        <div className="mb-6">
          <Progress value={progressPercentage} className="h-2" />
          <div className="flex justify-between mt-2 text-xs text-muted-foreground">
            <span>Step {currentStepIndex + 1} of {LOADING_STEPS.length}</span>
            <span>{Math.round(progressPercentage)}%</span>
          </div>
        </div>

        {/* Loading Steps */}
        <div className="space-y-3">
          {LOADING_STEPS.map((step, index) => {
            const isCompleted = completedSteps.has(index);
            const isCurrent = index === currentStepIndex;
            const isPending = index > currentStepIndex;
            const StepIcon = step.icon;

            return (
              <div
                key={step.id}
                className={`flex items-start gap-3 p-2 rounded-lg transition-all ${
                  isCurrent ? 'bg-primary/5 border border-primary/20' : ''
                } ${isPending ? 'opacity-40' : 'opacity-100'}`}
              >
                {/* Step Icon */}
                <div className="flex-shrink-0 mt-0.5">
                  {isCompleted ? (
                    <CheckCircle2 className="h-5 w-5 text-success" />
                  ) : isCurrent ? (
                    <div className="relative">
                      <StepIcon className="h-5 w-5 text-primary" />
                      <Loader2 className="h-3 w-3 text-primary animate-spin absolute -top-1 -right-1" />
                    </div>
                  ) : (
                    <StepIcon className="h-5 w-5 text-muted-foreground" />
                  )}
                </div>

                {/* Step Content */}
                <div className="flex-1 min-w-0">
                  <div
                    className={`font-medium text-sm ${
                      isCurrent ? 'text-foreground' : isCompleted ? 'text-success' : 'text-muted-foreground'
                    }`}
                  >
                    {step.label}
                  </div>
                  <div className="text-xs text-muted-foreground mt-0.5">
                    {step.description}
                  </div>
                  {/* Show duration estimate for AI narration step */}
                  {isCurrent && step.id === 'ai-narration' && (
                    <div className="text-xs text-primary mt-1 flex items-center gap-1">
                      <Bot className="h-3 w-3" />
                      <span>This may take a few seconds...</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </Card>

      {/* Helpful Tip */}
      <p className="text-xs text-muted-foreground mt-6 max-w-md text-center">
        The AI instructor is crafting a personalized learning experience for you.
      </p>
    </div>
  );
}
