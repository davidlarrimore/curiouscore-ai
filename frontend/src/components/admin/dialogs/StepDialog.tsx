import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Checkbox } from "@/components/ui/checkbox";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { Loader2, Plus, X } from "lucide-react";
import { useAdminSteps, useCreateStep, useUpdateStep, type StepCreatePayload } from "@/hooks/useAdminSteps";

interface StepDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  challengeId: string;
  stepId: string | null;
}

export function StepDialog({ open, onOpenChange, challengeId, stepId }: StepDialogProps) {
  const { toast } = useToast();
  const isEditing = !!stepId;

  const { data: steps } = useAdminSteps(challengeId);
  const createMutation = useCreateStep();
  const updateMutation = useUpdateStep();

  const [options, setOptions] = useState<string[]>([]);
  const [rubricJson, setRubricJson] = useState("");
  const [correctAnswer, setCorrectAnswer] = useState<number | null>(null);
  const [correctAnswers, setCorrectAnswers] = useState<number[]>([]);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    setValue,
    watch,
  } = useForm<StepCreatePayload>({
    defaultValues: {
      challenge_id: challengeId,
      step_index: 0,
      step_type: "CHAT",
      title: "",
      instruction: "",
      points_possible: 10,
      passing_threshold: 70,
      auto_narrate: true,
    },
  });

  const stepType = watch("step_type");
  const autoNarrate = watch("auto_narrate");

  // Load step data when editing
  useEffect(() => {
    if (stepId && steps) {
      const step = steps.find((s) => s.id === stepId);
      if (step) {
        reset({
          challenge_id: challengeId,
          step_index: step.step_index,
          step_type: step.step_type,
          title: step.title,
          instruction: step.instruction,
          options: step.options,
          correct_answer: step.correct_answer,
          correct_answers: step.correct_answers,
          points_possible: step.points_possible,
          passing_threshold: step.passing_threshold,
          rubric: step.rubric,
          gm_context: step.gm_context,
          auto_narrate: step.auto_narrate,
        });
        setOptions(step.options || []);
        setRubricJson(step.rubric ? JSON.stringify(step.rubric, null, 2) : "");
        setCorrectAnswer(step.correct_answer ?? null);
        setCorrectAnswers(step.correct_answers || []);
      }
    } else if (!isEditing) {
      const nextIndex = steps ? steps.length : 0;
      reset({
        challenge_id: challengeId,
        step_index: nextIndex,
        step_type: "CHAT",
        title: "",
        instruction: "",
        points_possible: 10,
        passing_threshold: 70,
        auto_narrate: true,
      });
      setOptions([]);
      setRubricJson("");
      setCorrectAnswer(null);
      setCorrectAnswers([]);
    }
  }, [stepId, steps, isEditing, challengeId, reset]);

  const onSubmit = async (data: StepCreatePayload) => {
    try {
      // Parse rubric JSON if provided
      let rubric = undefined;
      if (rubricJson.trim()) {
        try {
          rubric = JSON.parse(rubricJson);
        } catch (e) {
          toast({
            title: "Invalid rubric",
            description: "Rubric must be valid JSON",
            variant: "destructive",
          });
          return;
        }
      }

      const payload = {
        ...data,
        options: options.length > 0 ? options : undefined,
        correct_answer: correctAnswer !== null ? correctAnswer : undefined,
        correct_answers: correctAnswers.length > 0 ? correctAnswers : undefined,
        rubric,
      };

      if (isEditing && stepId) {
        await updateMutation.mutateAsync({ challengeId, stepId, data: payload });
        toast({
          title: "Step updated",
          description: "The step has been successfully updated.",
        });
      } else {
        await createMutation.mutateAsync({ challengeId, data: payload });
        toast({
          title: "Step created",
          description: "The step has been successfully created.",
        });
      }
      onOpenChange(false);
    } catch (error) {
      toast({
        title: "Error",
        description: `Failed to ${isEditing ? "update" : "create"} step: ${
          error instanceof Error ? error.message : "Unknown error"
        }`,
        variant: "destructive",
      });
    }
  };

  const addOption = () => {
    setOptions([...options, ""]);
  };

  const updateOption = (index: number, value: string) => {
    const newOptions = [...options];
    newOptions[index] = value;
    setOptions(newOptions);
  };

  const removeOption = (index: number) => {
    const newOptions = options.filter((_, i) => i !== index);
    setOptions(newOptions);

    // Update correct answer(s) when removing an option
    if (stepType === "MCQ_SINGLE" || stepType === "TRUE_FALSE") {
      if (correctAnswer !== null && correctAnswer >= index) {
        setCorrectAnswer(correctAnswer > index ? correctAnswer - 1 : null);
      }
    } else if (stepType === "MCQ_MULTI") {
      const newCorrectAnswers = correctAnswers
        .filter(a => a !== index)
        .map(a => a > index ? a - 1 : a);
      setCorrectAnswers(newCorrectAnswers);
    }
  };

  const toggleCorrectAnswer = (index: number) => {
    if (stepType === "MCQ_MULTI") {
      setCorrectAnswers(prev =>
        prev.includes(index) ? prev.filter(i => i !== index) : [...prev, index]
      );
    } else {
      setCorrectAnswer(index);
    }
  };

  const isMCQ = stepType === "MCQ_SINGLE" || stepType === "MCQ_MULTI" || stepType === "TRUE_FALSE";
  const isChat = stepType === "CHAT";
  const isSubmitting = createMutation.isPending || updateMutation.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{isEditing ? "Edit Step" : "Create Step"}</DialogTitle>
          <DialogDescription>
            {isEditing ? "Update step details and configuration." : "Add a new step to the challenge."}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Step Type */}
          <div className="space-y-2">
            <Label htmlFor="step_type">
              Step Type <span className="text-destructive">*</span>
            </Label>
            <Select value={stepType} onValueChange={(value) => setValue("step_type", value)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="CHAT">CHAT - Free text response</SelectItem>
                <SelectItem value="MCQ_SINGLE">MCQ_SINGLE - Single choice</SelectItem>
                <SelectItem value="MCQ_MULTI">MCQ_MULTI - Multiple choice</SelectItem>
                <SelectItem value="TRUE_FALSE">TRUE_FALSE - True/False</SelectItem>
                <SelectItem value="FILE_UPLOAD">FILE_UPLOAD - File submission</SelectItem>
                <SelectItem value="CONTINUE_GATE">CONTINUE_GATE - Narrative pause</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Title */}
          <div className="space-y-2">
            <Label htmlFor="title">
              Title <span className="text-destructive">*</span>
            </Label>
            <Input
              id="title"
              {...register("title", { required: "Title is required" })}
              placeholder="e.g., Explain the concept"
            />
            {errors.title && <p className="text-sm text-destructive">{errors.title.message}</p>}
          </div>

          {/* Instruction */}
          <div className="space-y-2">
            <Label htmlFor="instruction">
              Instruction <span className="text-destructive">*</span>
            </Label>
            <Textarea
              id="instruction"
              {...register("instruction", { required: "Instruction is required" })}
              placeholder="What should the learner do in this step?"
              rows={3}
            />
            {errors.instruction && (
              <p className="text-sm text-destructive">{errors.instruction.message}</p>
            )}
          </div>

          {/* MCQ Options */}
          {isMCQ && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label>
                  Options {stepType === "TRUE_FALSE" ? "(Auto: True/False)" : ""}
                  {stepType === "MCQ_MULTI" && (
                    <span className="text-xs text-muted-foreground ml-2">
                      (Check correct answers)
                    </span>
                  )}
                  {stepType === "MCQ_SINGLE" && (
                    <span className="text-xs text-muted-foreground ml-2">
                      (Select correct answer)
                    </span>
                  )}
                </Label>
                {stepType !== "TRUE_FALSE" && (
                  <Button type="button" onClick={addOption} size="sm" variant="outline">
                    <Plus className="h-4 w-4 mr-2" />
                    Add Option
                  </Button>
                )}
              </div>
              {stepType === "TRUE_FALSE" ? (
                <div className="space-y-2">
                  <div className="text-sm text-muted-foreground mb-2">
                    True/False options are automatically generated
                  </div>
                  <RadioGroup value={correctAnswer?.toString()} onValueChange={(v) => setCorrectAnswer(parseInt(v))}>
                    <div className="flex items-center space-x-2 p-2 border border-border/50 rounded-md">
                      <RadioGroupItem value="0" id="true-option" />
                      <Label htmlFor="true-option" className="flex-1 cursor-pointer font-normal">
                        True
                      </Label>
                    </div>
                    <div className="flex items-center space-x-2 p-2 border border-border/50 rounded-md">
                      <RadioGroupItem value="1" id="false-option" />
                      <Label htmlFor="false-option" className="flex-1 cursor-pointer font-normal">
                        False
                      </Label>
                    </div>
                  </RadioGroup>
                </div>
              ) : stepType === "MCQ_SINGLE" ? (
                <div className="space-y-2">
                  <RadioGroup value={correctAnswer?.toString()} onValueChange={(v) => setCorrectAnswer(parseInt(v))}>
                    {options.map((option, index) => (
                      <div key={index} className="flex items-center gap-2">
                        <div className="flex items-center space-x-2 p-2 border border-border/50 rounded-md flex-1">
                          <RadioGroupItem value={index.toString()} id={`option-${index}`} />
                          <Input
                            value={option}
                            onChange={(e) => updateOption(index, e.target.value)}
                            placeholder={`Option ${index + 1}`}
                            className="border-0 focus-visible:ring-0 focus-visible:ring-offset-0 p-0 h-auto"
                          />
                        </div>
                        <Button
                          type="button"
                          onClick={() => removeOption(index)}
                          size="icon"
                          variant="ghost"
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    ))}
                  </RadioGroup>
                  {options.length === 0 && (
                    <p className="text-sm text-muted-foreground">No options yet. Add at least 2.</p>
                  )}
                </div>
              ) : (
                <div className="space-y-2">
                  {options.map((option, index) => (
                    <div key={index} className="flex items-center gap-2">
                      <div className="flex items-center space-x-2 p-2 border border-border/50 rounded-md flex-1">
                        <Checkbox
                          id={`option-${index}`}
                          checked={correctAnswers.includes(index)}
                          onCheckedChange={() => toggleCorrectAnswer(index)}
                        />
                        <Input
                          value={option}
                          onChange={(e) => updateOption(index, e.target.value)}
                          placeholder={`Option ${index + 1}`}
                          className="border-0 focus-visible:ring-0 focus-visible:ring-offset-0 p-0 h-auto"
                        />
                      </div>
                      <Button
                        type="button"
                        onClick={() => removeOption(index)}
                        size="icon"
                        variant="ghost"
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                  {options.length === 0 && (
                    <p className="text-sm text-muted-foreground">No options yet. Add at least 2.</p>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Rubric (CHAT only) */}
          {isChat && (
            <div className="space-y-2">
              <Label htmlFor="rubric">Rubric (JSON)</Label>
              <Textarea
                id="rubric"
                value={rubricJson}
                onChange={(e) => setRubricJson(e.target.value)}
                placeholder='{"criteria": {...}, "examples": {...}}'
                rows={4}
                className="font-mono text-xs"
              />
              <p className="text-xs text-muted-foreground">
                Optional: Define evaluation criteria for LEM
              </p>
            </div>
          )}

          {/* Points and Passing Threshold */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="points_possible">Points Possible</Label>
              <Input
                id="points_possible"
                type="number"
                {...register("points_possible", { valueAsNumber: true, min: 0 })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="passing_threshold">Passing Threshold (%)</Label>
              <Input
                id="passing_threshold"
                type="number"
                {...register("passing_threshold", { valueAsNumber: true, min: 0, max: 100 })}
              />
            </div>
          </div>

          {/* GM Context */}
          <div className="space-y-2">
            <Label htmlFor="gm_context">GM Context (optional)</Label>
            <Textarea
              id="gm_context"
              {...register("gm_context")}
              placeholder="Context for GM narration..."
              rows={2}
            />
          </div>

          {/* Auto Narrate */}
          <div className="flex items-center space-x-2">
            <Switch
              id="auto_narrate"
              checked={autoNarrate}
              onCheckedChange={(checked) => setValue("auto_narrate", checked)}
            />
            <Label htmlFor="auto_narrate" className="font-normal">
              Auto narrate on step entry
            </Label>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  {isEditing ? "Updating..." : "Creating..."}
                </>
              ) : isEditing ? (
                "Update Step"
              ) : (
                "Create Step"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
