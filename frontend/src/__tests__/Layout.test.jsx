import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Layout from '@/components/Layout';
import { renderWithProviders } from './test-utils';

const mockLogout = vi.fn();

vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({
    user: { full_name: 'Oscar Mack', username: 'oscar', role: 'admin' },
    logout: mockLogout,
    isAuthenticated: true
  })
}));

vi.mock('@/components/AIQueryBar', () => ({
  default: () => null
}));

vi.mock('@/components/StagingBanner', () => ({
  default: () => <div data-testid="staging-banner">STAGING -- Not Production</div>
}));

vi.mock('@/assets/twg-logo.png', () => ({ default: 'twg-logo.png' }));

describe('Layout sidebar', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders TWG logo in sidebar header (NAV-02)', () => {
    renderWithProviders(<Layout />, { route: '/', path: '/*' });
    const logo = screen.getByAltText('TWG Global');
    expect(logo).toBeInTheDocument();
    expect(logo.tagName).toBe('IMG');
  });

  it('renders Nexus CRM subtext in sidebar header (NAV-02)', () => {
    renderWithProviders(<Layout />, { route: '/', path: '/*' });
    expect(screen.getByText('Nexus CRM')).toBeInTheDocument();
  });

  it('renders section group labels (NAV-04)', () => {
    renderWithProviders(<Layout />, { route: '/', path: '/*' });
    expect(screen.getByText('DEALS')).toBeInTheDocument();
    expect(screen.getByText('TOOLS')).toBeInTheDocument();
    expect(screen.getByText('ADMIN')).toBeInTheDocument();
  });

  it('renders all nav items with correct names', () => {
    renderWithProviders(<Layout />, { route: '/', path: '/*' });
    const expectedItems = ['Dashboard', 'Contacts', 'Companies', 'Deals', 'Pipelines', 'Boards', 'Pages', 'Automations', 'Analytics', 'AI', 'LinkedIn', 'Admin', 'Team Settings'];
    expectedItems.forEach((name) => {
      expect(screen.getByText(name)).toBeInTheDocument();
    });
  });

  it('renders user footer with name, role, and sign out (NAV-05)', () => {
    renderWithProviders(<Layout />, { route: '/', path: '/*' });
    expect(screen.getByText('Oscar Mack')).toBeInTheDocument();
    expect(screen.getByText('admin')).toBeInTheDocument();
    expect(screen.getByText('Sign out')).toBeInTheDocument();
  });

  it('calls logout when Sign out is clicked (NAV-05)', async () => {
    renderWithProviders(<Layout />, { route: '/', path: '/*' });
    await userEvent.click(screen.getByText('Sign out'));
    expect(mockLogout).toHaveBeenCalled();
  });

  it('renders staging banner (BANNER-01)', () => {
    renderWithProviders(<Layout />, { route: '/', path: '/*' });
    expect(screen.getByTestId('staging-banner')).toBeInTheDocument();
  });
});
