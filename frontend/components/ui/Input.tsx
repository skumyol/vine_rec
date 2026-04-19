import { forwardRef, InputHTMLAttributes, SelectHTMLAttributes } from 'react';
import { cn } from '@/lib/cn';

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        'flex h-9 w-full rounded-lg bg-surface px-3 py-1 text-sm shadow-subtle',
        'ring-1 ring-border placeholder:text-fg-subtle',
        'transition-colors',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
        'disabled:cursor-not-allowed disabled:opacity-50',
        className
      )}
      {...props}
    />
  )
);
Input.displayName = 'Input';

export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(
  ({ className, children, ...props }, ref) => (
    <select
      ref={ref}
      className={cn(
        'flex h-9 w-full rounded-lg bg-surface px-3 py-1 text-sm shadow-subtle',
        'ring-1 ring-border text-fg cursor-pointer',
        'transition-colors',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
        'disabled:cursor-not-allowed disabled:opacity-50',
        className
      )}
      {...props}
    >
      {children}
    </select>
  )
);
Select.displayName = 'Select';

export function Label({ className, ...props }: React.LabelHTMLAttributes<HTMLLabelElement>) {
  return (
    <label
      className={cn('text-xs font-medium text-fg-muted block mb-1.5', className)}
      {...props}
    />
  );
}
