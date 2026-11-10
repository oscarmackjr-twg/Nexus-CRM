import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import DealsPage from '@/pages/DealsPage';
import { renderWithProviders } from './test-utils';
import { getDeals } from '@/api/deals';
import { getPipelines } from '@/api/pipelines';
import { getUsers } from '@/api/users';

vi.mock('@/api/deals', () => ({
  createDeal: vi.fn(),
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
vi.mock('@/api/pipelines', () => ({ getPipelines: vi.fn().mockResolvedValue([{ id: 'pipeline-1', name: 'Sales', stages: [{ id: 'stage-1', name: 'Qualified' }] }]) }));
vi.mock('@/api/users', () => ({ getUsers: vi.fn().mockResolvedValue({ items: [{ id: 'owner-1', full_name: 'Ada Admin' }] }) }));

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

  it('searches deals after a short debounce', async () => {
    const user = userEvent.setup();
    renderWithProviders(<DealsPage />, { route: '/deals', path: '/deals' });
    await screen.findByText('Project Alpha');
    await user.type(screen.getByRole('textbox', { name: 'Search records' }), 'Alpha');
    await waitFor(() => expect(getDeals).toHaveBeenCalledWith(expect.objectContaining({ search: 'Alpha' })));
  });

  it('sends pipeline, dependent stage, owner, and status filters on page one', async () => {
    const user = userEvent.setup();
    renderWithProviders(<DealsPage />, { route: '/deals', path: '/deals' });
    await screen.findByText('Project Alpha');
    await user.selectOptions(screen.getByLabelText('Pipeline'), 'pipeline-1');
    await user.selectOptions(screen.getByLabelText('Stage'), 'stage-1');
    await user.selectOptions(screen.getByLabelText('Owner'), 'owner-1');
    await user.click(screen.getByText('Open'));
    await waitFor(() => expect(getDeals).toHaveBeenCalledWith(expect.objectContaining({ page: 1, pipeline_id: 'pipeline-1', stage_id: 'stage-1', owner_id: 'owner-1', status: 'open' })));
    expect(getPipelines).toHaveBeenCalled();
    expect(getUsers).toHaveBeenCalledWith({ page: 1, size: 100 });
  });
});
