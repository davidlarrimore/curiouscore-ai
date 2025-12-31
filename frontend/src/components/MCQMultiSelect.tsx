/**
 * MCQMultiSelect Component
 *
 * Checkbox interface for selecting multiple options.
 * Used for MCQ_MULTI step type in Game Master architecture.
 */

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Card } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface MCQMultiSelectProps {
  options: string[];
  onSubmit: (selectedIndices: number[], selectedTexts: string[]) => void;
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
  const isDisabled = disabled || isSubmitting;

  // Reset selection when options change (new question)
  useEffect(() => {
    setSelectedIndices(new Set());
  }, [options]);

  const toggleOption = (index: number) => {
    if (isDisabled) return;
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
    const texts = indices.map(i => options[i]);
    onSubmit(indices, texts);
  };

  return (
    <Card className="p-4 md:p-5">
      <div className="grid gap-2 md:grid-cols-2">
        {options.map((option, index) => {
          const isActive = selectedIndices.has(index);
          const optionId = `option-${index}`;

          return (
            <div
              key={index}
              role="button"
              tabIndex={isDisabled ? -1 : 0}
              aria-disabled={isDisabled}
              onClick={() => toggleOption(index)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  toggleOption(index);
                }
              }}
              className={cn(
                'flex items-start gap-3 rounded-lg border border-border/70 bg-card/80 p-2.5 text-sm leading-snug transition-colors',
                'hover:border-primary/60 hover:bg-primary/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/60',
                isActive && 'border-primary bg-primary/10 shadow-sm',
                isDisabled ? 'cursor-not-allowed opacity-60' : 'cursor-pointer'
              )}
            >
              <Checkbox
                id={optionId}
                checked={isActive}
                onCheckedChange={() => toggleOption(index)}
                disabled={isDisabled}
                className="mt-0.5 h-4 w-4"
              />
              <Label
                htmlFor={optionId}
                className="flex-1 cursor-pointer text-sm leading-snug text-foreground"
              >
                <span className="block whitespace-pre-line">{option}</span>
              </Label>
            </div>
          );
        })}
      </div>

      <div className="mt-3 flex items-center justify-between gap-3">
        <p className="text-xs text-muted-foreground">
          {selectedIndices.size === 0
            ? 'Select one or more options'
            : `${selectedIndices.size} option${selectedIndices.size === 1 ? '' : 's'} selected`}
        </p>
        <Button
          onClick={handleSubmit}
          disabled={selectedIndices.size === 0 || isDisabled}
          size="sm"
        >
          {isSubmitting ? 'Submitting...' : 'Submit Answer'}
        </Button>
      </div>
    </Card>
  );
}
