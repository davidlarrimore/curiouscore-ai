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
import { Plus, Trash2 } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface CustomVariablesEditorProps {
  variables: Record<string, string>;
  onChange: (variables: Record<string, string>) => void;
}

const RESERVED_VARIABLES = [
  "title",
  "description",
  "difficulty",
  "xp_reward",
  "passing_score",
  "estimated_time",
  "tags",
  "help_resources",
];

export function CustomVariablesEditor({
  variables,
  onChange,
}: CustomVariablesEditorProps) {
  const [newKey, setNewKey] = useState("");
  const [newValue, setNewValue] = useState("");
  const [error, setError] = useState("");

  const handleAdd = () => {
    setError("");

    // Validate key
    if (!newKey.trim()) {
      setError("Variable name is required");
      return;
    }

    // Check if key is alphanumeric + underscores
    if (!/^\w+$/.test(newKey)) {
      setError("Variable name must contain only letters, numbers, and underscores");
      return;
    }

    // Check if key starts with a number
    if (/^\d/.test(newKey)) {
      setError("Variable name cannot start with a number");
      return;
    }

    // Check if key is reserved
    if (RESERVED_VARIABLES.includes(newKey)) {
      setError(`"${newKey}" is a reserved variable name`);
      return;
    }

    // Check if key already exists
    if (variables[newKey]) {
      setError(`Variable "${newKey}" already exists`);
      return;
    }

    // Check value
    if (!newValue.trim()) {
      setError("Variable value is required");
      return;
    }

    // Add variable
    onChange({ ...variables, [newKey]: newValue });
    setNewKey("");
    setNewValue("");
  };

  const handleDelete = (key: string) => {
    const updated = { ...variables };
    delete updated[key];
    onChange(updated);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleAdd();
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Custom Variables</CardTitle>
        <CardDescription>
          Define custom variables to use in your challenge instructions. Use the format {`{{variable_name}}`} in your instructions.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Existing variables */}
        {Object.keys(variables).length > 0 && (
          <div className="space-y-2">
            {Object.entries(variables).map(([key, value]) => (
              <div key={key} className="flex gap-2 items-center">
                <Input
                  value={key}
                  disabled
                  className="font-mono text-sm flex-1"
                />
                <Input value={value} disabled className="flex-[2]" />
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => handleDelete(key)}
                  type="button"
                  className="shrink-0"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </div>
        )}

        {/* Add new variable */}
        <div className="space-y-2">
          <div className="flex gap-2 items-start">
            <div className="flex-1">
              <Input
                placeholder="variable_name"
                value={newKey}
                onChange={(e) => setNewKey(e.target.value)}
                onKeyPress={handleKeyPress}
                className="font-mono text-sm"
              />
            </div>
            <div className="flex-[2]">
              <Input
                placeholder="value"
                value={newValue}
                onChange={(e) => setNewValue(e.target.value)}
                onKeyPress={handleKeyPress}
              />
            </div>
            <Button
              onClick={handleAdd}
              size="icon"
              type="button"
              className="shrink-0"
            >
              <Plus className="h-4 w-4" />
            </Button>
          </div>

          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </div>

        {Object.keys(variables).length === 0 && !error && (
          <div className="text-sm text-muted-foreground">
            No custom variables defined. Add one above to get started.
          </div>
        )}
      </CardContent>
    </Card>
  );
}
