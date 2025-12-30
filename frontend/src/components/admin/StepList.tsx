import { useState } from "react";
import { useAdminSteps, useDeleteStep, useReorderSteps } from "@/hooks/useAdminSteps";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useToast } from "@/hooks/use-toast";
import { Plus, Pencil, Trash2, GripVertical, ChevronUp, ChevronDown } from "lucide-react";
import { ConfirmDeleteDialog } from "./ConfirmDeleteDialog";
import { StepDialog } from "./dialogs/StepDialog";

interface StepListProps {
  challengeId: string;
}

export function StepList({ challengeId }: StepListProps) {
  const { toast } = useToast();
  const { data: steps, isLoading } = useAdminSteps(challengeId);
  const deleteMutation = useDeleteStep();
  const reorderMutation = useReorderSteps();

  const [stepDialogOpen, setStepDialogOpen] = useState(false);
  const [selectedStepId, setSelectedStepId] = useState<string | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [stepToDelete, setStepToDelete] = useState<{ id: string; title: string } | null>(null);

  const handleCreate = () => {
    setSelectedStepId(null);
    setStepDialogOpen(true);
  };

  const handleEdit = (stepId: string) => {
    setSelectedStepId(stepId);
    setStepDialogOpen(true);
  };

  const handleDelete = (stepId: string, title: string) => {
    setStepToDelete({ id: stepId, title });
    setDeleteDialogOpen(true);
  };

  const confirmDelete = async () => {
    if (!stepToDelete) return;

    try {
      await deleteMutation.mutateAsync({ challengeId, stepId: stepToDelete.id });
      toast({
        title: "Step deleted",
        description: `${stepToDelete.title} has been deleted.`,
      });
      setDeleteDialogOpen(false);
      setStepToDelete(null);
    } catch (error) {
      toast({
        title: "Error",
        description: `Failed to delete step: ${error instanceof Error ? error.message : "Unknown error"}`,
        variant: "destructive",
      });
    }
  };

  const handleMoveStep = async (stepId: string, direction: "up" | "down") => {
    if (!steps) return;

    const currentIndex = steps.findIndex((s) => s.id === stepId);
    if (currentIndex === -1) return;

    const newIndex = direction === "up" ? currentIndex - 1 : currentIndex + 1;
    if (newIndex < 0 || newIndex >= steps.length) return;

    // Create new order
    const reordered = [...steps];
    const [moved] = reordered.splice(currentIndex, 1);
    reordered.splice(newIndex, 0, moved);

    try {
      await reorderMutation.mutateAsync({
        challengeId,
        stepIds: reordered.map((s) => s.id),
      });
      toast({
        title: "Steps reordered",
        description: "Step order has been updated.",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: `Failed to reorder steps: ${error instanceof Error ? error.message : "Unknown error"}`,
        variant: "destructive",
      });
    }
  };

  const stepTypeColors: Record<string, string> = {
    CHAT: "bg-blue-500/10 text-blue-500 border-blue-500/20",
    MCQ_SINGLE: "bg-purple-500/10 text-purple-500 border-purple-500/20",
    MCQ_MULTI: "bg-purple-500/10 text-purple-500 border-purple-500/20",
    TRUE_FALSE: "bg-green-500/10 text-green-500 border-green-500/20",
    FILE_UPLOAD: "bg-orange-500/10 text-orange-500 border-orange-500/20",
    CONTINUE_GATE: "bg-gray-500/10 text-gray-500 border-gray-500/20",
  };

  return (
    <>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold">Challenge Steps</h3>
            <p className="text-sm text-muted-foreground">
              Create and manage the learning journey
            </p>
          </div>
          <Button onClick={handleCreate} size="sm">
            <Plus className="h-4 w-4 mr-2" />
            Add Step
          </Button>
        </div>

        {isLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        ) : steps && steps.length === 0 ? (
          <div className="border border-dashed border-border/50 rounded-lg p-8 text-center">
            <p className="text-muted-foreground">No steps yet</p>
            <p className="text-sm text-muted-foreground mt-1">
              Add your first step to begin building the challenge
            </p>
          </div>
        ) : (
          <div className="border border-border/50 rounded-lg overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent border-border/50">
                  <TableHead className="w-[50px]">#</TableHead>
                  <TableHead>Title</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Points</TableHead>
                  <TableHead className="w-[120px]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {steps?.map((step, index) => (
                  <TableRow key={step.id} className="border-border/50">
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <GripVertical className="h-4 w-4 text-muted-foreground" />
                        <span className="text-muted-foreground">{step.step_index}</span>
                      </div>
                    </TableCell>
                    <TableCell className="font-medium">
                      <div>
                        <div>{step.title}</div>
                        <div className="text-xs text-muted-foreground line-clamp-1">
                          {step.instruction}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className={stepTypeColors[step.step_type] || ""}>
                        {step.step_type.replace(/_/g, " ")}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">{step.points_possible}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleMoveStep(step.id, "up")}
                          disabled={index === 0 || reorderMutation.isPending}
                          className="h-8 w-8"
                        >
                          <ChevronUp className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleMoveStep(step.id, "down")}
                          disabled={index === (steps?.length || 0) - 1 || reorderMutation.isPending}
                          className="h-8 w-8"
                        >
                          <ChevronDown className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleEdit(step.id)}
                          className="h-8 w-8"
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDelete(step.id, step.title)}
                          className="h-8 w-8 text-destructive hover:text-destructive"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </div>

      {/* Dialogs */}
      <StepDialog
        open={stepDialogOpen}
        onOpenChange={setStepDialogOpen}
        challengeId={challengeId}
        stepId={selectedStepId}
      />

      <ConfirmDeleteDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        title="Delete Step"
        description={`Are you sure you want to delete "${stepToDelete?.title}"? This action cannot be undone.`}
        onConfirm={confirmDelete}
        isLoading={deleteMutation.isPending}
      />
    </>
  );
}
