import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import { CoreRecordCreateDialog } from '@/components/CoreRecordCreateDialog';
import { renderWithProviders } from './test-utils';

const mocks = vi.hoisted(() => ({ createContact: vi.fn(), createCompany: vi.fn(), createDeal: vi.fn(), getPipelines: vi.fn() }));
vi.mock('@/api/contacts', () => ({ createContact: mocks.createContact }));
vi.mock('@/api/companies', () => ({ createCompany: mocks.createCompany }));
vi.mock('@/api/deals', () => ({ createDeal: mocks.createDeal }));
vi.mock('@/api/pipelines', () => ({ getPipelines: mocks.getPipelines }));

describe('CoreRecordCreateDialog', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows client validation before creating a contact', async () => {
    const user = userEvent.setup();
    renderWithProviders(<CoreRecordCreateDialog entity="contact" navigate={vi.fn()} />);
    await user.click(screen.getByRole('button', { name: 'New Contact' }));
    await user.click(screen.getByRole('button', { name: 'Create Contact' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Complete the required fields');
    expect(mocks.createContact).not.toHaveBeenCalled();
  });

  it('creates a contact and opens its detail route', async () => {
    const user = userEvent.setup();
    const navigate = vi.fn();
    mocks.createContact.mockResolvedValueOnce({ id: 'contact-42' });
    renderWithProviders(<CoreRecordCreateDialog entity="contact" navigate={navigate} />);
    await user.click(screen.getByRole('button', { name: 'New Contact' }));
    await user.type(screen.getByLabelText('First name'), 'Ada');
    await user.type(screen.getByLabelText('Last name'), 'Lovelace');
    await user.click(screen.getByRole('button', { name: 'Create Contact' }));
    await waitFor(() => expect(mocks.createContact.mock.calls[0][0]).toEqual({ first_name: 'Ada', last_name: 'Lovelace' }));
    await waitFor(() => expect(navigate).toHaveBeenCalledWith('/contacts/contact-42'));
  });

  it('creates a company and opens its detail route', async () => {
    const user = userEvent.setup();
    const navigate = vi.fn();
    mocks.createCompany.mockResolvedValueOnce({ id: 'company-42' });
    renderWithProviders(<CoreRecordCreateDialog entity="company" navigate={navigate} />);
    await user.click(screen.getByRole('button', { name: 'New Company' }));
    await user.type(screen.getByLabelText('Company name'), 'Analytical Engines');
    await user.click(screen.getByRole('button', { name: 'Create Company' }));
    await waitFor(() => expect(mocks.createCompany.mock.calls[0][0]).toEqual({ name: 'Analytical Engines' }));
    await waitFor(() => expect(navigate).toHaveBeenCalledWith('/companies/company-42'));
  });

  it('keeps entries visible after a failed create so the user can retry', async () => {
    const user = userEvent.setup();
    mocks.createCompany.mockRejectedValueOnce(new Error('service unavailable'));
    renderWithProviders(<CoreRecordCreateDialog entity="company" navigate={vi.fn()} />);
    await user.click(screen.getByRole('button', { name: 'New Company' }));
    await user.type(screen.getByLabelText('Company name'), 'Analytical Engines');
    await user.click(screen.getByRole('button', { name: 'Create Company' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('We could not create this company');
    expect(screen.getByLabelText('Company name')).toHaveValue('Analytical Engines');
  });

  it('loads pipeline stages, creates a deal, and opens its detail route', async () => {
    const user = userEvent.setup();
    const navigate = vi.fn();
    mocks.getPipelines.mockResolvedValueOnce([{ id: 'pipeline-1', name: 'Sales', stages: [{ id: 'stage-1', name: 'Qualified' }] }]);
    mocks.createDeal.mockResolvedValueOnce({ id: 'deal-42' });
    renderWithProviders(<CoreRecordCreateDialog entity="deal" navigate={navigate} />);
    await user.click(screen.getByRole('button', { name: 'New Deal' }));
    await user.type(screen.getByLabelText('Deal name'), 'Babbage expansion');
    await user.selectOptions(screen.getByLabelText('Pipeline'), 'pipeline-1');
    await user.selectOptions(screen.getByLabelText('Stage'), 'stage-1');
    await user.click(screen.getByRole('button', { name: 'Create Deal' }));
    await waitFor(() => expect(mocks.createDeal.mock.calls[0][0]).toEqual({ name: 'Babbage expansion', pipeline_id: 'pipeline-1', stage_id: 'stage-1', value: 0 }));
    await waitFor(() => expect(navigate).toHaveBeenCalledWith('/deals/deal-42'));
  });
});
