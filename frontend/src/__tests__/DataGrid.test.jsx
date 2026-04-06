import { screen } from '@testing-library/react';
import { DataGrid } from '@/components/DataGrid';
import { renderWithProviders } from './test-utils';

const columns = [
  { key: 'name', label: 'NAME' },
  { key: 'email', label: 'EMAIL' },
];

const mockData = [
  { id: '1', name: 'Alice', email: 'alice@test.com' },
  { id: '2', name: 'Bob', email: 'bob@test.com' },
];

const defaultProps = {
  columns,
  data: mockData,
  total: 2,
  page: 1,
  pages: 1,
  size: 25,
  isLoading: false,
  onPageChange: vi.fn(),
  onSizeChange: vi.fn(),
  sortKey: null,
  sortDir: 'asc',
  onSort: vi.fn(),
};

describe('DataGrid', () => {
  it('renders column headers with uppercase text (GRID-04)', () => {
    renderWithProviders(<DataGrid {...defaultProps} />);
    expect(screen.getByText('NAME')).toBeInTheDocument();
    expect(screen.getByText('EMAIL')).toBeInTheDocument();
  });

  it('renders data rows', () => {
    renderWithProviders(<DataGrid {...defaultProps} />);
    expect(screen.getByText('Alice')).toBeInTheDocument();
    expect(screen.getByText('bob@test.com')).toBeInTheDocument();
  });

  it('renders em dash for null values', () => {
    const data = [{ id: '1', name: 'Alice', email: null }];
    renderWithProviders(<DataGrid {...defaultProps} data={data} total={1} />);
    expect(screen.getByText('\u2014')).toBeInTheDocument();
  });

  it('renders View button text per row (GRID-05)', () => {
    renderWithProviders(<DataGrid {...defaultProps} onRowClick={vi.fn()} />);
    const viewButtons = screen.getAllByText('View');
    expect(viewButtons).toHaveLength(2);
  });

  it('renders Pagination bar (GRID-06)', () => {
    renderWithProviders(<DataGrid {...defaultProps} />);
    expect(screen.getByText(/2 records/)).toBeInTheDocument();
    expect(screen.getByText('Previous')).toBeInTheDocument();
    expect(screen.getByText('Next')).toBeInTheDocument();
  });

  it('renders skeleton rows when isLoading is true', () => {
    renderWithProviders(<DataGrid {...defaultProps} isLoading={true} data={[]} />);
    expect(screen.queryByText('Alice')).not.toBeInTheDocument();
  });

  it('renders empty state when data is empty and not loading', () => {
    renderWithProviders(
      <DataGrid {...defaultProps} data={[]} total={0} emptyHeading="No contacts yet" emptyBody="Contacts you add will appear here." />
    );
    expect(screen.getByText('No contacts yet')).toBeInTheDocument();
    expect(screen.getByText('Contacts you add will appear here.')).toBeInTheDocument();
  });
});
