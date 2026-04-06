import { cn } from '@/lib/utils';

export function LinkedInPanel({ entityType, entityId, className }) {
  return (
    <div className={cn('rounded-lg border bg-card p-4 text-sm text-muted-foreground', className)}>
      LinkedIn integration not configured.
    </div>
  );
}

export default LinkedInPanel;
