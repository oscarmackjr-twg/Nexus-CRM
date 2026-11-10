import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import { ExportCurrentViewButton } from '@/components/ExportCurrentViewButton';
import { renderWithProviders } from './test-utils';

const mocks = vi.hoisted(() => ({ downloadCsv: vi.fn() }));
vi.mock('@/lib/exportCsv', () => ({ downloadCsv: mocks.downloadCsv }));

describe('ExportCurrentViewButton', () => {
  it('includes active filter keys in the CSV filename', async () => {
    const user = userEvent.setup();
    renderWithProviders(<ExportCurrentViewButton resource="deals" filters={{ status: 'open', owner_id: 'owner-1' }} rows={[{ name: 'Alpha' }]} columns={[{ label: 'Deal', value: (row) => row.name }]} />);
    await user.click(screen.getByRole('button', { name: 'Export CSV' }));
    expect(mocks.downloadCsv).toHaveBeenCalledWith(expect.stringMatching(/^deals-status-owner_id-\d{4}-\d{2}-\d{2}\.csv$/), expect.any(Array), expect.any(Array));
  });
});
