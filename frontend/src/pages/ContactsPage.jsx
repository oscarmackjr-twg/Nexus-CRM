import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getContacts } from '@/api/contacts';
import { getCompanies } from '@/api/companies';
import { getUsers } from '@/api/users';
import { DataGrid } from '@/components/DataGrid';
import { Badge } from '@/components/ui/badge';
import { formatDate } from '@/lib/utils';
import { CoreRecordCreateDialog } from '@/components/CoreRecordCreateDialog';
import { ListSearch } from '@/components/ListSearch';
import { useDebouncedValue } from '@/hooks/useDebouncedValue';
import { ExportCurrentViewButton } from '@/components/ExportCurrentViewButton';
import { ListFilters } from '@/components/ListFilters';

export default function ContactsPage() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [size, setSize] = useState(25);
  const [sortKey, setSortKey] = useState(null);
  const [sortDir, setSortDir] = useState('asc');
  const [search, setSearch] = useState('');
  const [filters, setFilters] = useState({});
  const debouncedSearch = useDebouncedValue(search);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['contacts', { page, size, search: debouncedSearch, ...filters }],
    queryFn: () => getContacts({ page, size, ...filters, ...(debouncedSearch && { search: debouncedSearch }) }),
    placeholderData: (prev) => prev,
  });
  const companiesQuery = useQuery({ queryKey: ['companies', 'filter-options'], queryFn: () => getCompanies({ page: 1, size: 100 }) });
  const usersQuery = useQuery({ queryKey: ['users', 'filter-options'], queryFn: () => getUsers({ page: 1, size: 100 }) });

  const columns = [
    {
      key: 'name',
      label: 'NAME',
      render: (row) => (
        <Link
          to={`/contacts/${row.id}`}
          className="font-medium text-[#1a3868] hover:underline"
          onClick={(e) => e.stopPropagation()}
        >
          {row.first_name} {row.last_name}
        </Link>
      ),
    },
    { key: 'company_name', label: 'COMPANY' },
    { key: 'title', label: 'TITLE' },
    {
      key: 'lifecycle_stage',
      label: 'STAGE',
      render: (row) =>
        row.lifecycle_stage ? (
          <Badge variant="secondary">{row.lifecycle_stage}</Badge>
        ) : (
          '\u2014'
        ),
    },
    { key: 'email', label: 'EMAIL' },
    { key: 'lead_score', label: 'SCORE' },
    { key: 'owner_name', label: 'OWNER' },
    {
      key: 'updated_at',
      label: 'UPDATED',
      render: (row) => formatDate(row.updated_at),
    },
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
      <div className="flex items-center justify-between"><h1 className="text-xl font-semibold">Contacts</h1><div className="flex gap-2"><ExportCurrentViewButton resource="contacts" filters={filters} rows={data?.items} columns={[{ label: 'Name', value: (row) => `${row.first_name} ${row.last_name}` }, { label: 'Company', value: (row) => row.company_name }, { label: 'Email', value: (row) => row.email }, { label: 'Stage', value: (row) => row.lifecycle_stage }, { label: 'Owner', value: (row) => row.owner_name }]} /><CoreRecordCreateDialog entity="contact" navigate={navigate} /></div></div>
      <div className="flex flex-wrap gap-2"><ListSearch value={search} onChange={handleSearchChange} placeholder="Search contacts" /><ListFilters filters={filters} onChange={handleFilterChange} definitions={[{ key: 'lifecycle_stage', label: 'Stage', options: ['lead', 'customer'].map((id) => ({ id, label: id })) }, { key: 'company_id', label: 'Company', options: (companiesQuery.data?.items || []).map((row) => ({ id: row.id, label: row.name })) }, { key: 'owner_id', label: 'Owner', options: (usersQuery.data?.items || []).map((row) => ({ id: row.id, label: row.full_name || row.email })) }]} /></div>
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
        onRowClick={(row) => navigate(`/contacts/${row.id}`)}
        sortKey={sortKey}
        sortDir={sortDir}
        onSort={handleSort}
        emptyHeading="No contacts yet"
        emptyBody="Contacts you add will appear here."
      />
    </div>
  );
}
