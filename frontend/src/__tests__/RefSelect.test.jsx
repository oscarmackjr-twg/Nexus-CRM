import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { RefSelect } from '@/components/RefSelect';

// Mock useRefData hook
vi.mock('@/hooks/useRefData');
import { useRefData } from '@/hooks/useRefData';

const mockItems = [
  { id: 'uuid-equity', label: 'Equity', value: 'equity', category: 'transaction_type', position: 0, is_active: true },
  { id: 'uuid-credit', label: 'Credit', value: 'credit', category: 'transaction_type', position: 0, is_active: true },
];

describe('RefSelect', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders options from useRefData data', () => {
    useRefData.mockReturnValue({ data: mockItems, isLoading: false, isError: false });
    render(<RefSelect category="transaction_type" value="" onChange={vi.fn()} />);
    expect(screen.getByText('Equity')).toBeInTheDocument();
    expect(screen.getByText('Credit')).toBeInTheDocument();
  });

  it('option value is the item id (UUID), not the value slug', () => {
    useRefData.mockReturnValue({ data: mockItems, isLoading: false, isError: false });
    render(<RefSelect category="transaction_type" value="" onChange={vi.fn()} />);
    const option = screen.getByRole('option', { name: 'Equity' });
    expect(option).toHaveAttribute('value', 'uuid-equity');
  });

  it('renders Loading... when isLoading is true', () => {
    useRefData.mockReturnValue({ data: [], isLoading: true, isError: false });
    render(<RefSelect category="transaction_type" value="" onChange={vi.fn()} />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
    expect(screen.getByRole('combobox')).toBeDisabled();
  });

  it('renders Failed to load when isError is true', () => {
    useRefData.mockReturnValue({ data: [], isLoading: false, isError: true });
    render(<RefSelect category="transaction_type" value="" onChange={vi.fn()} />);
    expect(screen.getByText('Failed to load')).toBeInTheDocument();
    expect(screen.getByRole('combobox')).toBeDisabled();
  });

  it('renders No options available when data is empty array', () => {
    useRefData.mockReturnValue({ data: [], isLoading: false, isError: false });
    render(<RefSelect category="transaction_type" value="" onChange={vi.fn()} />);
    expect(screen.getByText('No options available')).toBeInTheDocument();
  });

  it('renders placeholder as first disabled option', () => {
    useRefData.mockReturnValue({ data: mockItems, isLoading: false, isError: false });
    render(<RefSelect category="transaction_type" value="" onChange={vi.fn()} placeholder="Select tier" />);
    const placeholder = screen.getByRole('option', { name: 'Select tier' });
    expect(placeholder).toBeInTheDocument();
    expect(placeholder).toBeDisabled();
  });
});
