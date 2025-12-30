import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import {
  AlertCircle,
  CheckCircle2,
  Loader2,
  PlayCircle,
  Info,
} from "lucide-react";
import { useTestChallenge, type TestRunResult } from "@/hooks/useAdminChallenges";

interface TestRunDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  challengeId: string;
  challengeTitle: string;
}

export function TestRunDialog({
  open,
  onOpenChange,
  challengeId,
  challengeTitle,
}: TestRunDialogProps) {
  const { toast } = useToast();
  const [testMessage, setTestMessage] = useState("");
  const [result, setResult] = useState<TestRunResult | null>(null);
  const testMutation = useTestChallenge();

  const handleTest = async () => {
    if (!testMessage.trim()) {
      toast({
        title: "Test message required",
        description: "Please enter a test message to send to the challenge.",
        variant: "destructive",
      });
      return;
    }

    try {
      const testResult = await testMutation.mutateAsync({
        challengeId,
        payload: { test_message: testMessage },
      });
      setResult(testResult);
    } catch (error) {
      toast({
        title: "Test run failed",
        description: error instanceof Error ? error.message : "Unknown error",
        variant: "destructive",
      });
    }
  };

  const handleClose = () => {
    setTestMessage("");
    setResult(null);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Test Run: {challengeTitle}</DialogTitle>
          <DialogDescription>
            Send a test message to verify the challenge responds correctly with metadata.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Info Alert */}
          <Alert>
            <Info className="h-4 w-4" />
            <AlertDescription>
              This test verifies that your challenge correctly generates metadata
              (like progress, scoring, and next steps) in its responses.
            </AlertDescription>
          </Alert>

          {/* Test Message Input */}
          <div className="space-y-2">
            <Label htmlFor="test_message">Test Message</Label>
            <Textarea
              id="test_message"
              value={testMessage}
              onChange={(e) => setTestMessage(e.target.value)}
              placeholder="Enter a sample message to test the challenge (e.g., 'Hello, I'm ready to start')"
              rows={4}
              disabled={testMutation.isPending}
            />
          </div>

          {/* Test Results */}
          {result && (
            <div className="space-y-4">
              {/* Success/Failure Badge */}
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Test Result:</span>
                {result.success ? (
                  <Badge className="bg-green-500 hover:bg-green-600">
                    <CheckCircle2 className="h-3 w-3 mr-1" />
                    PASSED
                  </Badge>
                ) : (
                  <Badge variant="destructive">
                    <AlertCircle className="h-3 w-3 mr-1" />
                    FAILED
                  </Badge>
                )}
              </div>

              {/* Response Content */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">AI Response</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="p-3 bg-muted rounded-lg">
                    <p className="text-sm whitespace-pre-wrap">{result.content || "No content returned"}</p>
                  </div>
                </CardContent>
              </Card>

              {/* Metadata */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm flex items-center gap-2">
                    Metadata
                    {result.metadata_found ? (
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                    ) : (
                      <AlertCircle className="h-4 w-4 text-destructive" />
                    )}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {result.metadata_found ? (
                    <div className="p-3 bg-muted rounded-lg">
                      <pre className="text-xs overflow-x-auto">
                        {JSON.stringify(result.metadata, null, 2)}
                      </pre>
                    </div>
                  ) : (
                    <Alert variant="destructive">
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>
                        No metadata found in response. Make sure your challenge
                        instructions include the metadata requirements.
                      </AlertDescription>
                    </Alert>
                  )}
                </CardContent>
              </Card>

              {/* Debugging Information */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Debugging Information</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {/* LLM Config */}
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="font-medium">Provider:</span>{" "}
                      {(result as any).provider || "unknown"}
                    </div>
                    <div>
                      <span className="font-medium">Model:</span>{" "}
                      {(result as any).model || "unknown"}
                    </div>
                    <div>
                      <span className="font-medium">Response Length:</span>{" "}
                      {(result as any).full_response_length || "unknown"} chars
                    </div>
                    <div>
                      <span className="font-medium">Metadata Instructions:</span>{" "}
                      {(result as any).metadata_instructions_included ? (
                        <Badge variant="outline" className="text-xs bg-green-500/10 text-green-500 border-green-500/20">
                          Included
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="text-xs bg-red-500/10 text-red-500 border-red-500/20">
                          Missing
                        </Badge>
                      )}
                    </div>
                  </div>

                  {/* System Prompt Preview */}
                  <details className="text-sm">
                    <summary className="cursor-pointer font-medium hover:underline">
                      View system prompt (last 1000 chars)
                    </summary>
                    <div className="mt-2 p-3 bg-muted rounded-lg">
                      <pre className="text-xs whitespace-pre-wrap">
                        {(result as any).system_prompt_preview || "Not available"}
                      </pre>
                    </div>
                  </details>

                  {/* Raw Response */}
                  <details className="text-sm">
                    <summary className="cursor-pointer font-medium hover:underline">
                      View raw response (first 500 chars)
                    </summary>
                    <div className="mt-2 p-3 bg-muted rounded-lg">
                      <pre className="text-xs whitespace-pre-wrap">
                        {result.raw_response}
                      </pre>
                    </div>
                  </details>
                </CardContent>
              </Card>

              {/* Troubleshooting Tips */}
              {!result.metadata_found && (
                <Alert>
                  <Info className="h-4 w-4" />
                  <AlertDescription>
                    <p className="font-medium mb-2">Metadata Not Found - Troubleshooting Tips:</p>
                    <ul className="text-xs space-y-1 list-disc list-inside">
                      <li>The LLM model may not be following structured output instructions well</li>
                      <li>Try using a more capable model (e.g., Claude Sonnet or GPT-4)</li>
                      <li>Your challenge instructions may be too long or complex</li>
                      <li>Try a different test message that's more specific</li>
                      <li>Check if the system prompt preview shows metadata instructions at the end</li>
                    </ul>
                  </AlertDescription>
                </Alert>
              )}
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose}>
            Close
          </Button>
          <Button
            onClick={handleTest}
            disabled={testMutation.isPending || !testMessage.trim()}
          >
            {testMutation.isPending ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Testing...
              </>
            ) : (
              <>
                <PlayCircle className="h-4 w-4 mr-2" />
                Run Test
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
