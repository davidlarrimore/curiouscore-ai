/**
 * Progress Tracking Editor Component
 *
 * Allows admins to configure progress tracking for Simple challenges.
 * Supports 4 modes: Questions, Phases, Milestones, and Triggers.
 */

import { useState, useEffect } from "react";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Trash2, Plus, Info, CheckCircle2 } from "lucide-react";

type ProgressMode = "questions" | "phases" | "milestones" | "triggers";

interface Phase {
  number: number;
  name: string;
  description: string;
}

interface Milestone {
  id: string;
  name: string;
  points: number;
}

interface ProgressConfig {
  mode: ProgressMode;
  total_questions?: number;
  phases?: Phase[];
  milestones?: Milestone[];
  triggers?: string[];
}

interface ProgressTrackingEditorProps {
  config: ProgressConfig | null;
  onChange: (config: ProgressConfig | null) => void;
  xpReward: number;
}

export function ProgressTrackingEditor({ config, onChange, xpReward }: ProgressTrackingEditorProps) {
  const [enabled, setEnabled] = useState(!!config);
  const [mode, setMode] = useState<ProgressMode>(config?.mode || "questions");

  // Questions mode state
  const [totalQuestions, setTotalQuestions] = useState(config?.total_questions || 5);

  // Phases mode state
  const [phases, setPhases] = useState<Phase[]>(config?.phases || [
    { number: 1, name: "Introduction", description: "Learn basic concepts" },
    { number: 2, name: "Practice", description: "Apply concepts with examples" },
    { number: 3, name: "Assessment", description: "Demonstrate mastery" },
  ]);

  // Milestones mode state
  const [milestones, setMilestones] = useState<Milestone[]>(config?.milestones || [
    { id: "milestone_1", name: "First Milestone", points: 25 },
    { id: "milestone_2", name: "Second Milestone", points: 25 },
    { id: "milestone_3", name: "Third Milestone", points: 25 },
    { id: "milestone_4", name: "Fourth Milestone", points: 25 },
  ]);

  // Triggers mode state
  const [triggers, setTriggers] = useState<string[]>(config?.triggers || [
    "concept_1",
    "concept_2",
    "concept_3",
    "concept_4",
  ]);

  // Sync internal state when config prop changes (e.g., when loading a challenge)
  useEffect(() => {
    if (config) {
      setEnabled(true);
      setMode(config.mode);
      if (config.total_questions) setTotalQuestions(config.total_questions);
      if (config.phases) setPhases(config.phases);
      if (config.milestones) setMilestones(config.milestones);
      if (config.triggers) setTriggers(config.triggers);
    } else {
      setEnabled(false);
    }
  }, [config]);

  // Update parent when configuration changes
  useEffect(() => {
    if (!enabled) {
      onChange(null);
      return;
    }

    const newConfig: ProgressConfig = { mode };

    if (mode === "questions") {
      newConfig.total_questions = totalQuestions;
    } else if (mode === "phases") {
      newConfig.phases = phases;
    } else if (mode === "milestones") {
      newConfig.milestones = milestones;
    } else if (mode === "triggers") {
      newConfig.triggers = triggers;
    }

    onChange(newConfig);
  }, [enabled, mode, totalQuestions, phases, milestones, triggers, onChange]);

  // Phases handlers
  const addPhase = () => {
    const newPhaseNumber = phases.length + 1;
    setPhases([...phases, { number: newPhaseNumber, name: `Phase ${newPhaseNumber}`, description: "" }]);
  };

  const updatePhase = (index: number, field: keyof Phase, value: string | number) => {
    const updated = [...phases];
    updated[index] = { ...updated[index], [field]: value };
    setPhases(updated);
  };

  const removePhase = (index: number) => {
    const updated = phases.filter((_, i) => i !== index);
    // Renumber phases
    updated.forEach((phase, i) => {
      phase.number = i + 1;
    });
    setPhases(updated);
  };

  // Milestones handlers
  const addMilestone = () => {
    const newId = `milestone_${milestones.length + 1}`;
    const suggestedPoints = Math.floor(xpReward / (milestones.length + 1));
    setMilestones([...milestones, { id: newId, name: "New Milestone", points: suggestedPoints }]);
  };

  const updateMilestone = (index: number, field: keyof Milestone, value: string | number) => {
    const updated = [...milestones];
    updated[index] = { ...updated[index], [field]: value };
    setMilestones(updated);
  };

  const removeMilestone = (index: number) => {
    setMilestones(milestones.filter((_, i) => i !== index));
  };

  // Triggers handlers
  const addTrigger = () => {
    setTriggers([...triggers, `trigger_${triggers.length + 1}`]);
  };

  const updateTrigger = (index: number, value: string) => {
    const updated = [...triggers];
    updated[index] = value;
    setTriggers(updated);
  };

  const removeTrigger = (index: number) => {
    setTriggers(triggers.filter((_, i) => i !== index));
  };

  // Calculate total points for milestones
  const totalMilestonePoints = milestones.reduce((sum, m) => sum + m.points, 0);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-base">Progress Tracking</CardTitle>
            <CardDescription className="text-xs">
              Configure how learner progress is measured (Simple challenges only)
            </CardDescription>
          </div>
          <Tabs value={enabled ? "enabled" : "disabled"} onValueChange={(v) => setEnabled(v === "enabled")}>
            <TabsList className="grid w-32 grid-cols-2">
              <TabsTrigger value="disabled" className="text-xs">Off</TabsTrigger>
              <TabsTrigger value="enabled" className="text-xs">On</TabsTrigger>
            </TabsList>
          </Tabs>
        </div>
      </CardHeader>

      {enabled && (
        <CardContent className="space-y-4">
          {/* Mode Selection */}
          <div className="space-y-2">
            <Label>Progress Mode</Label>
            <Select value={mode} onValueChange={(v) => setMode(v as ProgressMode)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="questions">
                  <div className="flex items-center gap-2">
                    <span>Questions</span>
                    <Badge variant="outline" className="text-xs">Sequential Q&A</Badge>
                  </div>
                </SelectItem>
                <SelectItem value="phases">
                  <div className="flex items-center gap-2">
                    <span>Phases</span>
                    <Badge variant="outline" className="text-xs">Multi-stage</Badge>
                  </div>
                </SelectItem>
                <SelectItem value="milestones">
                  <div className="flex items-center gap-2">
                    <span>Milestones</span>
                    <Badge variant="outline" className="text-xs">Achievement-based</Badge>
                  </div>
                </SelectItem>
                <SelectItem value="triggers">
                  <div className="flex items-center gap-2">
                    <span>Triggers</span>
                    <Badge variant="outline" className="text-xs">Conversation-driven</Badge>
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Mode-specific configuration */}
          {mode === "questions" && (
            <div className="space-y-3">
              <Alert>
                <Info className="h-4 w-4" />
                <AlertDescription className="text-xs">
                  Learners progress by answering a fixed number of questions sequentially.
                  Progress = questions_answered / total_questions × 100%
                </AlertDescription>
              </Alert>

              <div className="space-y-2">
                <Label htmlFor="total-questions">Total Questions</Label>
                <Input
                  id="total-questions"
                  type="number"
                  min="1"
                  max="20"
                  value={totalQuestions}
                  onChange={(e) => setTotalQuestions(parseInt(e.target.value) || 5)}
                />
                <p className="text-xs text-muted-foreground">
                  Points per question: ~{Math.floor(xpReward / totalQuestions)} XP
                </p>
              </div>

              <div className="p-3 bg-muted rounded-lg text-xs space-y-1">
                <p className="font-medium">Preview:</p>
                <p>Question 1 of {totalQuestions} = {Math.round((1/totalQuestions)*100)}% progress</p>
                <p>Question {totalQuestions} of {totalQuestions} = 100% progress (complete)</p>
              </div>
            </div>
          )}

          {mode === "phases" && (
            <div className="space-y-3">
              <Alert>
                <Info className="h-4 w-4" />
                <AlertDescription className="text-xs">
                  Learners progress through named phases with multiple interactions per phase.
                  Progress = current_phase / total_phases × 100%
                </AlertDescription>
              </Alert>

              <div className="space-y-2">
                {phases.map((phase, index) => (
                  <Card key={index} className="p-3">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label className="text-xs">Phase {phase.number}</Label>
                        {phases.length > 1 && (
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => removePhase(index)}
                          >
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        )}
                      </div>
                      <Input
                        placeholder="Phase name"
                        value={phase.name}
                        onChange={(e) => updatePhase(index, "name", e.target.value)}
                      />
                      <Input
                        placeholder="Description"
                        value={phase.description}
                        onChange={(e) => updatePhase(index, "description", e.target.value)}
                      />
                    </div>
                  </Card>
                ))}
              </div>

              <Button type="button" variant="outline" size="sm" onClick={addPhase} className="w-full">
                <Plus className="h-3 w-3 mr-2" />
                Add Phase
              </Button>

              <div className="p-3 bg-muted rounded-lg text-xs space-y-1">
                <p className="font-medium">Preview:</p>
                <p>Phase 1 ({phases[0]?.name}) = {Math.round((1/phases.length)*100)}% progress</p>
                <p>Phase {phases.length} ({phases[phases.length - 1]?.name}) = 100% progress (complete)</p>
              </div>
            </div>
          )}

          {mode === "milestones" && (
            <div className="space-y-3">
              <Alert>
                <Info className="h-4 w-4" />
                <AlertDescription className="text-xs">
                  Learners achieve milestones in any order (non-linear progression).
                  Progress = achieved_milestones / total_milestones × 100%
                </AlertDescription>
              </Alert>

              {totalMilestonePoints !== xpReward && (
                <Alert variant="destructive">
                  <Info className="h-4 w-4" />
                  <AlertDescription className="text-xs">
                    Milestone points ({totalMilestonePoints}) should equal XP reward ({xpReward})
                  </AlertDescription>
                </Alert>
              )}

              <div className="space-y-2">
                {milestones.map((milestone, index) => (
                  <Card key={index} className="p-3">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label className="text-xs">Milestone {index + 1}</Label>
                        {milestones.length > 1 && (
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => removeMilestone(index)}
                          >
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        )}
                      </div>
                      <Input
                        placeholder="Milestone ID (e.g., understand_variables)"
                        value={milestone.id}
                        onChange={(e) => updateMilestone(index, "id", e.target.value)}
                      />
                      <Input
                        placeholder="Milestone name"
                        value={milestone.name}
                        onChange={(e) => updateMilestone(index, "name", e.target.value)}
                      />
                      <Input
                        type="number"
                        placeholder="Points"
                        value={milestone.points}
                        onChange={(e) => updateMilestone(index, "points", parseInt(e.target.value) || 0)}
                      />
                    </div>
                  </Card>
                ))}
              </div>

              <Button type="button" variant="outline" size="sm" onClick={addMilestone} className="w-full">
                <Plus className="h-3 w-3 mr-2" />
                Add Milestone
              </Button>

              <div className="p-3 bg-muted rounded-lg text-xs space-y-1">
                <p className="font-medium">Total Points: {totalMilestonePoints} / {xpReward} XP</p>
                {totalMilestonePoints === xpReward && (
                  <p className="text-green-600 flex items-center gap-1">
                    <CheckCircle2 className="h-3 w-3" />
                    Points balanced correctly
                  </p>
                )}
              </div>
            </div>
          )}

          {mode === "triggers" && (
            <div className="space-y-3">
              <Alert>
                <Info className="h-4 w-4" />
                <AlertDescription className="text-xs">
                  Triggers activate during natural conversation when learners demonstrate understanding.
                  Progress = activated_triggers / total_triggers × 100%
                </AlertDescription>
              </Alert>

              <div className="space-y-2">
                {triggers.map((trigger, index) => (
                  <Card key={index} className="p-3">
                    <div className="flex items-center gap-2">
                      <Input
                        placeholder="Trigger ID (e.g., explain_transformers)"
                        value={trigger}
                        onChange={(e) => updateTrigger(index, e.target.value)}
                        className="flex-1"
                      />
                      {triggers.length > 1 && (
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => removeTrigger(index)}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      )}
                    </div>
                  </Card>
                ))}
              </div>

              <Button type="button" variant="outline" size="sm" onClick={addTrigger} className="w-full">
                <Plus className="h-3 w-3 mr-2" />
                Add Trigger
              </Button>

              <div className="p-3 bg-muted rounded-lg text-xs space-y-1">
                <p className="font-medium">Preview:</p>
                <p>Points per trigger: ~{Math.floor(xpReward / triggers.length)} XP</p>
                <p>Triggers can activate in any order based on conversation</p>
              </div>
            </div>
          )}
        </CardContent>
      )}
    </Card>
  );
}
