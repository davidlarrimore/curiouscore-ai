/**
 * TrueFalseToggle Component
 *
 * Binary choice interface for True/False questions.
 * Used for TRUE_FALSE step type in Game Master architecture.
 */

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Check, X } from 'lucide-react';

interface TrueFalseToggleProps {
  onSubmit: (answerIndex: number, answerText: string) => void;  // 0 for True, 1 for False
  disabled?: boolean;
  isSubmitting?: boolean;
}

export function TrueFalseToggle({
  onSubmit,
  disabled = false,
  isSubmitting = false
}: TrueFalseToggleProps) {
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);

  const handleSubmit = () => {
    if (selectedIndex !== null) {
      const answerText = selectedIndex === 0 ? 'True' : 'False';
      onSubmit(selectedIndex, answerText);
    }
  };

  return (
    <Card className="p-6">
      <div className="grid grid-cols-2 gap-4 mb-6">
        {/* True Button */}
        <button
          onClick={() => setSelectedIndex(0)}
          disabled={disabled || isSubmitting}
          className={`
            p-6 rounded-lg border-2 transition-all duration-200 flex flex-col items-center gap-3
            ${selectedIndex === 0
              ? 'border-green-500 bg-green-500/10'
              : 'border-border hover:border-green-500/50 hover:bg-green-500/5'
            }
            ${disabled || isSubmitting ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
          `}
        >
          <Check className={`w-8 h-8 ${selectedIndex === 0 ? 'text-green-500' : 'text-muted-foreground'}`} />
          <span className={`text-lg font-semibold ${selectedIndex === 0 ? 'text-green-500' : 'text-foreground'}`}>
            True
          </span>
        </button>

        {/* False Button */}
        <button
          onClick={() => setSelectedIndex(1)}
          disabled={disabled || isSubmitting}
          className={`
            p-6 rounded-lg border-2 transition-all duration-200 flex flex-col items-center gap-3
            ${selectedIndex === 1
              ? 'border-red-500 bg-red-500/10'
              : 'border-border hover:border-red-500/50 hover:bg-red-500/5'
            }
            ${disabled || isSubmitting ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
          `}
        >
          <X className={`w-8 h-8 ${selectedIndex === 1 ? 'text-red-500' : 'text-muted-foreground'}`} />
          <span className={`text-lg font-semibold ${selectedIndex === 1 ? 'text-red-500' : 'text-foreground'}`}>
            False
          </span>
        </button>
      </div>

      <Button
        onClick={handleSubmit}
        disabled={selectedIndex === null || disabled || isSubmitting}
        className="w-full"
      >
        {isSubmitting ? 'Submitting...' : 'Submit Answer'}
      </Button>
    </Card>
  );
}
