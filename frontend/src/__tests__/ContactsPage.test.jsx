import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ContactsPage from '@/pages/ContactsPage';
import { renderWithProviders } from './test-utils';
import { getContacts } from '@/api/contacts';
import { getCompanies } from '@/api/companies';
import { getUsers } from '@/api/users';

vi.mock('@/api/contacts', () => ({
  createContact: vi.fn(),
  getContacts: vi.fn().mockResolvedValue({
    items: [
      {
        id: '1',
        first_name: 'Alice',
        last_name: 'Smith',
        email: 'alice@test.com',
        company_name: 'Acme',
        title: 'CEO',
        lifecycle_stage: 'Lead',
        lead_score: 80,
        owner_name: 'Admin',
        updated_at: '2026-01-01T00:00:00Z',
      },
    ],
    total: 1,
    page: 1,
    size: 25,
    pages: 1,
  }),
}));
vi.mock('@/api/companies', () => ({ createCompany: vi.fn(), getCompanies: vi.fn().mockResolvedValue({ items: [{ id: 'company-1', name: 'Acme' }] }) }));
vi.mock('@/api/users', () => ({ getUsers: vi.fn().mockResolvedValue({ items: [{ id: 'owner-1', full_name: 'Ada Admin' }] }) }));

describe('ContactsPage', () => {
  it('renders page heading', async () => {
    renderWithProviders(<ContactsPage />, { route: '/contacts', path: '/contacts' });
    expect(await screen.findByText('Contacts')).toBeInTheDocument();
  });

  it('renders contact name in grid (GRID-01)', async () => {
    renderWithProviders(<ContactsPage />, { route: '/contacts', path: '/contacts' });
    expect(await screen.findByText('Alice Smith')).toBeInTheDocument();
  });

  it('renders column headers (GRID-04)', async () => {
    renderWithProviders(<ContactsPage />, { route: '/contacts', path: '/contacts' });
    await screen.findByText('Alice Smith');
    expect(screen.getByText('NAME')).toBeInTheDocument();
    expect(screen.getByText('COMPANY')).toBeInTheDocument();
    expect(screen.getByText('EMAIL')).toBeInTheDocument();
  });

  it('renders pagination bar (GRID-06)', async () => {
    renderWithProviders(<ContactsPage />, { route: '/contacts', path: '/contacts' });
    await screen.findByText('Alice Smith');
    expect(screen.getByText(/1 records/)).toBeInTheDocument();
  });

  it('searches contacts after a short debounce', async () => {
    const user = userEvent.setup();
    renderWithProviders(<ContactsPage />, { route: '/contacts', path: '/contacts' });
    await screen.findByText('Alice Smith');
    await user.type(screen.getByRole('textbox', { name: 'Search records' }), 'Alice');
    await waitFor(() => expect(getContacts).toHaveBeenCalledWith(expect.objectContaining({ search: 'Alice' })));
  });

  it('sends lifecycle, company, and owner filters and stays on page one', async () => {
    const user = userEvent.setup();
    renderWithProviders(<ContactsPage />, { route: '/contacts', path: '/contacts' });
    await screen.findByText('Alice Smith');
    await user.selectOptions(screen.getByLabelText('Stage'), 'lead');
    await user.selectOptions(screen.getByLabelText('Company'), 'company-1');
    await user.selectOptions(screen.getByLabelText('Owner'), 'owner-1');
    await waitFor(() => expect(getContacts).toHaveBeenCalledWith(expect.objectContaining({ page: 1, lifecycle_stage: 'lead', company_id: 'company-1', owner_id: 'owner-1' })));
    expect(getCompanies).toHaveBeenCalledWith({ page: 1, size: 100 });
    expect(getUsers).toHaveBeenCalledWith({ page: 1, size: 100 });
  });
});
