/**
 * MCQSingleSelect Component
 *
 * Radio button interface for selecting a single option from multiple choices.
 * Used for MCQ_SINGLE step type in Game Master architecture.
 */

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { Card } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface MCQSingleSelectProps {
  options: string[];
  onSubmit: (selectedIndex: number, selectedText: string) => void;
  disabled?: boolean;
  isSubmitting?: boolean;
}

export function MCQSingleSelect({
  options,
  onSubmit,
  disabled = false,
  isSubmitting = false
}: MCQSingleSelectProps) {
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const isDisabled = disabled || isSubmitting;

  // Reset selection when options change (new question)
  useEffect(() => {
    setSelectedIndex(null);
  }, [options]);

  const handleSubmit = () => {
    if (selectedIndex !== null) {
      onSubmit(selectedIndex, options[selectedIndex]);
    }
  };

  return (
    <Card className="p-4 md:p-5">
      <RadioGroup
        value={selectedIndex?.toString()}
        onValueChange={(value) => setSelectedIndex(parseInt(value))}
        disabled={isDisabled}
        className="grid gap-2 md:grid-cols-2"
      >
        {options.map((option, index) => {
          const isActive = selectedIndex === index;
          const optionId = `option-${index}`;

          return (
            <div
              key={index}
              role="button"
              tabIndex={isDisabled ? -1 : 0}
              aria-disabled={isDisabled}
              onClick={() => !isDisabled && setSelectedIndex(index)}
              onKeyDown={(e) => {
                if (!isDisabled && (e.key === 'Enter' || e.key === ' ')) {
                  e.preventDefault();
                  setSelectedIndex(index);
                }
              }}
              className={cn(
                'flex items-start gap-3 rounded-lg border border-border/70 bg-card/80 p-2.5 text-sm leading-snug transition-colors',
                'hover:border-primary/60 hover:bg-primary/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/60',
                isActive && 'border-primary bg-primary/10 shadow-sm',
                isDisabled ? 'cursor-not-allowed opacity-60' : 'cursor-pointer'
              )}
            >
              <RadioGroupItem value={index.toString()} id={optionId} className="mt-0.5 h-4 w-4" />
              <Label
                htmlFor={optionId}
                className="flex-1 cursor-pointer text-sm leading-snug text-foreground"
              >
                <span className="block whitespace-pre-line">{option}</span>
              </Label>
            </div>
          );
        })}
      </RadioGroup>

      <div className="mt-3 flex items-center justify-between gap-3">
        <p className="text-xs text-muted-foreground">Select one option</p>
        <Button
          onClick={handleSubmit}
          disabled={selectedIndex === null || isDisabled}
          size="sm"
        >
          {isSubmitting ? 'Submitting...' : 'Submit Answer'}
        </Button>
      </div>
    </Card>
  );
}
