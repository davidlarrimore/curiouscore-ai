/**
 * MCQMultiSelect Component
 *
 * Checkbox interface for selecting multiple options.
 * Used for MCQ_MULTI step type in Game Master architecture.
 */

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Card } from '@/components/ui/card';

interface MCQMultiSelectProps {
  options: string[];
  onSubmit: (selectedIndices: number[]) => void;
  disabled?: boolean;
  isSubmitting?: boolean;
}

export function MCQMultiSelect({
  options,
  onSubmit,
  disabled = false,
  isSubmitting = false
}: MCQMultiSelectProps) {
  const [selectedIndices, setSelectedIndices] = useState<Set<number>>(new Set());

  const toggleOption = (index: number) => {
    const newSelected = new Set(selectedIndices);
    if (newSelected.has(index)) {
      newSelected.delete(index);
    } else {
      newSelected.add(index);
    }
    setSelectedIndices(newSelected);
  };

  const handleSubmit = () => {
    const indices = Array.from(selectedIndices).sort((a, b) => a - b);
    onSubmit(indices);
  };

  return (
    <Card className="p-6">
      <div className="space-y-3">
        {options.map((option, index) => (
          <div
            key={index}
            className="flex items-center space-x-3 p-3 rounded-lg hover:bg-accent transition-colors"
          >
            <Checkbox
              id={`option-${index}`}
              checked={selectedIndices.has(index)}
              onCheckedChange={() => toggleOption(index)}
              disabled={disabled || isSubmitting}
            />
            <Label
              htmlFor={`option-${index}`}
              className="flex-1 cursor-pointer text-base"
            >
              {option}
            </Label>
          </div>
        ))}
      </div>

      <div className="mt-6 space-y-2">
        <p className="text-sm text-muted-foreground">
          {selectedIndices.size === 0
            ? 'Select one or more options'
            : `${selectedIndices.size} option${selectedIndices.size === 1 ? '' : 's'} selected`}
        </p>
        <Button
          onClick={handleSubmit}
          disabled={selectedIndices.size === 0 || disabled || isSubmitting}
          className="w-full"
        >
          {isSubmitting ? 'Submitting...' : 'Submit Answer'}
        </Button>
      </div>
    </Card>
  );
}
