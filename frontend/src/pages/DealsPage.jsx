import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { getDeals } from '@/api/deals';
import { getPipelines } from '@/api/pipelines';
import { getUsers } from '@/api/users';
import { DataGrid } from '@/components/DataGrid';
import { Badge } from '@/components/ui/badge';
import { formatCurrency, formatDate } from '@/lib/utils';
import { CoreRecordCreateDialog } from '@/components/CoreRecordCreateDialog';
import { ListSearch } from '@/components/ListSearch';
import { useDebouncedValue } from '@/hooks/useDebouncedValue';
import { ExportCurrentViewButton } from '@/components/ExportCurrentViewButton';
import { ListFilters } from '@/components/ListFilters';

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
  const [search, setSearch] = useState('');
  const [filters, setFilters] = useState({});
  const debouncedSearch = useDebouncedValue(search);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['deals', { page, size, status, search: debouncedSearch, ...filters }],
    queryFn: () => getDeals({ page, size, ...filters, ...(status && { status }), ...(debouncedSearch && { search: debouncedSearch }) }),
    placeholderData: keepPreviousData,
  });
  const pipelinesQuery = useQuery({ queryKey: ['pipelines'], queryFn: getPipelines });
  const usersQuery = useQuery({ queryKey: ['users', 'filter-options'], queryFn: () => getUsers({ page: 1, size: 100 }) });

  const handleStatusChange = (newStatus) => {
    setStatus(newStatus);
    setPage(1);
  };
  const handleSearchChange = (value) => { setSearch(value); setPage(1); };
  const handleFilterChange = (key, value) => { setFilters((current) => ({ ...current, [key]: value || undefined, ...(key === 'pipeline_id' ? { stage_id: undefined } : {}) })); setPage(1); };
  const selectedPipeline = (pipelinesQuery.data || []).find((pipeline) => pipeline.id === filters.pipeline_id);

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
      <div className="flex items-center justify-between"><h1 className="text-xl font-semibold">Deals</h1><div className="flex gap-2"><ExportCurrentViewButton resource="deals" filters={{ ...filters, ...(status && { status }) }} rows={data?.items} columns={[{ label: 'Deal', value: (row) => row.name }, { label: 'Company', value: (row) => row.company_name }, { label: 'Stage', value: (row) => row.stage_name }, { label: 'Status', value: (row) => row.status }, { label: 'Owner', value: (row) => row.owner_name }]} /><CoreRecordCreateDialog entity="deal" navigate={navigate} /></div></div>

      <div className="flex flex-wrap gap-2"><ListSearch value={search} onChange={handleSearchChange} placeholder="Search deals" /><ListFilters filters={filters} onChange={handleFilterChange} definitions={[{ key: 'pipeline_id', label: 'Pipeline', options: (pipelinesQuery.data || []).map((row) => ({ id: row.id, label: row.name })) }, { key: 'stage_id', label: 'Stage', options: (selectedPipeline?.stages || []).map((row) => ({ id: row.id, label: row.name })) }, { key: 'owner_id', label: 'Owner', options: (usersQuery.data?.items || []).map((row) => ({ id: row.id, label: row.full_name || row.email })) }]} /></div>

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
        isError={isError}
        onRetry={refetch}
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
