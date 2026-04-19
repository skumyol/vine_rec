import { HTMLAttributes } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/cn';

const badgeVariants = cva(
  'inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset',
  {
    variants: {
      variant: {
        default: 'bg-bg-muted text-fg ring-border',
        primary: 'bg-primary-soft text-primary ring-primary/20',
        success: 'bg-success-soft text-success ring-success/20',
        warning: 'bg-warning-soft text-warning ring-warning/20',
        danger: 'bg-danger-soft text-danger ring-danger/20',
        info: 'bg-info-soft text-info ring-info/20',
        outline: 'bg-transparent text-fg-muted ring-border',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
);

export interface BadgeProps
  extends HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant, className }))} {...props} />;
}

export function VerdictBadge({ verdict }: { verdict: string }) {
  const map: Record<string, { variant: BadgeProps['variant']; label: string; dot: string }> = {
    PASS: { variant: 'success', label: 'PASS', dot: 'bg-success' },
    REVIEW: { variant: 'warning', label: 'REVIEW', dot: 'bg-warning' },
    FAIL: { variant: 'danger', label: 'FAIL', dot: 'bg-danger' },
    NO_IMAGE: { variant: 'default', label: 'NO IMAGE', dot: 'bg-fg-subtle' },
  };
  const config = map[verdict] || map.NO_IMAGE;
  return (
    <Badge variant={config.variant}>
      <span className={cn('h-1.5 w-1.5 rounded-full', config.dot)} />
      {config.label}
    </Badge>
  );
}
