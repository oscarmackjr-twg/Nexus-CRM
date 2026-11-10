import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getCompanies } from '@/api/companies';
import { getUsers } from '@/api/users';
import { DataGrid } from '@/components/DataGrid';
import { CoreRecordCreateDialog } from '@/components/CoreRecordCreateDialog';
import { ListSearch } from '@/components/ListSearch';
import { useDebouncedValue } from '@/hooks/useDebouncedValue';
import { ExportCurrentViewButton } from '@/components/ExportCurrentViewButton';
import { ListFilters } from '@/components/ListFilters';

export default function CompaniesPage() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [size, setSize] = useState(25);
  const [sortKey, setSortKey] = useState(null);
  const [sortDir, setSortDir] = useState('asc');
  const [search, setSearch] = useState('');
  const [filters, setFilters] = useState({});
  const debouncedSearch = useDebouncedValue(search);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['companies', { page, size, search: debouncedSearch, ...filters }],
    queryFn: () => getCompanies({ page, size, ...filters, ...(debouncedSearch && { search: debouncedSearch }) }),
    placeholderData: (prev) => prev,
  });
  const usersQuery = useQuery({ queryKey: ['users', 'filter-options'], queryFn: () => getUsers({ page: 1, size: 100 }) });

  const columns = [
    {
      key: 'name',
      label: 'NAME',
      render: (row) => (
        <Link
          to={`/companies/${row.id}`}
          className="font-medium text-[#1a3868] hover:underline"
          onClick={(e) => e.stopPropagation()}
        >
          {row.name}
        </Link>
      ),
    },
    { key: 'company_type_label', label: 'TYPE' },
    { key: 'tier_label', label: 'TIER' },
    { key: 'sector_label', label: 'SECTOR' },
    { key: 'industry', label: 'INDUSTRY' },
    {
      key: 'linked_contacts_count',
      label: 'CONTACTS',
      render: (row) => row.linked_contacts_count ?? 0,
    },
    {
      key: 'open_deals_count',
      label: 'DEALS',
      render: (row) => row.open_deals_count ?? 0,
    },
    { key: 'owner_name', label: 'OWNER' },
  ];

  const handleSort = (key, dir) => {
    setSortKey(key);
    setSortDir(dir);
  };

  const handleSizeChange = (newSize) => {
    setSize(newSize);
    setPage(1);
  };
  const handleSearchChange = (value) => { setSearch(value); setPage(1); };
  const handleFilterChange = (key, value) => { setFilters((current) => ({ ...current, [key]: value || undefined })); setPage(1); };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between"><h1 className="text-xl font-semibold">Companies</h1><div className="flex gap-2"><ExportCurrentViewButton resource="companies" filters={filters} rows={data?.items} columns={[{ label: 'Name', value: (row) => row.name }, { label: 'Type', value: (row) => row.company_type_label }, { label: 'Sector', value: (row) => row.sector_label }, { label: 'Industry', value: (row) => row.industry }, { label: 'Owner', value: (row) => row.owner_name }]} /><CoreRecordCreateDialog entity="company" navigate={navigate} /></div></div>
      <div className="flex flex-wrap gap-2"><ListSearch value={search} onChange={handleSearchChange} placeholder="Search companies" /><ListFilters filters={filters} onChange={handleFilterChange} definitions={[{ key: 'industry', label: 'Industry', options: ['Technology', 'Healthcare', 'Financial Services'].map((id) => ({ id, label: id })) }, { key: 'size_range', label: 'Size', options: ['1-10', '11-50', '51-200', '201-500', '501+'].map((id) => ({ id, label: id })) }, { key: 'owner_id', label: 'Owner', options: (usersQuery.data?.items || []).map((row) => ({ id: row.id, label: row.full_name || row.email })) }]} /></div>
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
        onRowClick={(row) => navigate(`/companies/${row.id}`)}
        sortKey={sortKey}
        sortDir={sortDir}
        onSort={handleSort}
        emptyHeading="No companies yet"
        emptyBody="Companies you add will appear here."
      />
    </div>
  );
}
