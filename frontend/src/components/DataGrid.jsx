import { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { ChevronUp, ChevronDown, ChevronsUpDown } from 'lucide-react';
import {
  Table,
  TableHeader,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Pagination } from '@/components/Pagination';
import { cn } from '@/lib/utils';

export function DataGrid({
  columns,
  data,
  total,
  page,
  pages,
  size,
  isLoading,
  onPageChange,
  onSizeChange,
  onRowClick,
  sortKey,
  sortDir,
  onSort,
  emptyHeading,
  emptyBody,
  className,
}) {
  const sortedData = useMemo(() => {
    if (!sortKey || !data) return data || [];
    return [...data].sort((a, b) => {
      const av = a[sortKey] ?? '';
      const bv = b[sortKey] ?? '';
      const cmp = av < bv ? -1 : av > bv ? 1 : 0;
      return sortDir === 'asc' ? cmp : -cmp;
    });
  }, [data, sortKey, sortDir]);

  function handleSort(col) {
    if (col.sortable === false) return;
    if (sortKey !== col.key) {
      onSort?.(col.key, 'asc');
    } else if (sortDir === 'asc') {
      onSort?.(col.key, 'desc');
    } else {
      onSort?.(null, 'asc');
    }
  }

  function SortIndicator({ col }) {
    if (col.sortable === false) return null;
    if (col.key !== sortKey) {
      return <ChevronsUpDown className="h-3 w-3 text-gray-400 ml-1 inline-block" />;
    }
    if (sortDir === 'asc') {
      return <ChevronUp className="h-3 w-3 text-[#1a3868] ml-1 inline-block" />;
    }
    return <ChevronDown className="h-3 w-3 text-[#1a3868] ml-1 inline-block" />;
  }

  return (
    <div className={cn('rounded-lg border overflow-hidden', className)}>
      <Table>
        <TableHeader>
          <TableRow>
            {columns.map((col) => (
              <TableHead
                key={col.key}
                className={cn(
                  'py-2 px-4 text-xs font-semibold uppercase tracking-wide text-gray-500 border-b border-gray-200',
                  col.sortable !== false && 'cursor-pointer select-none'
                )}
                onClick={() => handleSort(col)}
              >
                {col.label}
                <SortIndicator col={col} />
              </TableHead>
            ))}
            <TableHead className="py-2 px-4 text-xs font-semibold uppercase tracking-wide text-gray-500 border-b border-gray-200" />
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading ? (
            Array.from({ length: 10 }).map((_, i) => (
              <TableRow key={i}>
                {Array.from({ length: columns.length + 1 }).map((_, j) => (
                  <TableCell key={j} className="py-2 px-4">
                    <Skeleton className="h-4 w-full" />
                  </TableCell>
                ))}
              </TableRow>
            ))
          ) : !data || data.length === 0 ? (
            <TableRow>
              <TableCell colSpan={columns.length + 1} className="py-12 text-center">
                <div className="text-center py-12 text-gray-400">
                  <p className="text-sm font-semibold text-gray-500 mb-1">
                    {emptyHeading || 'No data'}
                  </p>
                  <p className="text-xs text-gray-400">{emptyBody || ''}</p>
                </div>
              </TableCell>
            </TableRow>
          ) : (
            sortedData.map((row) => (
              <TableRow
                key={row.id}
                className="group hover:bg-gray-50 cursor-pointer border-b border-gray-100"
                onClick={() => onRowClick?.(row)}
              >
                {columns.map((col) => (
                  <TableCell key={col.key} className="py-2 px-4 text-sm text-gray-900">
                    {col.render ? col.render(row) : (row[col.key] ?? '\u2014')}
                  </TableCell>
                ))}
                <TableCell className="py-2 px-4 text-sm">
                  <div className="invisible group-hover:visible flex items-center gap-1">
                    {onRowClick && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          onRowClick(row);
                        }}
                      >
                        View
                      </Button>
                    )}
                  </div>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
      <Pagination
        page={page}
        pages={pages}
        total={total}
        size={size}
        onPageChange={onPageChange}
        onSizeChange={onSizeChange}
      />
    </div>
  );
}
