import { Download } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { downloadCsv } from '@/lib/exportCsv';

export function ExportCurrentViewButton({ resource, columns, rows = [], filters = {} }) {
  const activeFilters = Object.entries(filters).filter(([, value]) => value).map(([key]) => key).join('-');
  const exportRows = () => downloadCsv(`${resource}${activeFilters ? `-${activeFilters}` : ''}-${new Date().toISOString().slice(0, 10)}.csv`, columns, rows);
  return <Button variant="outline" size="sm" disabled={!rows.length} onClick={exportRows}><Download className="h-4 w-4" />Export CSV</Button>;
}
