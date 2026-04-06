import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { getDeals } from '@/api/deals';
import { DataGrid } from '@/components/DataGrid';
import { Badge } from '@/components/ui/badge';
import { formatCurrency, formatDate } from '@/lib/utils';

const STATUS_TABS = [
  { label: 'All', value: null },
  { label: 'Open', value: 'open' },
  { label: 'Won', value: 'won' },
  { label: 'Lost', value: 'lost' },
];

const STATUS_BADGE = {
  open: 'bg-blue-100 text-blue-800',
  won: 'bg-green-100 text-green-800',
  lost: 'bg-gray-100 text-gray-600',
};

export default function DealsPage() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [size, setSize] = useState(25);
  const [status, setStatus] = useState(null);
  const [sortKey, setSortKey] = useState(null);
  const [sortDir, setSortDir] = useState('asc');

  const { data, isLoading } = useQuery({
    queryKey: ['deals', { page, size, status }],
    queryFn: () => getDeals({ page, size, ...(status && { status }) }),
    placeholderData: keepPreviousData,
  });

  const handleStatusChange = (newStatus) => {
    setStatus(newStatus);
    setPage(1);
  };

  const handleSort = (key, dir) => {
    setSortKey(key);
    setSortDir(dir);
  };

  const handleSizeChange = (newSize) => {
    setSize(newSize);
    setPage(1);
  };

  const columns = [
    {
      key: 'name',
      label: 'DEAL',
      render: (row) => (
        <Link
          to={`/deals/${row.id}`}
          className="font-medium text-[#1a3868] hover:underline"
          onClick={(e) => e.stopPropagation()}
        >
          {row.name}
        </Link>
      ),
    },
    { key: 'company_name', label: 'COMPANY' },
    { key: 'stage_name', label: 'STAGE' },
    {
      key: 'value',
      label: 'VALUE',
      render: (row) => formatCurrency(row.value, row.currency),
    },
    {
      key: 'status',
      label: 'STATUS',
      render: (row) => (
        <Badge
          className={STATUS_BADGE[row.status] || 'bg-gray-100 text-gray-600'}
          variant="outline"
        >
          {row.status}
        </Badge>
      ),
    },
    {
      key: 'expected_close_date',
      label: 'CLOSE DATE',
      render: (row) => formatDate(row.expected_close_date),
    },
    { key: 'owner_name', label: 'OWNER' },
    { key: 'days_in_stage', label: 'DAYS' },
  ];

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Deals</h1>

      {/* Status filter tabs per D-04 */}
      <div className="flex gap-1 mb-4">
        {STATUS_TABS.map((tab) => (
          <button
            key={tab.label}
            onClick={() => handleStatusChange(tab.value)}
            className={
              status === tab.value
                ? 'px-3 py-2 text-sm rounded-md font-semibold text-[#1a3868] bg-white border border-gray-200 shadow-sm'
                : 'px-3 py-2 text-sm rounded-md text-gray-500 hover:text-gray-700 hover:bg-gray-100 transition-colors'
            }
          >
            {tab.label}
          </button>
        ))}
      </div>

      <DataGrid
        columns={columns}
        data={data?.items}
        total={data?.total ?? 0}
        page={data?.page ?? page}
        pages={data?.pages ?? 1}
        size={size}
        isLoading={isLoading}
        onPageChange={setPage}
        onSizeChange={handleSizeChange}
        onRowClick={(row) => navigate(`/deals/${row.id}`)}
        sortKey={sortKey}
        sortDir={sortDir}
        onSort={handleSort}
        emptyHeading="No deals found"
        emptyBody={status ? `No ${status} deals match your filter.` : 'Deals you create will appear here.'}
      />
    </div>
  );
}
