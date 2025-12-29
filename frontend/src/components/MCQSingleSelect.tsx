/**
 * MCQSingleSelect Component
 *
 * Radio button interface for selecting a single option from multiple choices.
 * Used for MCQ_SINGLE step type in Game Master architecture.
 */

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { Card } from '@/components/ui/card';

interface MCQSingleSelectProps {
  options: string[];
  onSubmit: (selectedIndex: number) => void;
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

  const handleSubmit = () => {
    if (selectedIndex !== null) {
      onSubmit(selectedIndex);
    }
  };

  return (
    <Card className="p-6">
      <RadioGroup
        value={selectedIndex?.toString()}
        onValueChange={(value) => setSelectedIndex(parseInt(value))}
        disabled={disabled || isSubmitting}
      >
        <div className="space-y-3">
          {options.map((option, index) => (
            <div key={index} className="flex items-center space-x-3 p-3 rounded-lg hover:bg-accent transition-colors">
              <RadioGroupItem value={index.toString()} id={`option-${index}`} />
              <Label
                htmlFor={`option-${index}`}
                className="flex-1 cursor-pointer text-base"
              >
                {option}
              </Label>
            </div>
          ))}
        </div>
      </RadioGroup>

      <div className="mt-6">
        <Button
          onClick={handleSubmit}
          disabled={selectedIndex === null || disabled || isSubmitting}
          className="w-full"
        >
          {isSubmitting ? 'Submitting...' : 'Submit Answer'}
        </Button>
      </div>
    </Card>
  );
}
