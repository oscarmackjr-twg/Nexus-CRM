import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import CompaniesPage from '@/pages/CompaniesPage';
import { renderWithProviders } from './test-utils';
import { getCompanies } from '@/api/companies';
import { getUsers } from '@/api/users';

vi.mock('@/api/companies', () => ({
  createCompany: vi.fn(),
  getCompanies: vi.fn().mockResolvedValue({
    items: [
      {
        id: '1',
        name: 'Acme Corp',
        company_type_label: 'LP',
        tier_label: 'Tier 1',
        sector_label: 'Technology',
        industry: 'SaaS',
        linked_contacts_count: 5,
        open_deals_count: 2,
        owner_name: 'Admin',
      },
    ],
    total: 1,
    page: 1,
    size: 25,
    pages: 1,
  }),
}));
vi.mock('@/api/users', () => ({ getUsers: vi.fn().mockResolvedValue({ items: [{ id: 'owner-1', full_name: 'Ada Admin' }] }) }));

describe('CompaniesPage', () => {
  it('renders page heading', async () => {
    renderWithProviders(<CompaniesPage />, { route: '/companies', path: '/companies' });
    expect(await screen.findByText('Companies')).toBeInTheDocument();
  });

  it('renders company name in grid (GRID-02)', async () => {
    renderWithProviders(<CompaniesPage />, { route: '/companies', path: '/companies' });
    expect(await screen.findByText('Acme Corp')).toBeInTheDocument();
  });

  it('renders column headers (GRID-04)', async () => {
    renderWithProviders(<CompaniesPage />, { route: '/companies', path: '/companies' });
    await screen.findByText('Acme Corp');
    expect(screen.getByText('NAME')).toBeInTheDocument();
    expect(screen.getByText('TYPE')).toBeInTheDocument();
    expect(screen.getByText('SECTOR')).toBeInTheDocument();
  });

  it('renders pagination bar (GRID-06)', async () => {
    renderWithProviders(<CompaniesPage />, { route: '/companies', path: '/companies' });
    await screen.findByText('Acme Corp');
    expect(screen.getByText(/1 records/)).toBeInTheDocument();
  });

  it('searches companies after a short debounce', async () => {
    const user = userEvent.setup();
    renderWithProviders(<CompaniesPage />, { route: '/companies', path: '/companies' });
    await screen.findByText('Acme Corp');
    await user.type(screen.getByRole('textbox', { name: 'Search records' }), 'Acme');
    await waitFor(() => expect(getCompanies).toHaveBeenCalledWith(expect.objectContaining({ search: 'Acme' })));
  });

  it('sends industry, size, and owner filters and stays on page one', async () => {
    const user = userEvent.setup();
    renderWithProviders(<CompaniesPage />, { route: '/companies', path: '/companies' });
    await screen.findByText('Acme Corp');
    await user.selectOptions(screen.getByLabelText('Industry'), 'Technology');
    await user.selectOptions(screen.getByLabelText('Size'), '51-200');
    await user.selectOptions(screen.getByLabelText('Owner'), 'owner-1');
    await waitFor(() => expect(getCompanies).toHaveBeenCalledWith(expect.objectContaining({ page: 1, industry: 'Technology', size_range: '51-200', owner_id: 'owner-1' })));
    expect(getUsers).toHaveBeenCalledWith({ page: 1, size: 100 });
  });
});
