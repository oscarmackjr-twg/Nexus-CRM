import { Button } from '@/components/ui/button';

export function Pagination({ page, pages, total, size, onPageChange, onSizeChange }) {
  return (
    <div className="flex items-center justify-between px-4 py-2 border-t border-gray-200 text-sm text-gray-600 bg-white">
      <span className="text-sm text-gray-500">
        {total} records · Page {page} of {pages}
      </span>
      <div className="flex items-center gap-3">
        <select
          value={size}
          onChange={(e) => {
            onSizeChange(Number(e.target.value));
            onPageChange(1);
          }}
          className="text-sm border border-gray-200 rounded px-2 py-1 text-gray-700 focus:outline-none focus:ring-1 focus:ring-[#1a3868]"
        >
          {[10, 25, 50, 100].map((n) => (
            <option key={n} value={n}>
              {n} per page
            </option>
          ))}
        </select>
        <Button
          variant="outline"
          size="sm"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          Previous
        </Button>
        <Button
          variant="outline"
          size="sm"
          disabled={page >= pages}
          onClick={() => onPageChange(page + 1)}
        >
          Next
        </Button>
      </div>
    </div>
  );
}
