import { useEffect, useState, useRef } from "react";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import { Info, Loader2 } from "lucide-react";
import {
  useAdminChallengeDetailed,
  useCreateChallenge,
  useUpdateChallenge,
  type ChallengeCreatePayload,
} from "@/hooks/useAdminChallenges";
import { StepList } from "../StepList";
import { useLLMModels, useChallengeModels, useUpdateChallengeModel, type Provider } from "@/hooks/useAdminModels";
import { VariablePicker } from "../VariablePicker";
import { CustomVariablesEditor } from "../CustomVariablesEditor";
import { VerificationPanel } from "../VerificationPanel";
import { ProgressTrackingEditor } from "../ProgressTrackingEditor";

interface ChallengeDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  challengeId: string | null;
}

export function ChallengeDialog({ open, onOpenChange, challengeId }: ChallengeDialogProps) {
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState("details");
  const isEditing = !!challengeId;

  const { data: challenge, isLoading: isLoadingChallenge } = useAdminChallengeDetailed(challengeId);
  const createMutation = useCreateChallenge();
  const updateMutation = useUpdateChallenge();

  // Challenge type and custom variables state
  const [challengeType, setChallengeType] = useState<"simple" | "advanced">("simple");
  const [customVariables, setCustomVariables] = useState<Record<string, string>>({});
  const [progressTracking, setProgressTracking] = useState<any>(null);
  const promptRef = useRef<HTMLTextAreaElement>(null);

  // LLM Model selection state
  const [selectedProvider, setSelectedProvider] = useState<Provider | "">("");
  const [selectedModel, setSelectedModel] = useState("");
  const { data: models, isLoading: isLoadingModels } = useLLMModels(selectedProvider || null);
  const { data: challengeModels } = useChallengeModels();
  const updateModelMutation = useUpdateChallengeModel();

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    setValue,
    watch,
  } = useForm<ChallengeCreatePayload>({
    defaultValues: {
      title: "",
      description: "",
      tags: [],
      difficulty: "beginner",
      system_prompt: "",
      estimated_time_minutes: 30,
      xp_reward: 100,
      passing_score: 70,
      help_resources: [],
      is_active: true,
      challenge_type: "simple",
      custom_variables: {},
    },
  });

  const difficulty = watch("difficulty");
  const isActive = watch("is_active");
  const systemPrompt = watch("system_prompt");
  const title = watch("title");

  useEffect(() => {
    if (challengeType === "simple" && activeTab === "steps") {
      setActiveTab("details");
    }
  }, [challengeType, activeTab]);

  // Load challenge data when editing
  useEffect(() => {
    if (challenge && isEditing) {
      const challengeTypeValue = (challenge as any).challenge_type || "simple";
      const customVarsValue = (challenge as any).custom_variables || {};

      console.log("Loading challenge data:", challenge.id);
      console.log("custom_variables from API:", customVarsValue);

      // Separate progress_tracking from other custom variables
      const { progress_tracking, ...otherCustomVars } = customVarsValue;

      console.log("progress_tracking extracted:", progress_tracking);
      console.log("other custom vars:", otherCustomVars);

      reset({
        title: challenge.title,
        description: challenge.description,
        tags: challenge.tags,
        difficulty: challenge.difficulty,
        system_prompt: challenge.system_prompt,
        estimated_time_minutes: challenge.estimated_time_minutes,
        xp_reward: challenge.xp_reward,
        passing_score: challenge.passing_score,
        help_resources: challenge.help_resources || [],
        is_active: challenge.is_active,
        challenge_type: challengeTypeValue,
        custom_variables: otherCustomVars,
      });

      setChallengeType(challengeTypeValue as "simple" | "advanced");
      setCustomVariables(otherCustomVars);
      setProgressTracking(progress_tracking || null);
      console.log("Set progressTracking state to:", progress_tracking || null);

      // Load current model mapping
      const currentMapping =
        (challenge as any).llm_config || challengeModels?.find((m) => m.challenge_id === challengeId);

      if (currentMapping) {
        setSelectedProvider(currentMapping.provider);
        setSelectedModel(currentMapping.model);
      } else {
        setSelectedProvider("");
        setSelectedModel("");
      }
    } else if (!isEditing) {
      reset({
        title: "",
        description: "",
        tags: [],
        difficulty: "beginner",
        system_prompt: "",
        estimated_time_minutes: 30,
        xp_reward: 100,
        passing_score: 70,
        help_resources: [],
        is_active: true,
        challenge_type: "simple",
        custom_variables: {},
      });
      setChallengeType("simple");
      setCustomVariables({});
      setSelectedProvider("");
      setSelectedModel("");
    }
  }, [challenge, isEditing, reset, challengeId, challengeModels]);

  // Reset form and tab when dialog closes
  useEffect(() => {
    if (!open) {
      setActiveTab("details");
      if (!isEditing) {
        reset();
      }
    }
  }, [open, isEditing, reset]);

  // Helper function to insert variable at cursor position
  const handleInsertVariable = (variableName: string) => {
    const textarea = promptRef.current;
    if (!textarea) return;

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const currentValue = systemPrompt || "";
    const variableText = `{{${variableName}}}`;

    const newValue =
      currentValue.substring(0, start) +
      variableText +
      currentValue.substring(end);

    setValue("system_prompt", newValue);

    // Set cursor position after inserted variable
    setTimeout(() => {
      textarea.focus();
      textarea.setSelectionRange(
        start + variableText.length,
        start + variableText.length
      );
    }, 0);
  };

  const onSubmit = async (data: ChallengeCreatePayload) => {
    try {
      // Merge progress_tracking into custom_variables
      const finalCustomVariables = { ...customVariables };
      if (progressTracking) {
        finalCustomVariables.progress_tracking = progressTracking;
      } else {
        // Remove progress_tracking if disabled
        delete finalCustomVariables.progress_tracking;
      }

      // Include challenge_type and custom_variables in the submission
      const submitData = {
        ...data,
        challenge_type: challengeType,
        custom_variables: finalCustomVariables,
      };

      let finalChallengeId = challengeId;

      if (isEditing && challengeId) {
        await updateMutation.mutateAsync({ id: challengeId, data: submitData });
        toast({
          title: "Challenge updated",
          description: "The challenge has been successfully updated.",
        });
      } else {
        const newChallenge = await createMutation.mutateAsync(submitData);
        finalChallengeId = newChallenge.id;
        toast({
          title: "Challenge created",
          description: "The challenge has been successfully created.",
        });
      }

      // Update model mapping if provider and model are selected
      if (selectedProvider && selectedModel && finalChallengeId) {
        try {
          await updateModelMutation.mutateAsync({
            challengeId: finalChallengeId,
            provider: selectedProvider as Provider,
            model: selectedModel,
          });
        } catch (modelError) {
          console.error("Failed to update model mapping", modelError);
          toast({
            title: "Warning",
            description: "Challenge saved but model mapping failed to update.",
            variant: "destructive",
          });
        }
      }

      onOpenChange(false);
    } catch (error) {
      toast({
        title: "Error",
        description: `Failed to ${isEditing ? "update" : "create"} challenge: ${
          error instanceof Error ? error.message : "Unknown error"
        }`,
        variant: "destructive",
      });
    }
  };

  const isSubmitting = createMutation.isPending || updateMutation.isPending || updateModelMutation.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{isEditing ? "Edit Challenge" : "Create Challenge"}</DialogTitle>
          <DialogDescription>
            {isEditing
              ? "Update challenge details and manage its steps."
              : "Create a new learning challenge."}
          </DialogDescription>
        </DialogHeader>

        {isLoadingChallenge && isEditing ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        ) : (
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <div className="space-y-2 mb-4">
              <Label>Challenge Type</Label>
              <Tabs value={challengeType} onValueChange={(v) => setChallengeType(v as "simple" | "advanced")}>
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="simple">Simple</TabsTrigger>
                  <TabsTrigger value="advanced">Advanced</TabsTrigger>
                </TabsList>
              </Tabs>
              <p className="text-xs text-muted-foreground">
                {challengeType === "simple"
                  ? "LLM-managed progression with challenge instructions and variables"
                  : "Step-based challenges with precise control over progression"}
              </p>
            </div>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="details">Details</TabsTrigger>
              <TabsTrigger value="steps" disabled={!isEditing || challengeType === "simple"}>
                Steps {isEditing && challenge ? `(${challenge.steps.length})` : ""}
              </TabsTrigger>
            </TabsList>

            <TabsContent value="details" className="space-y-4 mt-4">
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                {/* Title */}
                <div className="space-y-2">
                  <Label htmlFor="title">
                    Title <span className="text-destructive">*</span>
                  </Label>
                  <Input
                    id="title"
                    {...register("title", { required: "Title is required" })}
                    placeholder="e.g., Introduction to Python"
                  />
                  {errors.title && (
                    <p className="text-sm text-destructive">{errors.title.message}</p>
                  )}
                </div>

                {/* Description */}
                <div className="space-y-2">
                  <Label htmlFor="description">
                    Description <span className="text-destructive">*</span>
                  </Label>
                  <Textarea
                    id="description"
                    {...register("description", { required: "Description is required" })}
                    placeholder="Describe what learners will accomplish..."
                    rows={3}
                  />
                  {errors.description && (
                    <p className="text-sm text-destructive">{errors.description.message}</p>
                  )}
                </div>

                {/* Tags */}
                <div className="space-y-2">
                  <Label htmlFor="tags">Tags (comma-separated)</Label>
                  <Input
                    id="tags"
                    placeholder="python, beginner, programming"
                    defaultValue={challenge?.tags.join(", ") || ""}
                    onChange={(e) => {
                      const tags = e.target.value
                        .split(",")
                        .map((tag) => tag.trim())
                        .filter((tag) => tag.length > 0);
                      setValue("tags", tags);
                    }}
                  />
                </div>

                {/* Difficulty and Active Status */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="difficulty">Difficulty</Label>
                    <Select value={difficulty} onValueChange={(value) => setValue("difficulty", value)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="beginner">Beginner</SelectItem>
                        <SelectItem value="intermediate">Intermediate</SelectItem>
                        <SelectItem value="advanced">Advanced</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="is_active">Status</Label>
                    <div className="flex items-center space-x-2 h-10">
                      <Switch
                        id="is_active"
                        checked={isActive}
                        onCheckedChange={(checked) => setValue("is_active", checked)}
                      />
                      <Label htmlFor="is_active" className="font-normal">
                        {isActive ? "Active" : "Inactive"}
                      </Label>
                    </div>
                  </div>
                </div>

                {/* Simple Challenge: Challenge Instructions with Variables */}
                {challengeType === "simple" && (
                  <>
                    {/* Challenge Instructions */}
                    <div className="space-y-2">
                      <Label htmlFor="system_prompt">
                        Challenge Instructions <span className="text-destructive">*</span>
                      </Label>
                      <div className="flex gap-2 mb-2">
                        <VariablePicker
                          onInsert={handleInsertVariable}
                          customVariables={customVariables}
                        />
                      </div>
                      <Textarea
                        id="system_prompt"
                        {...register("system_prompt", { required: challengeType === "simple" ? "Challenge instructions are required" : false })}
                        ref={(e) => {
                          register("system_prompt").ref(e);
                          (promptRef as any).current = e;
                        }}
                        placeholder="Define how the AI should teach and assess learners. Include learning objectives, question types, and progression guidelines..."
                        rows={8}
                      />
                      {errors.system_prompt && (
                        <p className="text-sm text-destructive">{errors.system_prompt.message}</p>
                      )}
                      <p className="text-xs text-muted-foreground">
                        Use {`{{variable}}`} syntax to insert dynamic values. Click "Insert Variable" to browse available options.
                      </p>
                    </div>

                    {/* Custom Variables Editor */}
                    <CustomVariablesEditor
                      variables={customVariables}
                      onChange={setCustomVariables}
                    />

                    {/* Progress Tracking Editor */}
                    <ProgressTrackingEditor
                      config={progressTracking}
                      onChange={setProgressTracking}
                      xpReward={watch("xp_reward") || 100}
                    />

                    {/* Verification Panel */}
                    <VerificationPanel
                      systemPrompt={systemPrompt || ""}
                      challengeTitle={title || "Untitled Challenge"}
                      difficulty={difficulty}
                    />
                  </>
                )}

                {/* Advanced Challenge: Info Alert */}
                {challengeType === "advanced" && (
                  <Alert>
                    <Info className="h-4 w-4" />
                    <AlertDescription>
                      Advanced challenges use steps instead of challenge instructions.
                      Configure steps in the "Steps" tab after saving the challenge.
                    </AlertDescription>
                  </Alert>
                )}

                {/* LLM Model Selection */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="provider">LLM Provider</Label>
                    <Select
                      value={selectedProvider}
                      onValueChange={(value) => {
                        setSelectedProvider(value as Provider);
                        setSelectedModel(""); // Reset model when provider changes
                      }}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select provider" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="openai">OpenAI</SelectItem>
                        <SelectItem value="anthropic">Anthropic</SelectItem>
                        <SelectItem value="gemini">Google Gemini</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="model">LLM Model</Label>
                    <Select
                      value={selectedModel}
                      onValueChange={setSelectedModel}
                      disabled={!selectedProvider || isLoadingModels}
                    >
                      <SelectTrigger>
                        <SelectValue
                          placeholder={
                            !selectedProvider
                              ? "Select provider first"
                              : isLoadingModels
                              ? "Loading models..."
                              : "Select model"
                          }
                        />
                      </SelectTrigger>
                      <SelectContent>
                        {selectedModel && !models?.some((model) => model.id === selectedModel) && (
                          <SelectItem value={selectedModel}>
                            <div className="flex flex-col">
                              <span>{selectedModel}</span>
                              <span className="text-xs text-muted-foreground">
                                Saved selection (not in available list)
                              </span>
                            </div>
                          </SelectItem>
                        )}
                        {models && models.length > 0 ? (
                          models.map((model) => (
                            <SelectItem key={model.id} value={model.id}>
                              <div className="flex flex-col">
                                <span>{model.id}</span>
                                {model.description && (
                                  <span className="text-xs text-muted-foreground">
                                    {model.description}
                                  </span>
                                )}
                              </div>
                            </SelectItem>
                          ))
                        ) : (
                          <SelectItem value="__no_models" disabled>
                            No models available
                          </SelectItem>
                        )}
                      </SelectContent>
                    </Select>
                    {selectedProvider && !selectedModel && (
                      <p className="text-xs text-muted-foreground">
                        Optional: Select a specific model or use system default
                      </p>
                    )}
                  </div>
                </div>

                {/* Estimated Time, XP Reward, Passing Score */}
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="estimated_time_minutes">Time (min)</Label>
                    <Input
                      id="estimated_time_minutes"
                      type="number"
                      {...register("estimated_time_minutes", {
                        valueAsNumber: true,
                        min: 1,
                      })}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="xp_reward">XP Reward</Label>
                    <Input
                      id="xp_reward"
                      type="number"
                      {...register("xp_reward", { valueAsNumber: true, min: 0 })}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="passing_score">Passing %</Label>
                    <Input
                      id="passing_score"
                      type="number"
                      {...register("passing_score", {
                        valueAsNumber: true,
                        min: 0,
                        max: 100,
                      })}
                    />
                  </div>
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
                      "Update Challenge"
                    ) : (
                      "Create Challenge"
                    )}
                  </Button>
                </DialogFooter>
              </form>
            </TabsContent>

            <TabsContent value="steps" className="mt-4">
              {challengeId && challengeType === "advanced" && <StepList challengeId={challengeId} />}
            </TabsContent>
          </Tabs>
        )}
      </DialogContent>
    </Dialog>
  );
}
