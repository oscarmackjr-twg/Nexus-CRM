import { useState, useMemo } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Pencil, X, Plus, Trash2 } from 'lucide-react';
import { toast } from 'sonner';
import { getDeal, getDealActivities, logActivity, scoreDeal, updateDeal } from '@/api/deals';
import { getFunds, createFund } from '@/api/funds';
import { getCounterparties, createCounterparty, updateCounterparty, deleteCounterparty } from '@/api/counterparties';
import { getFunding, createFunding, updateFunding, deleteFunding } from '@/api/funding';
import { getUsers } from '@/api/users';
import { getCompanies } from '@/api/companies';
import { getContacts } from '@/api/contacts';
import { getBoards, getBoard } from '@/api/boards';
import { FieldRow } from '@/components/FieldRow';
import { RefSelect } from '@/components/RefSelect';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { formatCurrency, formatDate } from '@/lib/utils';

// ---- AI Score Card (preserved from original) ----
function DealScoreCard({ dealId }) {
  const scoreQuery = useQuery({
    queryKey: ['deal-score', dealId],
    queryFn: () => scoreDeal(dealId),
    retry: false,
  });
  const score = scoreQuery.data?.ai_score;
  return (
    <Card>
      <CardHeader className="border-b border-gray-200 pb-3"><CardTitle>AI Insights</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-4">
          <div className="flex h-24 w-24 items-center justify-center rounded-full border-8 border-primary/15 text-xl font-semibold">
            {score == null ? 'N/A' : Math.round(score)}
          </div>
          <div>
            <p className="font-medium">
              {score == null ? 'Not scored' : `Confidence: ${scoreQuery.data?.confidence}`}
            </p>
            <p className="text-sm text-muted-foreground">
              {scoreQuery.data?.next_action || 'Score this deal to get next-best action guidance.'}
            </p>
          </div>
        </div>
        <div className="space-y-2">
          {(scoreQuery.data?.factors || []).map((factor, index) => (
            <div key={index} className="rounded-xl bg-muted/40 px-3 py-2 text-sm">
              {factor.label || factor.factor || JSON.stringify(factor)}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

// ---- Loading skeleton for a card ----
function CardSkeleton({ height = 'h-48' }) {
  return <Skeleton className={`${height} w-full rounded-2xl`} />;
}

// ---- Per-card Edit/Save footer ----
function CardEditFooter({ onSave, onCancel, isSaving }) {
  return (
    <div className="flex justify-end gap-2 pt-4 border-t mt-4">
      <Button variant="ghost" size="sm" onClick={onCancel} disabled={isSaving}>
        Cancel
      </Button>
      <Button size="sm" onClick={onSave} disabled={isSaving}>
        {isSaving ? 'Saving…' : 'Save Changes'}
      </Button>
    </div>
  );
}

// ---- Counterparties Tab ----
function CounterpartiesTab({ dealId, companies }) {
  const [addOpen, setAddOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [editingRow, setEditingRow] = useState(null);
  const [editingCell, setEditingCell] = useState(null); // format: `${rowId}-${fieldName}`
  const [addForm, setAddForm] = useState({
    company_id: '',
    tier_id: '',
    investor_type_id: '',
    primary_contact_name: '',
    check_size_amount: '',
    check_size_currency: 'USD',
    next_steps: '',
  });
  const [editForm, setEditForm] = useState({});
  const queryClient = useQueryClient();

  const cpartiesQuery = useQuery({
    queryKey: ['deal-counterparties', dealId],
    queryFn: () => getCounterparties(dealId, { size: 200 }),
  });

  const createMutation = useMutation({
    mutationFn: (data) => createCounterparty(dealId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deal-counterparties', dealId] });
      setAddOpen(false);
      setAddForm({ company_id: '', tier_id: '', investor_type_id: '', primary_contact_name: '', check_size_amount: '', check_size_currency: 'USD', next_steps: '' });
      toast.success('Counterparty added');
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Failed to add counterparty'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => updateCounterparty(dealId, id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deal-counterparties', dealId] });
      setEditOpen(false);
      setEditingRow(null);
      setEditingCell(null);
      toast.success('Counterparty updated');
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Failed to update'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id) => deleteCounterparty(dealId, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deal-counterparties', dealId] });
      toast.success('Counterparty removed');
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Failed to remove'),
  });

  const stageDateCols = [
    { key: 'nda_sent_at', label: 'NDA Sent' },
    { key: 'nda_signed_at', label: 'NDA Signed' },
    { key: 'nrl_signed_at', label: 'NRL' },
    { key: 'intro_materials_sent_at', label: 'Materials' },
    { key: 'vdr_access_granted_at', label: 'VDR' },
    { key: 'feedback_received_at', label: 'Feedback' },
  ];

  const handleDateChange = (row, field, value) => {
    updateMutation.mutate({ id: row.id, data: { [field]: value || null } });
  };

  const fmtShortDate = (d) => {
    if (!d) return '';
    const dt = new Date(d + 'T00:00:00');
    return dt.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const openEdit = (row) => {
    setEditingRow(row);
    setEditForm({
      company_id: row.company_id || '',
      tier_id: row.tier_id || '',
      investor_type_id: row.investor_type_id || '',
      primary_contact_name: row.primary_contact_name || '',
      primary_contact_email: row.primary_contact_email || '',
      primary_contact_phone: row.primary_contact_phone || '',
      check_size_amount: row.check_size_amount ?? '',
      check_size_currency: row.check_size_currency || 'USD',
      aum_amount: row.aum_amount ?? '',
      aum_currency: row.aum_currency || 'USD',
      nda_sent_at: row.nda_sent_at || '',
      nda_signed_at: row.nda_signed_at || '',
      nrl_signed_at: row.nrl_signed_at || '',
      intro_materials_sent_at: row.intro_materials_sent_at || '',
      vdr_access_granted_at: row.vdr_access_granted_at || '',
      feedback_received_at: row.feedback_received_at || '',
      next_steps: row.next_steps || '',
      notes: row.notes || '',
    });
    setEditOpen(true);
  };

  const cleanFormData = (form) => {
    const out = {};
    for (const [k, v] of Object.entries(form)) {
      out[k] = v === '' ? null : v;
    }
    return out;
  };

  const items = cpartiesQuery.data?.items || [];

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button onClick={() => setAddOpen(true)}>
          <Plus className="h-4 w-4 mr-1" /> Add Counterparty
        </Button>
      </div>

      {cpartiesQuery.isLoading ? (
        <p className="text-sm text-muted-foreground">Loading counterparties...</p>
      ) : items.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          <p>No counterparties tracked yet. Add the first investor to start tracking stage progression.</p>
          <Button className="mt-4" onClick={() => setAddOpen(true)}>
            <Plus className="h-4 w-4 mr-1" /> Add Counterparty
          </Button>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/40">
                <th className="sticky left-0 z-10 bg-muted/40 px-4 py-2 text-left font-medium whitespace-nowrap">Company</th>
                <th className="px-4 py-2 text-left font-medium whitespace-nowrap">Tier</th>
                <th className="px-4 py-2 text-left font-medium whitespace-nowrap">Investor Type</th>
                {stageDateCols.map((col) => (
                  <th key={col.key} className="w-24 px-4 py-2 text-left font-medium whitespace-nowrap">{col.label}</th>
                ))}
                <th className="px-4 py-2 text-left font-medium">Next Steps</th>
                <th className="px-4 py-2 text-left font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((row) => (
                <tr key={row.id} className="border-b last:border-b-0 hover:bg-muted/20">
                  <td className="sticky left-0 z-10 bg-white px-4 py-2 font-medium whitespace-nowrap">{row.company_name || '—'}</td>
                  <td className="px-4 py-2 whitespace-nowrap">{row.tier_label || '---'}</td>
                  <td className="px-4 py-2 whitespace-nowrap">{row.investor_type_label || '---'}</td>
                  {stageDateCols.map((col) => (
                    <td key={col.key} className="w-24 px-4 py-2">
                      {editingCell === `${row.id}-${col.key}` ? (
                        <input
                          type="date"
                          autoFocus
                          className="w-24 rounded border px-1 py-0.5 text-xs"
                          defaultValue={row[col.key] ? row[col.key].substring(0, 10) : ''}
                          onChange={(e) => handleDateChange(row, col.key, e.target.value)}
                          onBlur={() => setEditingCell(null)}
                        />
                      ) : (
                        <span
                          className="cursor-pointer hover:text-primary"
                          onClick={() => setEditingCell(`${row.id}-${col.key}`)}
                        >
                          {fmtShortDate(row[col.key]) || <span className="text-muted-foreground text-xs">—</span>}
                        </span>
                      )}
                    </td>
                  ))}
                  <td className="px-4 py-2 max-w-xs truncate">{row.next_steps || '—'}</td>
                  <td className="px-4 py-2">
                    <div className="flex gap-1">
                      <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => openEdit(row)}>
                        <Pencil className="h-3.5 w-3.5" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7 text-destructive hover:text-destructive"
                        onClick={() => deleteMutation.mutate(row.id)}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Add Counterparty Dialog */}
      <Dialog open={addOpen} onOpenChange={setAddOpen}>
        <DialogContent className="max-w-md p-6">
          <DialogHeader>
            <DialogTitle>Add Counterparty</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-1">
              <Label>Company *</Label>
              <select
                className="flex h-10 w-full rounded-xl border border-input bg-background px-3 text-sm"
                value={addForm.company_id}
                onChange={(e) => setAddForm((f) => ({ ...f, company_id: e.target.value }))}
              >
                <option value="">Select company...</option>
                {companies.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
            <div className="space-y-1">
              <Label>Tier</Label>
              <RefSelect
                category="tier"
                value={addForm.tier_id}
                onChange={(v) => setAddForm((f) => ({ ...f, tier_id: v }))}
              />
            </div>
            <div className="space-y-1">
              <Label>Investor Type</Label>
              <RefSelect
                category="investor_type"
                value={addForm.investor_type_id}
                onChange={(v) => setAddForm((f) => ({ ...f, investor_type_id: v }))}
              />
            </div>
            <div className="space-y-1">
              <Label>Primary Contact Name</Label>
              <Input
                value={addForm.primary_contact_name}
                onChange={(e) => setAddForm((f) => ({ ...f, primary_contact_name: e.target.value }))}
                placeholder="e.g. Jane Smith"
              />
            </div>
            <div className="space-y-1">
              <Label>Check Size</Label>
              <div className="flex gap-2">
                <Input
                  type="number"
                  className="flex-1"
                  placeholder="Amount"
                  value={addForm.check_size_amount}
                  onChange={(e) => setAddForm((f) => ({ ...f, check_size_amount: e.target.value }))}
                />
                <Input
                  className="w-16 uppercase"
                  maxLength={3}
                  placeholder="USD"
                  value={addForm.check_size_currency}
                  onChange={(e) => setAddForm((f) => ({ ...f, check_size_currency: e.target.value.toUpperCase() }))}
                />
              </div>
            </div>
            <div className="space-y-1">
              <Label>Next Steps</Label>
              <Textarea
                value={addForm.next_steps}
                onChange={(e) => setAddForm((f) => ({ ...f, next_steps: e.target.value }))}
                rows={2}
              />
            </div>
          </div>
          <div className="flex justify-end gap-2 mt-4">
            <Button variant="ghost" onClick={() => setAddOpen(false)}>Cancel</Button>
            <Button
              disabled={!addForm.company_id || createMutation.isPending}
              onClick={() => createMutation.mutate(cleanFormData(addForm))}
            >
              {createMutation.isPending ? 'Adding…' : 'Add Counterparty'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Edit Counterparty Dialog */}
      <Dialog open={editOpen} onOpenChange={(o) => { if (!o) { setEditOpen(false); setEditingRow(null); } }}>
        <DialogContent className="max-w-lg p-6 max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Counterparty</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-1">
              <Label>Company</Label>
              <select
                className="flex h-10 w-full rounded-xl border border-input bg-background px-3 text-sm"
                value={editForm.company_id || ''}
                onChange={(e) => setEditForm((f) => ({ ...f, company_id: e.target.value }))}
              >
                <option value="">Select company...</option>
                {companies.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
            <div className="space-y-1">
              <Label>Tier</Label>
              <RefSelect
                category="tier"
                value={editForm.tier_id || ''}
                onChange={(v) => setEditForm((f) => ({ ...f, tier_id: v }))}
              />
            </div>
            <div className="space-y-1">
              <Label>Investor Type</Label>
              <RefSelect
                category="investor_type"
                value={editForm.investor_type_id || ''}
                onChange={(v) => setEditForm((f) => ({ ...f, investor_type_id: v }))}
              />
            </div>
            <div className="space-y-1">
              <Label>Primary Contact Name</Label>
              <Input
                value={editForm.primary_contact_name || ''}
                onChange={(e) => setEditForm((f) => ({ ...f, primary_contact_name: e.target.value }))}
              />
            </div>
            <div className="space-y-1">
              <Label>Primary Contact Email</Label>
              <Input
                type="email"
                value={editForm.primary_contact_email || ''}
                onChange={(e) => setEditForm((f) => ({ ...f, primary_contact_email: e.target.value }))}
              />
            </div>
            <div className="space-y-1">
              <Label>Primary Contact Phone</Label>
              <Input
                value={editForm.primary_contact_phone || ''}
                onChange={(e) => setEditForm((f) => ({ ...f, primary_contact_phone: e.target.value }))}
              />
            </div>
            <div className="space-y-1">
              <Label>Check Size</Label>
              <div className="flex gap-2">
                <Input
                  type="number"
                  className="flex-1"
                  placeholder="Amount"
                  value={editForm.check_size_amount ?? ''}
                  onChange={(e) => setEditForm((f) => ({ ...f, check_size_amount: e.target.value }))}
                />
                <Input
                  className="w-16 uppercase"
                  maxLength={3}
                  placeholder="USD"
                  value={editForm.check_size_currency || 'USD'}
                  onChange={(e) => setEditForm((f) => ({ ...f, check_size_currency: e.target.value.toUpperCase() }))}
                />
              </div>
            </div>
            <div className="space-y-1">
              <Label>AUM</Label>
              <div className="flex gap-2">
                <Input
                  type="number"
                  className="flex-1"
                  placeholder="Amount"
                  value={editForm.aum_amount ?? ''}
                  onChange={(e) => setEditForm((f) => ({ ...f, aum_amount: e.target.value }))}
                />
                <Input
                  className="w-16 uppercase"
                  maxLength={3}
                  placeholder="USD"
                  value={editForm.aum_currency || 'USD'}
                  onChange={(e) => setEditForm((f) => ({ ...f, aum_currency: e.target.value.toUpperCase() }))}
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              {stageDateCols.map((col) => (
                <div key={col.key} className="space-y-1">
                  <Label>{col.label}</Label>
                  <Input
                    type="date"
                    value={editForm[col.key] ? editForm[col.key].substring(0, 10) : ''}
                    onChange={(e) => setEditForm((f) => ({ ...f, [col.key]: e.target.value }))}
                  />
                </div>
              ))}
            </div>
            <div className="space-y-1">
              <Label>Next Steps</Label>
              <Textarea
                value={editForm.next_steps || ''}
                onChange={(e) => setEditForm((f) => ({ ...f, next_steps: e.target.value }))}
                rows={2}
              />
            </div>
            <div className="space-y-1">
              <Label>Notes</Label>
              <Textarea
                value={editForm.notes || ''}
                onChange={(e) => setEditForm((f) => ({ ...f, notes: e.target.value }))}
                rows={2}
              />
            </div>
          </div>
          <div className="flex justify-end gap-2 mt-4">
            <Button variant="ghost" onClick={() => { setEditOpen(false); setEditingRow(null); }}>Cancel</Button>
            <Button
              disabled={updateMutation.isPending}
              onClick={() => updateMutation.mutate({ id: editingRow.id, data: cleanFormData(editForm) })}
            >
              {updateMutation.isPending ? 'Saving…' : 'Save Changes'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// ---- Funding Tab ----
function FundingTab({ dealId, companies }) {
  const [modalOpen, setModalOpen] = useState(false);
  const [editingEntry, setEditingEntry] = useState(null); // null = add mode, object = edit mode
  const [form, setForm] = useState({
    capital_provider_id: '',
    status_id: '',
    projected_commitment_amount: '',
    projected_commitment_currency: 'USD',
    actual_commitment_amount: '',
    actual_commitment_currency: 'USD',
    actual_commitment_date: '',
    terms: '',
    comments_next_steps: '',
  });
  const queryClient = useQueryClient();

  const fundingQuery = useQuery({
    queryKey: ['deal-funding', dealId],
    queryFn: () => getFunding(dealId, { size: 200 }),
  });

  const createMutation = useMutation({
    mutationFn: (data) => createFunding(dealId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deal-funding', dealId] });
      setModalOpen(false);
      resetForm();
      toast.success('Funding entry added');
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Failed to add funding'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => updateFunding(dealId, id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deal-funding', dealId] });
      setModalOpen(false);
      setEditingEntry(null);
      resetForm();
      toast.success('Funding updated');
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Failed to update funding'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id) => deleteFunding(dealId, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deal-funding', dealId] });
      toast.success('Funding entry removed');
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Failed to remove'),
  });

  const emptyForm = {
    capital_provider_id: '',
    status_id: '',
    projected_commitment_amount: '',
    projected_commitment_currency: 'USD',
    actual_commitment_amount: '',
    actual_commitment_currency: 'USD',
    actual_commitment_date: '',
    terms: '',
    comments_next_steps: '',
  };

  const resetForm = () => setForm(emptyForm);

  const openAdd = () => {
    setEditingEntry(null);
    resetForm();
    setModalOpen(true);
  };

  const openEdit = (entry) => {
    setEditingEntry(entry);
    setForm({
      capital_provider_id: entry.capital_provider_id || '',
      status_id: entry.status_id || '',
      projected_commitment_amount: entry.projected_commitment_amount ?? '',
      projected_commitment_currency: entry.projected_commitment_currency || 'USD',
      actual_commitment_amount: entry.actual_commitment_amount ?? '',
      actual_commitment_currency: entry.actual_commitment_currency || 'USD',
      actual_commitment_date: entry.actual_commitment_date ? entry.actual_commitment_date.substring(0, 10) : '',
      terms: entry.terms || '',
      comments_next_steps: entry.comments_next_steps || '',
    });
    setModalOpen(true);
  };

  const cleanFormData = (f) => {
    const out = {};
    for (const [k, v] of Object.entries(f)) {
      out[k] = v === '' ? null : v;
    }
    return out;
  };

  const handleSubmit = () => {
    const data = cleanFormData(form);
    if (editingEntry) {
      updateMutation.mutate({ id: editingEntry.id, data });
    } else {
      createMutation.mutate(data);
    }
  };

  const fmtCommitment = (amount, currency) =>
    amount == null ? '—' : `${amount} ${currency || ''}`.trim();

  const items = fundingQuery.data?.items || [];
  const isPending = createMutation.isPending || updateMutation.isPending;

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button onClick={openAdd}>
          <Plus className="h-4 w-4 mr-1" /> Add Funding
        </Button>
      </div>

      {fundingQuery.isLoading ? (
        <p className="text-sm text-muted-foreground">Loading funding...</p>
      ) : items.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          <p>No funding commitments recorded. Add a capital provider to track commitments.</p>
          <Button className="mt-4" onClick={openAdd}>
            <Plus className="h-4 w-4 mr-1" /> Add Funding
          </Button>
        </div>
      ) : (
        <div className="rounded-xl border overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/40">
                <th className="px-4 py-2 text-left font-medium">Provider</th>
                <th className="px-4 py-2 text-left font-medium">Status</th>
                <th className="px-4 py-2 text-left font-medium">Projected</th>
                <th className="px-4 py-2 text-left font-medium">Actual</th>
                <th className="px-4 py-2 text-left font-medium">Date</th>
                <th className="px-4 py-2 text-left font-medium">Terms</th>
                <th className="px-4 py-2 text-left font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((entry) => (
                <tr key={entry.id} className="border-b last:border-b-0 hover:bg-muted/20">
                  <td className="px-4 py-2 font-medium">{entry.capital_provider_name || '—'}</td>
                  <td className="px-4 py-2">{entry.status_label || '---'}</td>
                  <td className="px-4 py-2 whitespace-nowrap">{fmtCommitment(entry.projected_commitment_amount, entry.projected_commitment_currency)}</td>
                  <td className="px-4 py-2 whitespace-nowrap">{fmtCommitment(entry.actual_commitment_amount, entry.actual_commitment_currency)}</td>
                  <td className="px-4 py-2 whitespace-nowrap">{entry.actual_commitment_date ? entry.actual_commitment_date.substring(0, 10) : '—'}</td>
                  <td className="px-4 py-2 max-w-xs">
                    {entry.terms ? (
                      <span title={entry.terms}>{entry.terms.length > 50 ? entry.terms.substring(0, 50) + '…' : entry.terms}</span>
                    ) : '—'}
                  </td>
                  <td className="px-4 py-2">
                    <div className="flex gap-1">
                      <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => openEdit(entry)}>
                        <Pencil className="h-3.5 w-3.5" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7 text-destructive hover:text-destructive"
                        onClick={() => deleteMutation.mutate(entry.id)}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Add/Edit Funding Modal */}
      <Dialog open={modalOpen} onOpenChange={(o) => { if (!o) { setModalOpen(false); setEditingEntry(null); resetForm(); } }}>
        <DialogContent className="max-w-md p-6">
          <DialogHeader>
            <DialogTitle>{editingEntry ? 'Edit Funding' : 'Add Funding'}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-1">
              <Label>Capital Provider</Label>
              <select
                className="flex h-10 w-full rounded-xl border border-input bg-background px-3 text-sm"
                value={form.capital_provider_id}
                onChange={(e) => setForm((f) => ({ ...f, capital_provider_id: e.target.value }))}
              >
                <option value="">Select company...</option>
                {companies.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
            <div className="space-y-1">
              <Label>Status</Label>
              <RefSelect
                category="deal_funding_status"
                value={form.status_id}
                onChange={(v) => setForm((f) => ({ ...f, status_id: v }))}
              />
            </div>
            <div className="space-y-1">
              <Label>Projected Commitment</Label>
              <div className="flex gap-2">
                <Input
                  type="number"
                  className="flex-1"
                  placeholder="Amount"
                  value={form.projected_commitment_amount}
                  onChange={(e) => setForm((f) => ({ ...f, projected_commitment_amount: e.target.value }))}
                />
                <Input
                  className="w-16 uppercase"
                  maxLength={3}
                  placeholder="USD"
                  value={form.projected_commitment_currency}
                  onChange={(e) => setForm((f) => ({ ...f, projected_commitment_currency: e.target.value.toUpperCase() }))}
                />
              </div>
            </div>
            <div className="space-y-1">
              <Label>Actual Commitment</Label>
              <div className="flex gap-2">
                <Input
                  type="number"
                  className="flex-1"
                  placeholder="Amount"
                  value={form.actual_commitment_amount}
                  onChange={(e) => setForm((f) => ({ ...f, actual_commitment_amount: e.target.value }))}
                />
                <Input
                  className="w-16 uppercase"
                  maxLength={3}
                  placeholder="USD"
                  value={form.actual_commitment_currency}
                  onChange={(e) => setForm((f) => ({ ...f, actual_commitment_currency: e.target.value.toUpperCase() }))}
                />
              </div>
            </div>
            <div className="space-y-1">
              <Label>Commitment Date</Label>
              <Input
                type="date"
                value={form.actual_commitment_date}
                onChange={(e) => setForm((f) => ({ ...f, actual_commitment_date: e.target.value }))}
              />
            </div>
            <div className="space-y-1">
              <Label>Terms</Label>
              <Textarea
                value={form.terms}
                onChange={(e) => setForm((f) => ({ ...f, terms: e.target.value }))}
                rows={2}
              />
            </div>
            <div className="space-y-1">
              <Label>Comments / Next Steps</Label>
              <Textarea
                value={form.comments_next_steps}
                onChange={(e) => setForm((f) => ({ ...f, comments_next_steps: e.target.value }))}
                rows={2}
              />
            </div>
          </div>
          <div className="flex justify-end gap-2 mt-4">
            <Button variant="ghost" onClick={() => { setModalOpen(false); setEditingEntry(null); resetForm(); }}>Cancel</Button>
            <Button disabled={isPending} onClick={handleSubmit}>
              {isPending ? 'Saving…' : editingEntry ? 'Save Changes' : 'Add Funding'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default function DealDetailPage() {
  const { id } = useParams();
  const queryClient = useQueryClient();

  // One-at-a-time card editing
  const [editingCard, setEditingCard] = useState(null); // 'identity'|'financials'|'milestones'|'sourceTeam'|'passedDead'|null
  const [fundModalOpen, setFundModalOpen] = useState(false);

  // Per-card local form state
  const [identityForm, setIdentityForm] = useState(null);
  const [financialsForm, setFinancialsForm] = useState(null);
  const [milestonesForm, setMilestonesForm] = useState(null);
  const [sourceTeamForm, setSourceTeamForm] = useState(null);
  const [passedDeadForm, setPassedDeadForm] = useState(null);

  // Fund modal form state
  const [fundForm, setFundForm] = useState({
    fund_name: '',
    fundraise_status_id: '',
    target_fund_size_amount: '',
    target_fund_size_currency: 'USD',
    vintage_year: '',
  });

  // Activity tab state (preserved from original)
  const [draftTitle, setDraftTitle] = useState('');
  const [draftBody, setDraftBody] = useState('');

  // Queries
  const dealQuery = useQuery({ queryKey: ['deal', id], queryFn: () => getDeal(id) });
  const fundsQuery = useQuery({ queryKey: ['funds'], queryFn: getFunds });
  const usersQuery = useQuery({ queryKey: ['users'], queryFn: getUsers });
  const companiesQuery = useQuery({ queryKey: ['companies'], queryFn: () => getCompanies({ size: 200 }) });
  const contactsQuery = useQuery({ queryKey: ['contacts'], queryFn: () => getContacts({ size: 200 }) });
  const activitiesQuery = useQuery({
    queryKey: ['deal', id, 'activities'],
    queryFn: () => getDealActivities(id, { size: 50 }),
  });
  const tasksQuery = useQuery({
    queryKey: ['deal', id, 'tasks'],
    queryFn: async () => {
      const boards = await getBoards();
      const details = await Promise.all(boards.slice(0, 4).map((b) => getBoard(b.id).catch(() => null)));
      return details
        .filter(Boolean)
        .flatMap((b) => b.columns.flatMap((col) => col.tasks))
        .filter((t) => t.deal_id === id);
    },
  });

  const deal = dealQuery.data;
  const funds = fundsQuery.data || [];
  const users = usersQuery.data || [];
  const companies = (companiesQuery.data?.items || companiesQuery.data || []);
  const contacts = (contactsQuery.data?.items || contactsQuery.data || []);

  // Sync local form state from deal on load (once)
  useMemo(() => {
    if (!deal) return;
    if (identityForm === null) {
      setIdentityForm({
        transaction_type_id: deal.transaction_type_id || '',
        fund_id: deal.fund_id || '',
        platform_or_addon: deal.platform_or_addon || '',
        platform_company_id: deal.platform_company_id || '',
        description: deal.description || '',
        legacy_id: deal.legacy_id || '',
      });
    }
    if (financialsForm === null) {
      setFinancialsForm({
        revenue_amount: deal.revenue_amount ?? '',
        revenue_currency: deal.revenue_currency || 'USD',
        ebitda_amount: deal.ebitda_amount ?? '',
        ebitda_currency: deal.ebitda_currency || 'USD',
        enterprise_value_amount: deal.enterprise_value_amount ?? '',
        enterprise_value_currency: deal.enterprise_value_currency || 'USD',
        equity_investment_amount: deal.equity_investment_amount ?? '',
        equity_investment_currency: deal.equity_investment_currency || 'USD',
        ioi_bid_amount: deal.ioi_bid_amount ?? '',
        ioi_bid_currency: deal.ioi_bid_currency || 'USD',
        loi_bid_amount: deal.loi_bid_amount ?? '',
        loi_bid_currency: deal.loi_bid_currency || 'USD',
      });
    }
    if (milestonesForm === null) {
      setMilestonesForm({
        new_deal_date: deal.new_deal_date || '',
        cim_received_date: deal.cim_received_date || '',
        ioi_due_date: deal.ioi_due_date || '',
        ioi_submitted_date: deal.ioi_submitted_date || '',
        management_presentation_date: deal.management_presentation_date || '',
        loi_due_date: deal.loi_due_date || '',
        loi_submitted_date: deal.loi_submitted_date || '',
        live_diligence_date: deal.live_diligence_date || '',
        portfolio_company_date: deal.portfolio_company_date || '',
      });
    }
    if (sourceTeamForm === null) {
      setSourceTeamForm({
        deal_team: deal.deal_team || [],
        originator_id: deal.originator_id || '',
        source_type_id: deal.source_type_id || '',
        source_company_id: deal.source_company_id || '',
        source_individual_id: deal.source_individual_id || '',
      });
    }
    if (passedDeadForm === null) {
      setPassedDeadForm({
        passed_dead_date: deal.passed_dead_date || '',
        passed_dead_reasons: deal.passed_dead_reasons || [],
        passed_dead_commentary: deal.passed_dead_commentary || '',
      });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [deal]);

  // Mutations
  const updateDealMutation = useMutation({
    mutationFn: (data) => updateDeal(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deal', id] });
      setEditingCard(null);
      toast.success('Deal updated');
    },
    onError: () => toast.error('Failed to save changes. Please try again.'),
  });

  const createFundMutation = useMutation({
    mutationFn: createFund,
    onSuccess: (newFund) => {
      queryClient.invalidateQueries({ queryKey: ['funds'] });
      setIdentityForm((prev) => ({ ...prev, fund_id: newFund.id }));
      setFundModalOpen(false);
      setFundForm({ fund_name: '', fundraise_status_id: '', target_fund_size_amount: '', target_fund_size_currency: 'USD', vintage_year: '' });
      toast.success('Fund created');
    },
    onError: () => toast.error('Failed to create fund. Please try again.'),
  });

  const logMutation = useMutation({
    mutationFn: (payload) => logActivity(id, payload),
    onSuccess: () => {
      setDraftBody('');
      setDraftTitle('');
      queryClient.invalidateQueries({ queryKey: ['deal', id, 'activities'] });
      toast.success('Activity logged');
    },
  });

  const isSaving = updateDealMutation.isPending;

  // ---- Loading state ----
  if (dealQuery.isLoading) {
    return (
      <div className="space-y-6 p-6">
        <div className="flex gap-4">
          {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-8 w-24 rounded-lg" />)}
        </div>
        {[...Array(5)].map((_, i) => <CardSkeleton key={i} />)}
      </div>
    );
  }

  // ---- Error state ----
  if (dealQuery.isError) {
    return (
      <div className="p-6 text-center text-muted-foreground">
        Could not load deal. It may have been removed.
      </div>
    );
  }

  // ---- Helper functions ----
  const openCard = (card) => {
    if (editingCard === card) return;
    setEditingCard(card);
  };

  const cancelCard = () => setEditingCard(null);

  const fmt = (val) => (val == null || val === '') ? '—' : val;
  const fmtDate = (val) => (val == null || val === '') ? '—' : formatDate(val);
  const fmtAmount = (amount, currency) =>
    (amount == null || amount === '') ? '—' : `${amount} ${currency || ''}`.trim();

  // ---- Render ----
  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">{deal?.name || 'Unnamed Deal'}</h1>
        <Badge>{deal?.stage_name}</Badge>
      </div>

      <Tabs defaultValue="profile">
        <TabsList className="detail-tabs">
          <TabsTrigger value="profile">Profile</TabsTrigger>
          <TabsTrigger value="counterparties">Counterparties</TabsTrigger>
          <TabsTrigger value="funding">Funding</TabsTrigger>
          <TabsTrigger value="activity">Activity</TabsTrigger>
          <TabsTrigger value="tasks">Tasks</TabsTrigger>
          <TabsTrigger value="ai">AI Insights</TabsTrigger>
        </TabsList>

        {/* ============================================================ */}
        {/* PROFILE TAB                                                  */}
        {/* ============================================================ */}
        <TabsContent value="profile" className="pt-6 space-y-8">

          {/* Card 1: Deal Identity */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between border-b border-gray-200 pb-3">
              <CardTitle className="text-base font-semibold">Deal Identity</CardTitle>
              {editingCard !== 'identity' && (
                <Button variant="ghost" size="icon" aria-label="Edit Deal Identity" onClick={() => openCard('identity')}>
                  <Pencil className="h-4 w-4" />
                </Button>
              )}
            </CardHeader>
            <CardContent className="space-y-4">
              {editingCard === 'identity' ? (
                <>
                  {/* Transaction Type */}
                  <div className="space-y-1">
                    <Label>Transaction Type</Label>
                    <RefSelect
                      category="transaction_type"
                      value={identityForm?.transaction_type_id || ''}
                      onChange={(v) => setIdentityForm((f) => ({ ...f, transaction_type_id: v }))}
                    />
                  </div>

                  {/* Fund */}
                  <div className="space-y-1">
                    <Label>Fund</Label>
                    <div className="flex gap-2 items-center">
                      <select
                        className="flex h-10 flex-1 rounded-xl border border-input bg-background px-3 text-sm"
                        value={identityForm?.fund_id || ''}
                        onChange={(e) => setIdentityForm((f) => ({ ...f, fund_id: e.target.value }))}
                      >
                        <option value="">No fund assigned</option>
                        {funds.map((fund) => (
                          <option key={fund.id} value={fund.id}>{fund.fund_name}</option>
                        ))}
                      </select>
                      <Button
                        variant="ghost"
                        size="sm"
                        type="button"
                        onClick={() => setFundModalOpen(true)}
                        className="whitespace-nowrap text-primary"
                      >
                        <Plus className="h-3.5 w-3.5 mr-1" />
                        New fund
                      </Button>
                    </div>
                  </div>

                  {/* Platform or Add-on */}
                  <div className="space-y-1">
                    <Label>Platform or Add-on</Label>
                    <select
                      className="flex h-10 w-full rounded-xl border border-input bg-background px-3 text-sm"
                      value={identityForm?.platform_or_addon || ''}
                      onChange={(e) => setIdentityForm((f) => ({ ...f, platform_or_addon: e.target.value, platform_company_id: '' }))}
                    >
                      <option value="">N/A</option>
                      <option value="platform">Platform Company</option>
                      <option value="addon">Add-on</option>
                    </select>
                  </div>

                  {/* Platform Company (only when addon) */}
                  {identityForm?.platform_or_addon === 'addon' && (
                    <div className="space-y-1">
                      <Label>Platform Company</Label>
                      <select
                        className="flex h-10 w-full rounded-xl border border-input bg-background px-3 text-sm"
                        value={identityForm?.platform_company_id || ''}
                        onChange={(e) => setIdentityForm((f) => ({ ...f, platform_company_id: e.target.value }))}
                      >
                        <option value="">Select company</option>
                        {companies.map((c) => (
                          <option key={c.id} value={c.id}>{c.name}</option>
                        ))}
                      </select>
                    </div>
                  )}

                  {/* Description */}
                  <div className="space-y-1">
                    <Label>Description</Label>
                    <Textarea
                      value={identityForm?.description || ''}
                      onChange={(e) => setIdentityForm((f) => ({ ...f, description: e.target.value }))}
                      rows={3}
                    />
                  </div>

                  {/* Legacy ID */}
                  <div className="space-y-1">
                    <Label>Legacy ID</Label>
                    <Input
                      value={identityForm?.legacy_id || ''}
                      onChange={(e) => setIdentityForm((f) => ({ ...f, legacy_id: e.target.value }))}
                    />
                  </div>

                  <CardEditFooter
                    onSave={() => updateDealMutation.mutate({
                      transaction_type_id: identityForm.transaction_type_id || null,
                      fund_id: identityForm.fund_id || null,
                      platform_or_addon: identityForm.platform_or_addon || null,
                      platform_company_id: identityForm.platform_company_id || null,
                      description: identityForm.description || null,
                      legacy_id: identityForm.legacy_id || null,
                    })}
                    onCancel={cancelCard}
                    isSaving={isSaving}
                  />
                </>
              ) : (
                <div className="space-y-3">
                  <FieldRow label="Transaction Type" value={deal.transaction_type_label} />
                  <FieldRow label="Fund" value={deal.fund_name || 'No fund assigned'} />
                  <FieldRow
                    label="Platform or Add-on"
                    value={
                      deal.platform_or_addon === 'platform'
                        ? 'Platform Company'
                        : deal.platform_or_addon === 'addon'
                          ? 'Add-on'
                          : null
                    }
                  />
                  {deal.platform_or_addon === 'addon' && (
                    <FieldRow
                      label="Platform Company"
                      value={
                        deal.platform_company_id ? (
                          <Link className="text-sm underline" to={`/companies/${deal.platform_company_id}`}>
                            {deal.platform_company_name}
                          </Link>
                        ) : null
                      }
                    />
                  )}
                  <FieldRow label="Description" value={deal.description} />
                  <FieldRow label="Legacy ID" value={deal.legacy_id} />
                </div>
              )}
            </CardContent>
          </Card>

          {/* Card 2: Financials */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between border-b border-gray-200 pb-3">
              <CardTitle className="text-base font-semibold">Financials</CardTitle>
              {editingCard !== 'financials' && (
                <Button variant="ghost" size="icon" aria-label="Edit Financials" onClick={() => openCard('financials')}>
                  <Pencil className="h-4 w-4" />
                </Button>
              )}
            </CardHeader>
            <CardContent className="space-y-4">
              {editingCard === 'financials' ? (
                <>
                  <p className="text-xs font-medium text-muted-foreground">Deal Metrics</p>
                  {[
                    { label: 'Revenue', amtKey: 'revenue_amount', curKey: 'revenue_currency' },
                    { label: 'EBITDA', amtKey: 'ebitda_amount', curKey: 'ebitda_currency' },
                    { label: 'Enterprise Value', amtKey: 'enterprise_value_amount', curKey: 'enterprise_value_currency' },
                    { label: 'Equity Investment', amtKey: 'equity_investment_amount', curKey: 'equity_investment_currency' },
                  ].map(({ label, amtKey, curKey }) => (
                    <div key={amtKey} className="space-y-1">
                      <Label>{label}</Label>
                      <div className="flex gap-2">
                        <Input
                          type="text"
                          className="w-32"
                          placeholder="Amount"
                          value={financialsForm?.[amtKey] ?? ''}
                          onChange={(e) => setFinancialsForm((f) => ({ ...f, [amtKey]: e.target.value }))}
                        />
                        <Input
                          className="w-16 uppercase"
                          maxLength={3}
                          placeholder="USD"
                          value={financialsForm?.[curKey] || ''}
                          onChange={(e) => setFinancialsForm((f) => ({ ...f, [curKey]: e.target.value.toUpperCase() }))}
                        />
                      </div>
                    </div>
                  ))}

                  <p className="text-xs font-medium text-muted-foreground mt-4">Bid Amounts</p>
                  {[
                    { label: 'IOI Bid', amtKey: 'ioi_bid_amount', curKey: 'ioi_bid_currency' },
                    { label: 'LOI Bid', amtKey: 'loi_bid_amount', curKey: 'loi_bid_currency' },
                  ].map(({ label, amtKey, curKey }) => (
                    <div key={amtKey} className="space-y-1">
                      <Label>{label}</Label>
                      <div className="flex gap-2">
                        <Input
                          type="text"
                          className="w-32"
                          placeholder="Amount"
                          value={financialsForm?.[amtKey] ?? ''}
                          onChange={(e) => setFinancialsForm((f) => ({ ...f, [amtKey]: e.target.value }))}
                        />
                        <Input
                          className="w-16 uppercase"
                          maxLength={3}
                          placeholder="USD"
                          value={financialsForm?.[curKey] || ''}
                          onChange={(e) => setFinancialsForm((f) => ({ ...f, [curKey]: e.target.value.toUpperCase() }))}
                        />
                      </div>
                    </div>
                  ))}

                  <CardEditFooter
                    onSave={() => updateDealMutation.mutate({
                      revenue_amount: financialsForm.revenue_amount !== '' ? Number(financialsForm.revenue_amount) : null,
                      revenue_currency: financialsForm.revenue_currency || null,
                      ebitda_amount: financialsForm.ebitda_amount !== '' ? Number(financialsForm.ebitda_amount) : null,
                      ebitda_currency: financialsForm.ebitda_currency || null,
                      enterprise_value_amount: financialsForm.enterprise_value_amount !== '' ? Number(financialsForm.enterprise_value_amount) : null,
                      enterprise_value_currency: financialsForm.enterprise_value_currency || null,
                      equity_investment_amount: financialsForm.equity_investment_amount !== '' ? Number(financialsForm.equity_investment_amount) : null,
                      equity_investment_currency: financialsForm.equity_investment_currency || null,
                      ioi_bid_amount: financialsForm.ioi_bid_amount !== '' ? Number(financialsForm.ioi_bid_amount) : null,
                      ioi_bid_currency: financialsForm.ioi_bid_currency || null,
                      loi_bid_amount: financialsForm.loi_bid_amount !== '' ? Number(financialsForm.loi_bid_amount) : null,
                      loi_bid_currency: financialsForm.loi_bid_currency || null,
                    })}
                    onCancel={cancelCard}
                    isSaving={isSaving}
                  />
                </>
              ) : (
                <div className="space-y-4">
                  <p className="text-xs font-medium text-muted-foreground">Deal Metrics</p>
                  <div className="space-y-2">
                    {[
                      { label: 'Revenue', amt: deal.revenue_amount, cur: deal.revenue_currency },
                      { label: 'EBITDA', amt: deal.ebitda_amount, cur: deal.ebitda_currency },
                      { label: 'Enterprise Value', amt: deal.enterprise_value_amount, cur: deal.enterprise_value_currency },
                      { label: 'Equity Investment', amt: deal.equity_investment_amount, cur: deal.equity_investment_currency },
                    ].map(({ label, amt, cur }) => (
                      <FieldRow key={label} label={label} value={fmtAmount(amt, cur)} />
                    ))}
                  </div>
                  <p className="text-xs font-medium text-muted-foreground">Bid Amounts</p>
                  <div className="space-y-2">
                    {[
                      { label: 'IOI Bid', amt: deal.ioi_bid_amount, cur: deal.ioi_bid_currency },
                      { label: 'LOI Bid', amt: deal.loi_bid_amount, cur: deal.loi_bid_currency },
                    ].map(({ label, amt, cur }) => (
                      <FieldRow key={label} label={label} value={fmtAmount(amt, cur)} />
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Card 3: Process Milestones */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between border-b border-gray-200 pb-3">
              <CardTitle className="text-base font-semibold">Process Milestones</CardTitle>
              {editingCard !== 'milestones' && (
                <Button variant="ghost" size="icon" aria-label="Edit Process Milestones" onClick={() => openCard('milestones')}>
                  <Pencil className="h-4 w-4" />
                </Button>
              )}
            </CardHeader>
            <CardContent>
              {editingCard === 'milestones' ? (
                <>
                  <div className="grid grid-cols-2 gap-x-8 gap-y-3">
                    {[
                      { label: 'New Deal Date', key: 'new_deal_date' },
                      { label: 'CIM Received', key: 'cim_received_date' },
                      { label: 'IOI Due', key: 'ioi_due_date' },
                      { label: 'IOI Submitted', key: 'ioi_submitted_date' },
                      { label: 'Mgmt Presentation', key: 'management_presentation_date' },
                      { label: 'LOI Due', key: 'loi_due_date' },
                      { label: 'LOI Submitted', key: 'loi_submitted_date' },
                      { label: 'Live Diligence', key: 'live_diligence_date' },
                      { label: 'Portfolio Company', key: 'portfolio_company_date' },
                    ].map(({ label, key }) => (
                      <div key={key} className="space-y-1">
                        <Label className="text-sm text-muted-foreground">{label}</Label>
                        <Input
                          type="date"
                          value={milestonesForm?.[key] || ''}
                          onChange={(e) => setMilestonesForm((f) => ({ ...f, [key]: e.target.value }))}
                        />
                      </div>
                    ))}
                  </div>
                  <CardEditFooter
                    onSave={() => updateDealMutation.mutate({
                      new_deal_date: milestonesForm.new_deal_date || null,
                      cim_received_date: milestonesForm.cim_received_date || null,
                      ioi_due_date: milestonesForm.ioi_due_date || null,
                      ioi_submitted_date: milestonesForm.ioi_submitted_date || null,
                      management_presentation_date: milestonesForm.management_presentation_date || null,
                      loi_due_date: milestonesForm.loi_due_date || null,
                      loi_submitted_date: milestonesForm.loi_submitted_date || null,
                      live_diligence_date: milestonesForm.live_diligence_date || null,
                      portfolio_company_date: milestonesForm.portfolio_company_date || null,
                    })}
                    onCancel={cancelCard}
                    isSaving={isSaving}
                  />
                </>
              ) : (
                <div className="grid grid-cols-2 gap-x-8 gap-y-3">
                  {[
                    { label: 'New Deal Date', val: deal.new_deal_date },
                    { label: 'CIM Received', val: deal.cim_received_date },
                    { label: 'IOI Due', val: deal.ioi_due_date },
                    { label: 'IOI Submitted', val: deal.ioi_submitted_date },
                    { label: 'Mgmt Presentation', val: deal.management_presentation_date },
                    { label: 'LOI Due', val: deal.loi_due_date },
                    { label: 'LOI Submitted', val: deal.loi_submitted_date },
                    { label: 'Live Diligence', val: deal.live_diligence_date },
                    { label: 'Portfolio Company', val: deal.portfolio_company_date },
                  ].filter(({ label }) => label).map(({ label, val }) => (
                    <FieldRow key={label} label={label} value={fmtDate(val)} />
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Card 4: Source & Team */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between border-b border-gray-200 pb-3">
              <CardTitle className="text-base font-semibold">Source &amp; Team</CardTitle>
              {editingCard !== 'sourceTeam' && (
                <Button variant="ghost" size="icon" aria-label="Edit Source and Team" onClick={() => openCard('sourceTeam')}>
                  <Pencil className="h-4 w-4" />
                </Button>
              )}
            </CardHeader>
            <CardContent className="space-y-4">
              {editingCard === 'sourceTeam' ? (
                <>
                  {/* Deal Team */}
                  <div className="space-y-2">
                    <Label>Deal Team</Label>
                    <div className="flex flex-wrap gap-2 mb-2">
                      {(sourceTeamForm?.deal_team || []).map((u) => (
                        <Badge key={u.id} variant="secondary" className="gap-1">
                          {u.name}
                          <button
                            type="button"
                            onClick={() => setSourceTeamForm((f) => ({
                              ...f,
                              deal_team: f.deal_team.filter((m) => m.id !== u.id),
                            }))}
                            className="ml-1 hover:text-destructive"
                          >
                            <X className="h-3 w-3" />
                          </button>
                        </Badge>
                      ))}
                    </div>
                    <select
                      className="flex h-10 w-full rounded-xl border border-input bg-background px-3 text-sm"
                      value=""
                      onChange={(e) => {
                        const userId = e.target.value;
                        if (!userId) return;
                        const user = users.find((u) => u.id === userId);
                        if (!user) return;
                        const currentTeam = sourceTeamForm?.deal_team || [];
                        if (currentTeam.some((m) => m.id === userId)) return;
                        setSourceTeamForm((f) => ({
                          ...f,
                          deal_team: [...currentTeam, { id: user.id, name: user.full_name || user.name || user.email }],
                        }));
                      }}
                    >
                      <option value="">Add team member…</option>
                      {users.map((u) => (
                        <option key={u.id} value={u.id}>{u.full_name || u.name || u.email}</option>
                      ))}
                    </select>
                  </div>

                  {/* Originator */}
                  <div className="space-y-1">
                    <Label>Originator</Label>
                    <select
                      className="flex h-10 w-full rounded-xl border border-input bg-background px-3 text-sm"
                      value={sourceTeamForm?.originator_id || ''}
                      onChange={(e) => setSourceTeamForm((f) => ({ ...f, originator_id: e.target.value }))}
                    >
                      <option value="">None</option>
                      {users.map((u) => (
                        <option key={u.id} value={u.id}>{u.full_name || u.name || u.email}</option>
                      ))}
                    </select>
                  </div>

                  {/* Source Type */}
                  <div className="space-y-1">
                    <Label>Source Type</Label>
                    <RefSelect
                      category="deal_source_type"
                      value={sourceTeamForm?.source_type_id || ''}
                      onChange={(v) => setSourceTeamForm((f) => ({ ...f, source_type_id: v }))}
                    />
                  </div>

                  {/* Source Company */}
                  <div className="space-y-1">
                    <Label>Source Company</Label>
                    <select
                      className="flex h-10 w-full rounded-xl border border-input bg-background px-3 text-sm"
                      value={sourceTeamForm?.source_company_id || ''}
                      onChange={(e) => setSourceTeamForm((f) => ({ ...f, source_company_id: e.target.value }))}
                    >
                      <option value="">None</option>
                      {companies.map((c) => (
                        <option key={c.id} value={c.id}>{c.name}</option>
                      ))}
                    </select>
                  </div>

                  {/* Source Individual */}
                  <div className="space-y-1">
                    <Label>Source Individual</Label>
                    <select
                      className="flex h-10 w-full rounded-xl border border-input bg-background px-3 text-sm"
                      value={sourceTeamForm?.source_individual_id || ''}
                      onChange={(e) => setSourceTeamForm((f) => ({ ...f, source_individual_id: e.target.value }))}
                    >
                      <option value="">None</option>
                      {contacts.map((c) => (
                        <option key={c.id} value={c.id}>{c.first_name} {c.last_name}</option>
                      ))}
                    </select>
                  </div>

                  <CardEditFooter
                    onSave={() => updateDealMutation.mutate({
                      deal_team: sourceTeamForm.deal_team.map((u) => u.id),
                      originator_id: sourceTeamForm.originator_id || null,
                      source_type_id: sourceTeamForm.source_type_id || null,
                      source_company_id: sourceTeamForm.source_company_id || null,
                      source_individual_id: sourceTeamForm.source_individual_id || null,
                    })}
                    onCancel={cancelCard}
                    isSaving={isSaving}
                  />
                </>
              ) : (
                <div className="space-y-3">
                  <FieldRow
                    label="Deal Team"
                    value={
                      (deal.deal_team || []).length > 0 ? (
                        <div className="flex flex-wrap gap-2">
                          {deal.deal_team.map((u) => (
                            <Badge key={u.id} variant="secondary">{u.name}</Badge>
                          ))}
                        </div>
                      ) : null
                    }
                  />
                  <FieldRow label="Originator" value={deal.originator_name} />
                  <FieldRow label="Source Type" value={deal.source_type_label} />
                  <FieldRow
                    label="Source Company"
                    value={
                      deal.source_company_id ? (
                        <Link className="text-sm underline" to={`/companies/${deal.source_company_id}`}>
                          {deal.source_company_name}
                        </Link>
                      ) : null
                    }
                  />
                  <FieldRow label="Source Individual" value={deal.source_individual_name} />
                </div>
              )}
            </CardContent>
          </Card>

          {/* Card 5: Passed / Dead */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between border-b border-gray-200 pb-3">
              <CardTitle className="text-base font-semibold">Passed / Dead</CardTitle>
              {editingCard !== 'passedDead' && (
                <Button variant="ghost" size="icon" aria-label="Edit Passed Dead" onClick={() => openCard('passedDead')}>
                  <Pencil className="h-4 w-4" />
                </Button>
              )}
            </CardHeader>
            <CardContent className="space-y-4">
              {editingCard === 'passedDead' ? (
                <>
                  <div className="space-y-1">
                    <Label>Passed / Dead Date</Label>
                    <Input
                      type="date"
                      value={passedDeadForm?.passed_dead_date || ''}
                      onChange={(e) => setPassedDeadForm((f) => ({ ...f, passed_dead_date: e.target.value }))}
                    />
                  </div>

                  <div className="space-y-1">
                    <Label>Reasons</Label>
                    <RefSelect
                      category="passed_dead_reason"
                      value={passedDeadForm?.passed_dead_reasons?.[0] || ''}
                      onChange={(v) => {
                        if (!v) return;
                        setPassedDeadForm((f) => {
                          const current = f.passed_dead_reasons || [];
                          if (current.includes(v)) return f;
                          return { ...f, passed_dead_reasons: [...current, v] };
                        });
                      }}
                    />
                    <div className="flex flex-wrap gap-2 mt-2">
                      {(passedDeadForm?.passed_dead_reasons || []).map((reasonId) => (
                        <Badge key={reasonId} variant="secondary" className="gap-1">
                          {reasonId}
                          <button
                            type="button"
                            onClick={() => setPassedDeadForm((f) => ({
                              ...f,
                              passed_dead_reasons: f.passed_dead_reasons.filter((r) => r !== reasonId),
                            }))}
                            className="ml-1 hover:text-destructive"
                          >
                            <X className="h-3 w-3" />
                          </button>
                        </Badge>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-1">
                    <Label>Commentary</Label>
                    <Textarea
                      value={passedDeadForm?.passed_dead_commentary || ''}
                      onChange={(e) => setPassedDeadForm((f) => ({ ...f, passed_dead_commentary: e.target.value }))}
                      rows={3}
                    />
                  </div>

                  <CardEditFooter
                    onSave={() => updateDealMutation.mutate({
                      passed_dead_date: passedDeadForm.passed_dead_date || null,
                      passed_dead_reasons: passedDeadForm.passed_dead_reasons,
                      passed_dead_commentary: passedDeadForm.passed_dead_commentary || null,
                    })}
                    onCancel={cancelCard}
                    isSaving={isSaving}
                  />
                </>
              ) : (
                <div className="space-y-3">
                  {!deal.passed_dead_date && !(deal.passed_dead_reasons?.length) && !deal.passed_dead_commentary ? (
                    <p className="text-sm text-muted-foreground">No passed/dead information recorded</p>
                  ) : (
                    <div className="space-y-3">
                      <FieldRow label="Passed / Dead Date" value={fmtDate(deal.passed_dead_date)} />
                      <FieldRow
                        label="Reasons"
                        value={
                          (deal.passed_dead_reasons || []).length > 0 ? (
                            <div className="flex flex-wrap gap-2">
                              {deal.passed_dead_reasons.map((r) => (
                                <Badge key={r} variant="secondary">{r}</Badge>
                              ))}
                            </div>
                          ) : null
                        }
                      />
                      <FieldRow label="Commentary" value={deal.passed_dead_commentary} />
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ============================================================ */}
        {/* COUNTERPARTIES TAB                                          */}
        {/* ============================================================ */}
        <TabsContent value="counterparties" className="pt-6">
          <CounterpartiesTab dealId={id} companies={companiesQuery.data?.items || []} />
        </TabsContent>

        {/* ============================================================ */}
        {/* FUNDING TAB                                                  */}
        {/* ============================================================ */}
        <TabsContent value="funding" className="pt-6">
          <FundingTab dealId={id} companies={companiesQuery.data?.items || []} />
        </TabsContent>

        {/* ============================================================ */}
        {/* ACTIVITY TAB                                                 */}
        {/* ============================================================ */}
        <TabsContent value="activity" className="pt-6">
          <Card>
            <CardHeader className="border-b border-gray-200 pb-3"><CardTitle>Activity timeline</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap gap-2">
                {['call', 'email', 'meeting', 'note', 'linkedin_message'].map((type) => (
                  <Button key={type} variant="outline" size="sm" onClick={() => setDraftTitle(type)}>
                    {type}
                  </Button>
                ))}
              </div>
              <Input placeholder="Activity title" value={draftTitle} onChange={(e) => setDraftTitle(e.target.value)} />
              <Textarea placeholder="Notes" value={draftBody} onChange={(e) => setDraftBody(e.target.value)} />
              <Button onClick={() => logMutation.mutate({
                activity_type: draftTitle || 'note',
                title: draftTitle || 'Note',
                body: draftBody,
                occurred_at: new Date().toISOString(),
              })}>
                Log activity
              </Button>
              <div className="space-y-3">
                {(activitiesQuery.data?.items || []).length > 0 ? (
                  (activitiesQuery.data?.items || []).map((item) => (
                    <div key={item.id} className="rounded-xl bg-muted/40 px-4 py-3">
                      <div className="mb-2 flex items-center justify-between">
                        <Badge>{item.activity_type}</Badge>
                        <span className="text-xs text-muted-foreground">{formatDate(item.occurred_at)}</span>
                      </div>
                      <p className="font-medium">{item.title}</p>
                      <p className="text-sm text-muted-foreground">{item.body}</p>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-muted-foreground">No activity recorded yet. Log the first activity above.</p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ============================================================ */}
        {/* AI INSIGHTS TAB                                              */}
        {/* ============================================================ */}
        <TabsContent value="ai" className="pt-6">
          <DealScoreCard dealId={id} />
        </TabsContent>

        {/* ============================================================ */}
        {/* TASKS TAB                                                    */}
        {/* ============================================================ */}
        <TabsContent value="tasks" className="pt-6">
          <Card>
            <CardHeader className="border-b border-gray-200 pb-3"><CardTitle>Tasks</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              {(tasksQuery.data || []).length > 0 ? (
                (tasksQuery.data || []).map((task) => (
                  <div key={task.id} className="rounded-xl bg-muted/40 p-3">
                    <p className="font-medium">{task.title}</p>
                    <p className="text-xs text-muted-foreground">{task.priority} • {task.status}</p>
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">No tasks linked to this deal.</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* ============================================================ */}
      {/* FUND QUICK-CREATE MODAL                                      */}
      {/* ============================================================ */}
      <Dialog open={fundModalOpen} onOpenChange={setFundModalOpen}>
        <DialogContent className="max-w-md p-6">
          <DialogHeader>
            <DialogTitle>Create Fund</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-1">
              <Label>Fund Name *</Label>
              <Input
                value={fundForm.fund_name}
                onChange={(e) => setFundForm((f) => ({ ...f, fund_name: e.target.value }))}
                placeholder="e.g. TWG Fund IV"
              />
            </div>
            <div className="space-y-1">
              <Label>Fundraise Status</Label>
              <RefSelect
                category="fund_status"
                value={fundForm.fundraise_status_id}
                onChange={(v) => setFundForm((f) => ({ ...f, fundraise_status_id: v }))}
              />
            </div>
            <div className="space-y-1">
              <Label>Target Fund Size</Label>
              <div className="flex gap-2">
                <Input
                  type="text"
                  className="w-32"
                  placeholder="Amount"
                  value={fundForm.target_fund_size_amount}
                  onChange={(e) => setFundForm((f) => ({ ...f, target_fund_size_amount: e.target.value }))}
                />
                <Input
                  className="w-16 uppercase"
                  maxLength={3}
                  placeholder="USD"
                  value={fundForm.target_fund_size_currency}
                  onChange={(e) => setFundForm((f) => ({ ...f, target_fund_size_currency: e.target.value.toUpperCase() }))}
                />
              </div>
            </div>
            <div className="space-y-1">
              <Label>Vintage Year</Label>
              <Input
                type="number"
                min={1900}
                max={2100}
                placeholder="e.g. 2024"
                value={fundForm.vintage_year}
                onChange={(e) => setFundForm((f) => ({ ...f, vintage_year: e.target.value }))}
              />
            </div>
          </div>
          <div className="flex justify-end gap-2 mt-4">
            <Button variant="ghost" onClick={() => setFundModalOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => createFundMutation.mutate({
                fund_name: fundForm.fund_name,
                fundraise_status_id: fundForm.fundraise_status_id || null,
                target_fund_size_amount: fundForm.target_fund_size_amount ? Number(fundForm.target_fund_size_amount) : null,
                target_fund_size_currency: fundForm.target_fund_size_currency || null,
                vintage_year: fundForm.vintage_year ? Number(fundForm.vintage_year) : null,
              })}
              disabled={!fundForm.fund_name || createFundMutation.isPending}
            >
              {createFundMutation.isPending ? 'Creating…' : 'Create Fund'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
