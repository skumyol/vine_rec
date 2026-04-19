import { ReactNode } from 'react';
import { cn } from '@/lib/cn';

export function PageHeader({
  title,
  description,
  actions,
  eyebrow,
  className,
}: {
  title: string;
  description?: string;
  actions?: ReactNode;
  eyebrow?: string;
  className?: string;
}) {
  return (
    <header className={cn('mb-8', className)}>
      {eyebrow && (
        <div className="text-[11px] font-semibold uppercase tracking-[0.14em] text-primary mb-2">
          {eyebrow}
        </div>
      )}
      <div className="flex items-start justify-between gap-6 flex-wrap">
        <div className="space-y-1.5 min-w-0">
          <h1 className="text-3xl font-semibold tracking-tight text-fg text-balance">
            {title}
          </h1>
          {description && (
            <p className="text-fg-muted text-pretty max-w-2xl">{description}</p>
          )}
        </div>
        {actions && <div className="flex items-center gap-2 shrink-0">{actions}</div>}
      </div>
    </header>
  );
}
