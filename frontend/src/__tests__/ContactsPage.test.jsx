import { screen } from '@testing-library/react';
import ContactsPage from '@/pages/ContactsPage';
import { renderWithProviders } from './test-utils';

vi.mock('@/api/contacts', () => ({
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
});
