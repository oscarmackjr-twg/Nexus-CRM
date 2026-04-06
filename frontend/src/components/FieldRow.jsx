export function FieldRow({ label, value }) {
  const isEmpty =
    value === null ||
    value === undefined ||
    (typeof value === 'string' && value.trim() === '') ||
    (Array.isArray(value) && value.length === 0);

  return (
    <div className="grid grid-cols-[140px_1fr] gap-2 items-start">
      <span className="text-xs uppercase tracking-wide text-muted-foreground">
        {label}
      </span>
      <span className="text-sm">
        {isEmpty ? '\u2014' : value}
      </span>
    </div>
  );
}
