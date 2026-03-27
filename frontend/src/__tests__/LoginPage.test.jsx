import userEvent from '@testing-library/user-event';
import { screen, waitFor } from '@testing-library/react';
import LoginPage from '@/pages/LoginPage';
import { renderWithProviders } from './test-utils';

const { login, navigate, toastError } = vi.hoisted(() => ({
  login: vi.fn(),
  navigate: vi.fn(),
  toastError: vi.fn()
}));

vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({ login, isAuthenticated: false })
}));

vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal();
  return { ...actual, useNavigate: () => navigate };
});

vi.mock('sonner', () => ({ toast: { error: toastError } }));

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn().mockResolvedValue({ ok: true });
  });

  it('renders the form and submits credentials', async () => {
    login.mockResolvedValueOnce({});
    renderWithProviders(<LoginPage />, { route: '/login', path: '/login' });

    await userEvent.type(screen.getByLabelText(/email/i), 'demo@example.com');
    await userEvent.type(screen.getByLabelText(/password/i), 'secret');
    await userEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => expect(login).toHaveBeenCalledWith({ username: 'demo@example.com', password: 'secret' }));
    expect(navigate).toHaveBeenCalledWith('/');
  });

  it('handles login error', async () => {
    login.mockRejectedValueOnce({ response: { data: { detail: 'Invalid credentials' } } });
    renderWithProviders(<LoginPage />, { route: '/login', path: '/login' });

    await userEvent.type(screen.getByLabelText(/email/i), 'bad@example.com');
    await userEvent.type(screen.getByLabelText(/password/i), 'wrong');
    await userEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => expect(toastError).toHaveBeenCalledWith('Invalid credentials'));
  });

  it('shows backend status indicator', async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: true });
    renderWithProviders(<LoginPage />, { route: '/login', path: '/login' });
    await waitFor(() => expect(screen.getByText(/Backend: Connected/i)).toBeInTheDocument());
  });

  it('renders staging banner in non-production mode', () => {
    renderWithProviders(<LoginPage />, { route: '/login', path: '/login' });
    expect(screen.getByText(/environment/i)).toBeInTheDocument();
  });
});
