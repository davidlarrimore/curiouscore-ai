import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle, CheckCircle2, AlertTriangle, Loader2 } from "lucide-react";
import {
  useVerifyPrompt,
  type VerificationResult,
} from "@/hooks/useAdminChallenges";
import { useToast } from "@/hooks/use-toast";

interface VerificationPanelProps {
  systemPrompt: string;
  challengeTitle: string;
  difficulty: string;
}

export function VerificationPanel({
  systemPrompt,
  challengeTitle,
  difficulty,
}: VerificationPanelProps) {
  const [result, setResult] = useState<VerificationResult | null>(null);
  const { toast } = useToast();
  const verifyMutation = useVerifyPrompt();

  const handleVerify = async (runLLM: boolean = true) => {
    try {
      const verificationResult = await verifyMutation.mutateAsync({
        system_prompt: systemPrompt,
        title: challengeTitle,
        difficulty,
        run_llm: runLLM,
      });
      setResult(verificationResult);
    } catch (error) {
      toast({
        title: "Verification failed",
        description: error instanceof Error ? error.message : "Unknown error",
        variant: "destructive",
      });
    }
  };

  const getRecommendationBadge = (recommendation: string) => {
    switch (recommendation) {
      case "approve":
        return (
          <Badge className="bg-green-500 hover:bg-green-600">
            <CheckCircle2 className="h-3 w-3 mr-1" />
            APPROVED
          </Badge>
        );
      case "review":
        return (
          <Badge className="bg-yellow-500 hover:bg-yellow-600">
            <AlertTriangle className="h-3 w-3 mr-1" />
            NEEDS REVIEW
          </Badge>
        );
      case "reject":
        return (
          <Badge variant="destructive">
            <AlertCircle className="h-3 w-3 mr-1" />
            REJECTED
          </Badge>
        );
      default:
        return null;
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-center">
          <div>
            <CardTitle>Instructions Verification</CardTitle>
            <CardDescription>
              Validate your challenge instructions meet quality standards
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Button
              onClick={() => handleVerify(false)}
              variant="outline"
              size="sm"
              disabled={verifyMutation.isPending || !systemPrompt}
              type="button"
            >
              {verifyMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Checking...
                </>
              ) : (
                "Quick Check"
              )}
            </Button>
            <Button
              onClick={() => handleVerify(true)}
              size="sm"
              disabled={verifyMutation.isPending || !systemPrompt}
              type="button"
            >
              {verifyMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Validating...
                </>
              ) : (
                "Full Validation"
              )}
            </Button>
          </div>
        </div>
      </CardHeader>

      {result && (
        <CardContent className="space-y-6">
          {/* Overall Recommendation */}
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Overall Recommendation:</span>
            {getRecommendationBadge(result.overall_recommendation)}
          </div>

          {/* Tier 1: Heuristic Analysis */}
          <div className="space-y-3">
            <h4 className="font-medium text-sm flex items-center gap-2">
              Tier 1: Heuristic Analysis
              <Badge variant="outline" className="text-xs">
                Score: {result.tier1_heuristics.score}/100
              </Badge>
            </h4>

            <Progress value={result.tier1_heuristics.score} className="h-2" />

            {result.tier1_heuristics.issues.length > 0 && (
              <div className="space-y-2">
                {result.tier1_heuristics.issues.map((issue, index) => (
                  <Alert key={index} variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{issue}</AlertDescription>
                  </Alert>
                ))}
              </div>
            )}

            {result.tier1_heuristics.warnings.length > 0 && (
              <div className="space-y-2">
                {result.tier1_heuristics.warnings.map((warning, index) => (
                  <Alert key={index}>
                    <AlertTriangle className="h-4 w-4" />
                    <AlertDescription>{warning}</AlertDescription>
                  </Alert>
                ))}
              </div>
            )}

            {result.tier1_heuristics.issues.length === 0 &&
              result.tier1_heuristics.warnings.length === 0 && (
                <Alert>
                  <CheckCircle2 className="h-4 w-4" />
                  <AlertDescription>
                    All heuristic checks passed!
                  </AlertDescription>
                </Alert>
              )}
          </div>

          {/* Tier 2: LLM Validation */}
          {result.tier2_llm && (
            <div className="space-y-3">
              <h4 className="font-medium text-sm flex items-center gap-2">
                Tier 2: LLM Validation
                <Badge variant="outline" className="text-xs">
                  Confidence: {result.tier2_llm.confidence}%
                </Badge>
              </h4>

              <div className="p-3 bg-muted rounded-lg">
                <p className="text-sm text-muted-foreground">
                  {result.tier2_llm.feedback}
                </p>
              </div>

              {result.tier2_llm.suggestions.length > 0 && (
                <div>
                  <p className="text-sm font-medium mb-2">Suggestions:</p>
                  <ul className="space-y-1 text-sm text-muted-foreground">
                    {result.tier2_llm.suggestions.map((suggestion, index) => (
                      <li key={index} className="flex items-start gap-2">
                        <span className="text-primary mt-1">•</span>
                        <span>{suggestion}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Tier 3: Test Run Info */}
          {result.tier3_test_available && (
            <div className="space-y-2">
              <h4 className="font-medium text-sm">Tier 3: Test Run</h4>
              <p className="text-sm text-muted-foreground">
                Once you save this challenge, you can test it with a real LLM conversation!
                Go to the challenges list, click the "..." menu on your challenge, and select "Test Run"
                to verify metadata generation and response quality.
              </p>
            </div>
          )}
        </CardContent>
      )}

      {!result && !verifyMutation.isPending && (
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Click "Quick Check" for instant heuristic analysis, or "Full
            Validation" to include AI-powered quality assessment.
          </p>
        </CardContent>
      )}
    </Card>
  );
}
