import { cn } from '@/lib/utils';
import { Select } from '@/components/ui/select';
import { useRefData } from '@/hooks/useRefData';

export function RefSelect({ category, value, onChange, placeholder, disabled = false, className }) {
  const { data: items = [], isLoading, isError } = useRefData(category);

  if (isLoading) {
    return (
      <div className="opacity-50">
        <Select disabled className={className}>
          <option value="">Loading...</option>
        </Select>
      </div>
    );
  }

  if (isError) {
    return (
      <Select disabled className={cn('border-danger', className)}>
        <option value="">Failed to load</option>
      </Select>
    );
  }

  return (
    <Select
      value={value ?? ''}
      onChange={(e) => onChange(e.target.value)}
      disabled={disabled}
      className={className}
    >
      {placeholder && (
        <option value="" disabled>
          {placeholder}
        </option>
      )}
      {items.length === 0 ? (
        <option value="" disabled>
          No options available
        </option>
      ) : (
        items.map((item) => (
          <option key={item.id} value={item.id}>
            {item.label}
          </option>
        ))
      )}
    </Select>
  );
}
