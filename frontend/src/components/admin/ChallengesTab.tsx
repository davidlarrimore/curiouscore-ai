import { useState } from "react";
import { useAdminChallenges, useDeleteChallenge } from "@/hooks/useAdminChallenges";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";
import { useToast } from "@/hooks/use-toast";
import { Plus, Search, MoreVertical, Pencil, Trash2, Layers, RefreshCw, PlayCircle } from "lucide-react";
import { ChallengeDialog } from "./dialogs/ChallengeDialog";
import { ConfirmDeleteDialog } from "./ConfirmDeleteDialog";
import { TestRunDialog } from "./dialogs/TestRunDialog";

export default function ChallengesTab() {
  const { toast } = useToast();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [difficulty, setDifficulty] = useState<string>("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedChallengeId, setSelectedChallengeId] = useState<string | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [challengeToDelete, setChallengeToDelete] = useState<{ id: string; title: string } | null>(null);
  const [testRunDialogOpen, setTestRunDialogOpen] = useState(false);
  const [testRunChallenge, setTestRunChallenge] = useState<{ id: string; title: string } | null>(null);

  const { data, isLoading, refetch } = useAdminChallenges({
    page,
    limit: 20,
    search: search || undefined,
    difficulty: difficulty || undefined,
  });

  const deleteMutation = useDeleteChallenge();

  const handleEdit = (challengeId: string) => {
    setSelectedChallengeId(challengeId);
    setDialogOpen(true);
  };

  const handleCreate = () => {
    setSelectedChallengeId(null);
    setDialogOpen(true);
  };

  const handleDelete = (id: string, title: string) => {
    setChallengeToDelete({ id, title });
    setDeleteDialogOpen(true);
  };

  const handleTestRun = (id: string, title: string) => {
    setTestRunChallenge({ id, title });
    setTestRunDialogOpen(true);
  };

  const confirmDelete = async () => {
    if (!challengeToDelete) return;

    try {
      await deleteMutation.mutateAsync(challengeToDelete.id);
      toast({
        title: "Challenge deleted",
        description: `${challengeToDelete.title} has been deleted.`,
      });
      setDeleteDialogOpen(false);
      setChallengeToDelete(null);
    } catch (error) {
      toast({
        title: "Error",
        description: `Failed to delete challenge: ${error instanceof Error ? error.message : 'Unknown error'}`,
        variant: "destructive",
      });
    }
  };

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= (data?.pages || 1)) {
      setPage(newPage);
    }
  };

  const difficultyColors: Record<string, string> = {
    beginner: "bg-green-500/10 text-green-500 border-green-500/20",
    intermediate: "bg-yellow-500/10 text-yellow-500 border-yellow-500/20",
    advanced: "bg-red-500/10 text-red-500 border-red-500/20",
  };

  return (
    <>
      <Card className="glass-dark border-border/50">
        <CardHeader>
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <CardTitle>Challenges</CardTitle>
              <p className="text-sm text-muted-foreground mt-1">
                Manage learning challenges and their configurations
              </p>
            </div>
            <div className="flex gap-2">
              <Button variant="ghost" size="icon" onClick={() => refetch()}>
                <RefreshCw className="h-4 w-4" />
              </Button>
              <Button onClick={handleCreate}>
                <Plus className="h-4 w-4 mr-2" />
                Create Challenge
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Filters */}
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search challenges..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(1);
                }}
                className="pl-10"
              />
            </div>
            <Select
              value={difficulty}
              onValueChange={(value) => {
                setDifficulty(value === "all" ? "" : value);
                setPage(1);
              }}
            >
              <SelectTrigger className="w-full sm:w-[180px]">
                <SelectValue placeholder="All difficulties" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All difficulties</SelectItem>
                <SelectItem value="beginner">Beginner</SelectItem>
                <SelectItem value="intermediate">Intermediate</SelectItem>
                <SelectItem value="advanced">Advanced</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Table */}
          <div className="border border-border/50 rounded-lg overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent border-border/50">
                  <TableHead>Title</TableHead>
                  <TableHead>Difficulty</TableHead>
                  <TableHead>Steps</TableHead>
                  <TableHead>XP</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="w-[70px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  Array.from({ length: 5 }).map((_, i) => (
                    <TableRow key={i}>
                      <TableCell>
                        <Skeleton className="h-4 w-[250px]" />
                      </TableCell>
                      <TableCell>
                        <Skeleton className="h-6 w-[80px]" />
                      </TableCell>
                      <TableCell>
                        <Skeleton className="h-4 w-[40px]" />
                      </TableCell>
                      <TableCell>
                        <Skeleton className="h-4 w-[40px]" />
                      </TableCell>
                      <TableCell>
                        <Skeleton className="h-6 w-[60px]" />
                      </TableCell>
                      <TableCell>
                        <Skeleton className="h-8 w-8" />
                      </TableCell>
                    </TableRow>
                  ))
                ) : data?.items.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center text-muted-foreground py-8">
                      No challenges found
                    </TableCell>
                  </TableRow>
                ) : (
                  data?.items.map((challenge) => (
                    <TableRow key={challenge.id} className="border-border/50">
                      <TableCell className="font-medium">
                        <div>
                          <div>{challenge.title}</div>
                          <div className="text-xs text-muted-foreground line-clamp-1">
                            {challenge.description}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className={difficultyColors[challenge.difficulty] || ""}
                        >
                          {challenge.difficulty}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {challenge.step_count ?? 0}
                      </TableCell>
                      <TableCell className="text-muted-foreground">{challenge.xp_reward}</TableCell>
                      <TableCell>
                        <Badge variant={challenge.is_active ? "default" : "secondary"}>
                          {challenge.is_active ? "Active" : "Inactive"}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreVertical className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => handleEdit(challenge.id)}>
                              <Pencil className="h-4 w-4 mr-2" />
                              Edit
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => handleEdit(challenge.id)}>
                              <Layers className="h-4 w-4 mr-2" />
                              Manage Steps
                            </DropdownMenuItem>
                            {((challenge as any).challenge_type === "simple" || !(challenge as any).challenge_type) && (
                              <DropdownMenuItem onClick={() => handleTestRun(challenge.id, challenge.title)}>
                                <PlayCircle className="h-4 w-4 mr-2" />
                                Test Run
                              </DropdownMenuItem>
                            )}
                            <DropdownMenuItem
                              onClick={() => handleDelete(challenge.id, challenge.title)}
                              className="text-destructive focus:text-destructive"
                            >
                              <Trash2 className="h-4 w-4 mr-2" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>

          {/* Pagination */}
          {data && data.pages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                Showing {(page - 1) * (data.limit || 20) + 1} to{" "}
                {Math.min(page * (data.limit || 20), data.total)} of {data.total} challenges
              </p>
              <Pagination>
                <PaginationContent>
                  <PaginationItem>
                    <PaginationPrevious
                      onClick={() => handlePageChange(page - 1)}
                      className={page === 1 ? "pointer-events-none opacity-50" : "cursor-pointer"}
                    />
                  </PaginationItem>
                  {Array.from({ length: Math.min(5, data.pages) }, (_, i) => {
                    const pageNum = i + 1;
                    return (
                      <PaginationItem key={pageNum}>
                        <PaginationLink
                          onClick={() => handlePageChange(pageNum)}
                          isActive={page === pageNum}
                          className="cursor-pointer"
                        >
                          {pageNum}
                        </PaginationLink>
                      </PaginationItem>
                    );
                  })}
                  <PaginationItem>
                    <PaginationNext
                      onClick={() => handlePageChange(page + 1)}
                      className={
                        page === data.pages ? "pointer-events-none opacity-50" : "cursor-pointer"
                      }
                    />
                  </PaginationItem>
                </PaginationContent>
              </Pagination>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Dialogs */}
      <ChallengeDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        challengeId={selectedChallengeId}
      />

      <ConfirmDeleteDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        title="Delete Challenge"
        description={`Are you sure you want to delete "${challengeToDelete?.title}"? This will permanently delete the challenge and all its steps, personas, scenes, and associated data.`}
        onConfirm={confirmDelete}
        isLoading={deleteMutation.isPending}
      />

      {testRunChallenge && (
        <TestRunDialog
          open={testRunDialogOpen}
          onOpenChange={setTestRunDialogOpen}
          challengeId={testRunChallenge.id}
          challengeTitle={testRunChallenge.title}
        />
      )}
    </>
  );
}
