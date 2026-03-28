import { useState, useMemo } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Pencil, X, Plus } from 'lucide-react';
import { toast } from 'sonner';
import { getDeal, getDealActivities, logActivity, scoreDeal, updateDeal } from '@/api/deals';
import { getFunds, createFund } from '@/api/funds';
import { getUsers } from '@/api/users';
import { getCompanies } from '@/api/companies';
import { getContacts } from '@/api/contacts';
import { getBoards, getBoard } from '@/api/boards';
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
      <CardHeader><CardTitle>AI Insights</CardTitle></CardHeader>
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
        <TabsList>
          <TabsTrigger value="profile">Profile</TabsTrigger>
          <TabsTrigger value="activity">Activity</TabsTrigger>
          <TabsTrigger value="ai">AI Insights</TabsTrigger>
          <TabsTrigger value="tasks">Tasks</TabsTrigger>
        </TabsList>

        {/* ============================================================ */}
        {/* PROFILE TAB                                                  */}
        {/* ============================================================ */}
        <TabsContent value="profile" className="pt-6 space-y-8">

          {/* Card 1: Deal Identity */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
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
                  <div>
                    <p className="text-sm text-muted-foreground">Transaction Type</p>
                    <p className="text-sm">{fmt(deal.transaction_type_label)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Fund</p>
                    <p className="text-sm">{deal.fund_name || 'No fund assigned'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Platform or Add-on</p>
                    <p className="text-sm">
                      {deal.platform_or_addon === 'platform' ? 'Platform Company' : deal.platform_or_addon === 'addon' ? 'Add-on' : '—'}
                    </p>
                  </div>
                  {deal.platform_or_addon === 'addon' && (
                    <div>
                      <p className="text-sm text-muted-foreground">Platform Company</p>
                      {deal.platform_company_id ? (
                        <Link className="text-sm underline" to={`/companies/${deal.platform_company_id}`}>
                          {deal.platform_company_name}
                        </Link>
                      ) : (
                        <p className="text-sm">—</p>
                      )}
                    </div>
                  )}
                  <div>
                    <p className="text-sm text-muted-foreground">Description</p>
                    <p className="text-sm">{fmt(deal.description)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Legacy ID</p>
                    <p className="text-sm">{fmt(deal.legacy_id)}</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Card 2: Financials */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
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
                      <div key={label}>
                        <p className="text-sm text-muted-foreground">{label}</p>
                        <p className="text-sm">{fmtAmount(amt, cur)}</p>
                      </div>
                    ))}
                  </div>
                  <p className="text-xs font-medium text-muted-foreground">Bid Amounts</p>
                  <div className="space-y-2">
                    {[
                      { label: 'IOI Bid', amt: deal.ioi_bid_amount, cur: deal.ioi_bid_currency },
                      { label: 'LOI Bid', amt: deal.loi_bid_amount, cur: deal.loi_bid_currency },
                    ].map(({ label, amt, cur }) => (
                      <div key={label}>
                        <p className="text-sm text-muted-foreground">{label}</p>
                        <p className="text-sm">{fmtAmount(amt, cur)}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Card 3: Process Milestones */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
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
                    { label: '', val: null },
                  ].map(({ label, val }, i) => (
                    <div key={i}>
                      <p className="text-sm text-muted-foreground">{label}</p>
                      {label && <p className="text-sm">{fmtDate(val)}</p>}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Card 4: Source & Team */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
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
                  <div>
                    <p className="text-sm text-muted-foreground">Deal Team</p>
                    {(deal.deal_team || []).length > 0 ? (
                      <div className="flex flex-wrap gap-2 mt-1">
                        {deal.deal_team.map((u) => (
                          <Badge key={u.id} variant="secondary">{u.name}</Badge>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm">No team members assigned</p>
                    )}
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Originator</p>
                    <p className="text-sm">{fmt(deal.originator_name)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Source Type</p>
                    <p className="text-sm">{fmt(deal.source_type_label)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Source Company</p>
                    {deal.source_company_id ? (
                      <Link className="text-sm underline" to={`/companies/${deal.source_company_id}`}>
                        {deal.source_company_name}
                      </Link>
                    ) : (
                      <p className="text-sm">—</p>
                    )}
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Source Individual</p>
                    <p className="text-sm">{fmt(deal.source_individual_name)}</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Card 5: Passed / Dead */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
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
                    <>
                      <div>
                        <p className="text-sm text-muted-foreground">Passed / Dead Date</p>
                        <p className="text-sm">{fmtDate(deal.passed_dead_date)}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Reasons</p>
                        {(deal.passed_dead_reasons || []).length > 0 ? (
                          <div className="flex flex-wrap gap-2 mt-1">
                            {deal.passed_dead_reasons.map((r) => (
                              <Badge key={r} variant="secondary">{r}</Badge>
                            ))}
                          </div>
                        ) : (
                          <p className="text-sm">—</p>
                        )}
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Commentary</p>
                        <p className="text-sm">{fmt(deal.passed_dead_commentary)}</p>
                      </div>
                    </>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ============================================================ */}
        {/* ACTIVITY TAB                                                 */}
        {/* ============================================================ */}
        <TabsContent value="activity" className="pt-6">
          <Card>
            <CardHeader><CardTitle>Activity timeline</CardTitle></CardHeader>
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
            <CardHeader><CardTitle>Tasks</CardTitle></CardHeader>
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
