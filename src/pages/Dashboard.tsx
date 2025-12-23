import { useNavigate, Navigate } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import { useChallenges, useUserProgress } from "@/hooks/useChallenges";
import { useProfile } from "@/hooks/useProfile";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Loader2, Sparkles, Trophy, Zap, LogOut, User, Shield, Clock, Star } from "lucide-react";

const difficultyColors = {
  beginner: "bg-success/20 text-success border-success/30",
  intermediate: "bg-warning/20 text-warning border-warning/30",
  advanced: "bg-primary/20 text-primary border-primary/30",
  expert: "bg-destructive/20 text-destructive border-destructive/30",
};

const tagColors: Record<string, string> = {
  "Generative AI": "bg-neon-purple/20 text-neon-purple",
  "NLP": "bg-neon-cyan/20 text-neon-cyan",
  "Biometrics and FRT": "bg-neon-pink/20 text-neon-pink",
  "Prompt Engineering": "bg-primary/20 text-primary",
  "AI Ops": "bg-accent/20 text-accent",
};

export default function Dashboard() {
  const { user, loading: authLoading, signOut, isAdmin } = useAuth();
  const { challenges, loading: challengesLoading } = useChallenges();
  const { allProgress } = useUserProgress();
  const { profile } = useProfile();
  const navigate = useNavigate();

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/auth" replace />;
  }

  const getProgressForChallenge = (challengeId: string) => {
    return allProgress.find((p) => p.challenge_id === challengeId);
  };

  const completedChallenges = allProgress.filter((p) => p.status === "completed").length;
  const totalXP = profile?.xp || 0;
  const level = profile?.level || 1;

  return (
    <div className="min-h-screen bg-background">
      <div className="absolute inset-0 bg-grid-pattern opacity-5 pointer-events-none" />

      {/* Header */}
      <header className="sticky top-0 z-50 glass-dark border-b border-border/50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl gradient-primary flex items-center justify-center">
              <Sparkles className="h-5 w-5 text-primary-foreground" />
            </div>
            <h1 className="text-xl font-bold">AI Challenge Hub</h1>
          </div>

          <div className="flex items-center gap-4">
            {isAdmin && (
              <Button variant="outline" size="sm" onClick={() => navigate("/admin")} className="gap-2">
                <Shield className="h-4 w-4" />
                Admin
              </Button>
            )}
            <Button variant="ghost" size="sm" onClick={() => navigate("/profile")} className="gap-2">
              <User className="h-4 w-4" />
              Profile
            </Button>
            <Button variant="ghost" size="sm" onClick={signOut} className="gap-2">
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <Card className="glass-dark border-border/50">
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-primary/20 flex items-center justify-center">
                  <Zap className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Total XP</p>
                  <p className="text-2xl font-bold">{totalXP.toLocaleString()}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="glass-dark border-border/50">
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-accent/20 flex items-center justify-center">
                  <Star className="h-6 w-6 text-accent" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Level</p>
                  <p className="text-2xl font-bold">{level}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="glass-dark border-border/50">
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-success/20 flex items-center justify-center">
                  <Trophy className="h-6 w-6 text-success" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Completed</p>
                  <p className="text-2xl font-bold">{completedChallenges}/{challenges.length}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Challenges */}
        <h2 className="text-2xl font-bold mb-6">Challenges</h2>

        {challengesLoading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {challenges.map((challenge) => {
              const progress = getProgressForChallenge(challenge.id);
              const isCompleted = progress?.status === "completed";
              const isInProgress = progress?.status === "in_progress";

              return (
                <Card
                  key={challenge.id}
                  className={`glass-dark border-border/50 hover:border-primary/50 transition-all cursor-pointer group ${
                    isCompleted ? "ring-2 ring-success/50" : ""
                  }`}
                  onClick={() => navigate(`/challenge/${challenge.id}`)}
                >
                  <CardHeader>
                    <div className="flex items-start justify-between gap-2">
                      <CardTitle className="text-lg group-hover:text-primary transition-colors">
                        {challenge.title}
                      </CardTitle>
                      <Badge variant="outline" className={difficultyColors[challenge.difficulty]}>
                        {challenge.difficulty}
                      </Badge>
                    </div>
                    <CardDescription className="line-clamp-2">{challenge.description}</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex flex-wrap gap-2">
                      {challenge.tags.map((tag) => (
                        <Badge key={tag} variant="secondary" className={tagColors[tag] || "bg-muted"}>
                          {tag}
                        </Badge>
                      ))}
                    </div>

                    <div className="flex items-center justify-between text-sm text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Clock className="h-4 w-4" />
                        {challenge.estimated_time_minutes}m
                      </span>
                      <span className="flex items-center gap-1">
                        <Zap className="h-4 w-4" />
                        {challenge.xp_reward} XP
                      </span>
                    </div>

                    {(isInProgress || isCompleted) && (
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span>{isCompleted ? "Completed" : "In Progress"}</span>
                          <span>{progress?.progress_percent || 0}%</span>
                        </div>
                        <Progress value={progress?.progress_percent || 0} className="h-2" />
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
}
