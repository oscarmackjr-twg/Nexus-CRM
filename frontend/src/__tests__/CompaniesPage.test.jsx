import { screen } from '@testing-library/react';
import CompaniesPage from '@/pages/CompaniesPage';
import { renderWithProviders } from './test-utils';

vi.mock('@/api/companies', () => ({
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
});
