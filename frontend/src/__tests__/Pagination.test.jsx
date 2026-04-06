import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Pagination } from '@/components/Pagination';
import { renderWithProviders } from './test-utils';

const defaultProps = {
  page: 1,
  pages: 5,
  total: 120,
  size: 25,
  onPageChange: vi.fn(),
  onSizeChange: vi.fn(),
};

describe('Pagination', () => {
  it('renders total records and page info (GRID-06)', () => {
    renderWithProviders(<Pagination {...defaultProps} />);
    expect(screen.getByText(/120 records/)).toBeInTheDocument();
    expect(screen.getByText(/Page 1 of 5/)).toBeInTheDocument();
  });

  it('disables Previous when on first page', () => {
    renderWithProviders(<Pagination {...defaultProps} page={1} />);
    expect(screen.getByText('Previous').closest('button')).toBeDisabled();
  });

  it('disables Next when on last page', () => {
    renderWithProviders(<Pagination {...defaultProps} page={5} />);
    expect(screen.getByText('Next').closest('button')).toBeDisabled();
  });

  it('enables both buttons on middle page', () => {
    renderWithProviders(<Pagination {...defaultProps} page={3} />);
    expect(screen.getByText('Previous').closest('button')).not.toBeDisabled();
    expect(screen.getByText('Next').closest('button')).not.toBeDisabled();
  });

  it('renders per-page selector with options 10, 25, 50, 100', () => {
    renderWithProviders(<Pagination {...defaultProps} />);
    const select = screen.getByDisplayValue('25 per page');
    expect(select).toBeInTheDocument();
    expect(select.options).toHaveLength(4);
  });

  it('is visible even when pages === 1 (D-08)', () => {
    renderWithProviders(<Pagination {...defaultProps} pages={1} total={5} />);
    expect(screen.getByText(/5 records/)).toBeInTheDocument();
    expect(screen.getByText('Previous')).toBeInTheDocument();
  });

  it('calls onPageChange when Next is clicked', async () => {
    const onPageChange = vi.fn();
    renderWithProviders(<Pagination {...defaultProps} page={2} onPageChange={onPageChange} />);
    await userEvent.click(screen.getByText('Next'));
    expect(onPageChange).toHaveBeenCalledWith(3);
  });
});
