import { Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import { useProfile, useAllBadges } from "@/hooks/useProfile";
import { useUserProgress } from "@/hooks/useChallenges";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Loader2, ArrowLeft, Trophy, Zap, Star, Award, Lock } from "lucide-react";

const badgeIcons: Record<string, any> = {
  trophy: Trophy,
  zap: Zap,
  star: Star,
  flame: Zap,
  sparkles: Star,
  brain: Award,
  code: Award,
  compass: Award,
};

export default function Profile() {
  const { user, loading: authLoading } = useAuth();
  const { profile, badges: userBadges, loading } = useProfile();
  const { badges: allBadges } = useAllBadges();
  const { allProgress } = useUserProgress();
  const navigate = useNavigate();

  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!user) return <Navigate to="/auth" replace />;

  const xpToNextLevel = 500;
  const currentLevelXP = (profile?.xp || 0) % 500;
  const completedChallenges = allProgress.filter((p) => p.status === "completed").length;
  const earnedBadgeIds = userBadges.map((ub) => ub.badge_id);

  return (
    <div className="min-h-screen bg-background">
      <div className="absolute inset-0 bg-grid-pattern opacity-5 pointer-events-none" />

      <header className="glass-dark border-b border-border/50 p-4">
        <div className="container mx-auto flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate("/")}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <h1 className="text-xl font-bold">Profile</h1>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Profile Card */}
        <Card className="glass-dark border-border/50 mb-8">
          <CardContent className="pt-6">
            <div className="flex items-center gap-6">
              <div className="w-20 h-20 rounded-full gradient-primary flex items-center justify-center text-3xl font-bold text-primary-foreground">
                {profile?.username?.[0]?.toUpperCase() || "U"}
              </div>
              <div className="flex-1">
                <h2 className="text-2xl font-bold">{profile?.username || "Learner"}</h2>
                <p className="text-muted-foreground">{user.email}</p>
                <div className="flex items-center gap-4 mt-2">
                  <Badge className="gradient-primary">Level {profile?.level || 1}</Badge>
                  <span className="text-sm text-muted-foreground">
                    {completedChallenges} challenges completed
                  </span>
                </div>
              </div>
            </div>

            <div className="mt-6">
              <div className="flex justify-between text-sm mb-2">
                <span>XP to next level</span>
                <span className="font-mono">{currentLevelXP} / {xpToNextLevel}</span>
              </div>
              <Progress value={(currentLevelXP / xpToNextLevel) * 100} className="h-3" />
            </div>
          </CardContent>
        </Card>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          <Card className="glass-dark border-border/50 text-center">
            <CardContent className="pt-6">
              <Zap className="h-8 w-8 mx-auto text-primary mb-2" />
              <p className="text-2xl font-bold">{profile?.xp || 0}</p>
              <p className="text-sm text-muted-foreground">Total XP</p>
            </CardContent>
          </Card>
          <Card className="glass-dark border-border/50 text-center">
            <CardContent className="pt-6">
              <Trophy className="h-8 w-8 mx-auto text-accent mb-2" />
              <p className="text-2xl font-bold">{completedChallenges}</p>
              <p className="text-sm text-muted-foreground">Completed</p>
            </CardContent>
          </Card>
          <Card className="glass-dark border-border/50 text-center">
            <CardContent className="pt-6">
              <Award className="h-8 w-8 mx-auto text-warning mb-2" />
              <p className="text-2xl font-bold">{userBadges.length}</p>
              <p className="text-sm text-muted-foreground">Badges</p>
            </CardContent>
          </Card>
        </div>

        {/* Badges */}
        <Card className="glass-dark border-border/50">
          <CardHeader>
            <CardTitle>Badges</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {allBadges.map((badge) => {
                const earned = earnedBadgeIds.includes(badge.id);
                const IconComponent = badgeIcons[badge.icon] || Award;

                return (
                  <div
                    key={badge.id}
                    className={`p-4 rounded-xl text-center transition-all ${
                      earned
                        ? "bg-primary/10 border border-primary/30"
                        : "bg-muted/30 border border-border/50 opacity-50"
                    }`}
                  >
                    <div
                      className={`w-12 h-12 mx-auto rounded-full flex items-center justify-center mb-2 ${
                        earned ? "gradient-primary" : "bg-muted"
                      }`}
                    >
                      {earned ? (
                        <IconComponent className="h-6 w-6 text-primary-foreground" />
                      ) : (
                        <Lock className="h-5 w-5 text-muted-foreground" />
                      )}
                    </div>
                    <p className="font-medium text-sm">{badge.name}</p>
                    <p className="text-xs text-muted-foreground mt-1">{badge.description}</p>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
