import { Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ThemeToggle } from "@/components/ThemeToggle";
import { Shield, ArrowLeft, Loader2 } from "lucide-react";
import ChallengesTab from "@/components/admin/ChallengesTab";

export default function Admin() {
  const { user, loading, isAdmin } = useAuth();
  const navigate = useNavigate();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!user) return <Navigate to="/auth" replace />;
  if (!isAdmin) return <Navigate to="/" replace />;

  return (
    <div className="min-h-screen bg-background">
      <div className="absolute inset-0 bg-grid-pattern opacity-5 pointer-events-none" />

      <header className="glass-dark border-b border-border/50 p-4 relative z-10">
        <div className="container mx-auto flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate("/")}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <Shield className="h-5 w-5 text-primary" />
          <h1 className="text-xl font-bold">Admin Panel</h1>
          <div className="ml-auto">
            <ThemeToggle />
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8 max-w-7xl relative z-10">
        <Tabs defaultValue="challenges" className="space-y-6">
          <TabsList className="glass-dark">
            <TabsTrigger value="challenges">Challenges</TabsTrigger>
            <TabsTrigger value="personas">Personas</TabsTrigger>
            <TabsTrigger value="scenes">Scenes</TabsTrigger>
            <TabsTrigger value="media">Media</TabsTrigger>
            <TabsTrigger value="knowledge">Knowledge Base</TabsTrigger>
          </TabsList>

          <TabsContent value="challenges" className="space-y-4">
            <ChallengesTab />
          </TabsContent>

          <TabsContent value="personas" className="space-y-4">
            <div className="glass-dark p-8 rounded-xl border border-border/50 text-center">
              <p className="text-muted-foreground">Personas management coming soon</p>
            </div>
          </TabsContent>

          <TabsContent value="scenes" className="space-y-4">
            <div className="glass-dark p-8 rounded-xl border border-border/50 text-center">
              <p className="text-muted-foreground">Scenes management coming soon</p>
            </div>
          </TabsContent>

          <TabsContent value="media" className="space-y-4">
            <div className="glass-dark p-8 rounded-xl border border-border/50 text-center">
              <p className="text-muted-foreground">Media management coming soon</p>
            </div>
          </TabsContent>

          <TabsContent value="knowledge" className="space-y-4">
            <div className="glass-dark p-8 rounded-xl border border-border/50 text-center">
              <p className="text-muted-foreground">Knowledge Base management coming soon</p>
            </div>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
