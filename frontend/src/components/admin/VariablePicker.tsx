import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Code } from "lucide-react";

interface VariablePickerProps {
  onInsert: (variable: string) => void;
  customVariables?: Record<string, string>;
}

const BASIC_VARIABLES = [
  { name: "title", description: "Challenge title" },
  { name: "description", description: "Challenge description" },
  { name: "difficulty", description: "Difficulty level" },
  { name: "xp_reward", description: "Total XP reward" },
  { name: "passing_score", description: "Passing score percentage" },
];

const EXTENDED_VARIABLES = [
  { name: "estimated_time", description: "Estimated time in minutes" },
  { name: "tags", description: "Challenge tags (comma-separated)" },
  { name: "help_resources", description: "Help resources (JSON)" },
];

export function VariablePicker({ onInsert, customVariables = {} }: VariablePickerProps) {
  const hasCustomVars = Object.keys(customVariables).length > 0;

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="outline" size="sm" type="button">
          <Code className="h-4 w-4 mr-2" />
          Insert Variable
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-96" align="start">
        <div className="space-y-4">
          {/* Basic Variables */}
          <div>
            <h4 className="font-medium text-sm mb-2">Basic Variables</h4>
            <div className="grid grid-cols-2 gap-1">
              {BASIC_VARIABLES.map((variable) => (
                <Button
                  key={variable.name}
                  variant="ghost"
                  size="sm"
                  onClick={() => onInsert(variable.name)}
                  className="justify-start font-mono text-xs h-auto py-2 px-2"
                  type="button"
                  title={variable.description}
                >
                  <span className="truncate">{`{{${variable.name}}}`}</span>
                </Button>
              ))}
            </div>
          </div>

          {/* Extended Variables */}
          <div>
            <h4 className="font-medium text-sm mb-2">Extended Variables</h4>
            <div className="grid grid-cols-2 gap-1">
              {EXTENDED_VARIABLES.map((variable) => (
                <Button
                  key={variable.name}
                  variant="ghost"
                  size="sm"
                  onClick={() => onInsert(variable.name)}
                  className="justify-start font-mono text-xs h-auto py-2 px-2"
                  type="button"
                  title={variable.description}
                >
                  <span className="truncate">{`{{${variable.name}}}`}</span>
                </Button>
              ))}
            </div>
          </div>

          {/* Custom Variables */}
          {hasCustomVars && (
            <div>
              <h4 className="font-medium text-sm mb-2">Custom Variables</h4>
              <div className="grid grid-cols-2 gap-1">
                {Object.entries(customVariables).map(([key, value]) => (
                  <Button
                    key={key}
                    variant="ghost"
                    size="sm"
                    onClick={() => onInsert(key)}
                    className="justify-start font-mono text-xs h-auto py-2 px-2"
                    type="button"
                    title={`Value: ${value}`}
                  >
                    <span className="truncate">{`{{${key}}}`}</span>
                  </Button>
                ))}
              </div>
            </div>
          )}

          {!hasCustomVars && (
            <div className="text-xs text-muted-foreground">
              Add custom variables below to use them here
            </div>
          )}
        </div>
      </PopoverContent>
    </Popover>
  );
}
