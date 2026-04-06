import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import DealsPage from '@/pages/DealsPage';
import { renderWithProviders } from './test-utils';
import { getDeals } from '@/api/deals';

vi.mock('@/api/deals', () => ({
  getDeals: vi.fn().mockResolvedValue({
    items: [
      {
        id: '1',
        name: 'Project Alpha',
        company_name: 'Acme Corp',
        stage_name: 'Due Diligence',
        value: 5000000,
        currency: 'USD',
        status: 'open',
        owner_name: 'Admin',
        expected_close_date: '2026-06-01T00:00:00Z',
        days_in_stage: 12,
      },
    ],
    total: 1,
    page: 1,
    size: 25,
    pages: 1,
  }),
}));

describe('DealsPage', () => {
  it('renders page heading', async () => {
    renderWithProviders(<DealsPage />, { route: '/deals', path: '/deals' });
    expect(await screen.findByText('Deals')).toBeInTheDocument();
  });

  it('renders deal name in grid (GRID-03)', async () => {
    renderWithProviders(<DealsPage />, { route: '/deals', path: '/deals' });
    expect(await screen.findByText('Project Alpha')).toBeInTheDocument();
  });

  it('renders column headers (GRID-04)', async () => {
    renderWithProviders(<DealsPage />, { route: '/deals', path: '/deals' });
    await screen.findByText('Project Alpha');
    expect(screen.getByText('DEAL')).toBeInTheDocument();
    expect(screen.getByText('COMPANY')).toBeInTheDocument();
    expect(screen.getByText('STATUS')).toBeInTheDocument();
  });

  it('renders status filter tabs (D-04)', async () => {
    renderWithProviders(<DealsPage />, { route: '/deals', path: '/deals' });
    await screen.findByText('Project Alpha');
    expect(screen.getByText('All')).toBeInTheDocument();
    expect(screen.getByText('Open')).toBeInTheDocument();
    expect(screen.getByText('Won')).toBeInTheDocument();
    expect(screen.getByText('Lost')).toBeInTheDocument();
  });

  it('filters by status when tab is clicked (D-04)', async () => {
    renderWithProviders(<DealsPage />, { route: '/deals', path: '/deals' });
    await screen.findByText('Project Alpha');
    await userEvent.click(screen.getByText('Open'));
    expect(getDeals).toHaveBeenCalledWith(expect.objectContaining({ status: 'open' }));
  });

  it('renders pagination bar (GRID-06)', async () => {
    renderWithProviders(<DealsPage />, { route: '/deals', path: '/deals' });
    await screen.findByText('Project Alpha');
    expect(screen.getByText(/1 records/)).toBeInTheDocument();
  });
});
