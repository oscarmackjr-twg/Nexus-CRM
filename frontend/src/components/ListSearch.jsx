import { Search, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

export function ListSearch({ value, onChange, placeholder }) {
  return <div className="relative max-w-md">
    <Search aria-hidden="true" className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
    <Input aria-label="Search records" className="pl-9 pr-9" value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} />
    {value ? <Button type="button" variant="ghost" size="icon" aria-label="Clear search" className="absolute right-0 top-0 h-9 w-9" onClick={() => onChange('')}><X className="h-4 w-4" /></Button> : null}
  </div>;
}
