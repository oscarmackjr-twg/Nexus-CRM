import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useParams } from 'react-router-dom';
import { toast } from 'sonner';
import { Edit3, X } from 'lucide-react';
import { getCompany, getCompanyContacts, getCompanyDeals, updateCompany, syncCompanyLinkedIn } from '@/api/companies';
import { getUsers } from '@/api/users';
import { getRefData } from '@/api/refData';
import LinkedInPanel from '@/components/LinkedInPanel';
import { RefSelect } from '@/components/RefSelect';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { formatCurrency, formatDate } from '@/lib/utils';

export default function CompanyDetailPage() {
  const { id } = useParams();
  const queryClient = useQueryClient();

  // Per-card editing state
  const [editingIdentity, setEditingIdentity] = useState(false);
  const [editingProfile, setEditingProfile] = useState(false);
  const [editingInternal, setEditingInternal] = useState(false);

  // Form values for each card
  const [identityForm, setIdentityForm] = useState({});
  const [profileForm, setProfileForm] = useState({});
  const [internalForm, setInternalForm] = useState({});

  // Multi-select JSONB fields
  const [subTypes, setSubTypes] = useState([]);
  const [transactionTypes, setTransactionTypes] = useState([]);
  const [sectorPrefs, setSectorPrefs] = useState([]);
  const [subSectorPrefs, setSubSectorPrefs] = useState([]);

  // Data queries
  const { data: company, isLoading } = useQuery({
    queryKey: ['company', id],
    queryFn: () => getCompany(id),
  });
  const { data: contacts } = useQuery({
    queryKey: ['company', id, 'contacts'],
    queryFn: () => getCompanyContacts(id),
  });
  const { data: deals } = useQuery({
    queryKey: ['company', id, 'deals'],
    queryFn: () => getCompanyDeals(id),
  });
  const { data: users } = useQuery({
    queryKey: ['users'],
    queryFn: getUsers,
  });

  // Ref data for resolving JSONB UUID arrays to labels
  const { data: companySubTypeOptions } = useQuery({
    queryKey: ['ref', 'company_sub_type'],
    queryFn: () => getRefData('company_sub_type'),
  });
  const { data: sectorOptions } = useQuery({
    queryKey: ['ref', 'sector'],
    queryFn: () => getRefData('sector'),
  });
  const { data: subSectorOptions } = useQuery({
    queryKey: ['ref', 'sub_sector'],
    queryFn: () => getRefData('sub_sector'),
  });
  const { data: transactionTypeOptions } = useQuery({
    queryKey: ['ref', 'transaction_type'],
    queryFn: () => getRefData('transaction_type'),
  });

  const syncMutation = useMutation({
    mutationFn: () => syncCompanyLinkedIn(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['company', id] });
      toast.success('Company synced with LinkedIn');
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data) => updateCompany(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['company', id] });
      toast.success('Company updated');
      setEditingIdentity(false);
      setEditingProfile(false);
      setEditingInternal(false);
    },
    onError: () => {
      toast.error('Could not save changes. Check your connection and try again.');
    },
  });

  // Initialize form state from company data
  useEffect(() => {
    if (company) {
      setIdentityForm({
        company_type_id: company.company_type_id || '',
        tier_id: company.tier_id || '',
        sector_id: company.sector_id || '',
        sub_sector_id: company.sub_sector_id || '',
        description: company.description || '',
        main_phone: company.main_phone || '',
        parent_company_id: company.parent_company_id || '',
        address: company.address || '',
        city: company.city || '',
        state: company.state || '',
        postal_code: company.postal_code || '',
        country: company.country || '',
      });
      setProfileForm({
        aum_amount: company.aum_amount || '',
        aum_currency: company.aum_currency || '',
        ebitda_amount: company.ebitda_amount || '',
        ebitda_currency: company.ebitda_currency || '',
        min_ebitda: company.min_ebitda || '',
        max_ebitda: company.max_ebitda || '',
        ebitda_range_currency: company.ebitda_range_currency || '',
        typical_bite_size_low: company.typical_bite_size_low || '',
        typical_bite_size_high: company.typical_bite_size_high || '',
        bite_size_currency: company.bite_size_currency || '',
        co_invest: company.co_invest || false,
        preference_notes: company.preference_notes || '',
      });
      setInternalForm({
        watchlist: company.watchlist || false,
        coverage_person_id: company.coverage_person_id || '',
        contact_frequency: company.contact_frequency || '',
        legacy_id: company.legacy_id || '',
      });
      setSubTypes(company.company_sub_type_ids || []);
      setSectorPrefs(company.sector_preferences || []);
      setSubSectorPrefs(company.sub_sector_preferences || []);
      setTransactionTypes(company.transaction_types || []);
    }
  }, [company]);

  const resolveLabel = (options, id) => options?.find((o) => o.id === id)?.label || id;

  const setIdentityField = (field, value) => setIdentityForm((f) => ({ ...f, [field]: value }));
  const setProfileField = (field, value) => setProfileForm((f) => ({ ...f, [field]: value }));
  const setInternalField = (field, value) => setInternalForm((f) => ({ ...f, [field]: value }));

  const handleSaveIdentity = () => {
    updateMutation.mutate({
      ...identityForm,
      company_sub_type_ids: subTypes,
    });
  };

  const handleSaveProfile = () => {
    updateMutation.mutate({
      ...profileForm,
      transaction_types: transactionTypes,
      sector_preferences: sectorPrefs,
      sub_sector_preferences: subSectorPrefs,
    });
  };

  const handleSaveInternal = () => {
    updateMutation.mutate(internalForm);
  };

  if (isLoading) return <Skeleton className="h-[620px] w-full" />;

  return (
    <div className="space-y-6">
      {/* Primary visual anchor */}
      <div className="flex items-center gap-3">
        <h1 className="text-3xl font-semibold">{company.name}</h1>
        {internalForm.watchlist && (
          <Badge variant="accent">Watchlist</Badge>
        )}
      </div>

      <Tabs defaultValue="profile" className="space-y-4">
        <TabsList>
          <TabsTrigger value="profile">Profile</TabsTrigger>
          <TabsTrigger value="contacts">Contacts</TabsTrigger>
          <TabsTrigger value="deals">Deals</TabsTrigger>
          <TabsTrigger value="linkedin">LinkedIn</TabsTrigger>
        </TabsList>

        {/* Profile Tab */}
        <TabsContent value="profile" className="space-y-4">

          {/* Card 1 — Identity */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle>Identity</CardTitle>
              <Button
                variant="ghost"
                size="icon"
                aria-label="Edit Identity"
                onClick={() => setEditingIdentity((v) => !v)}
              >
                <Edit3 className="h-4 w-4" />
              </Button>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="space-y-2">
                <Label>Company type</Label>
                <RefSelect
                  category="company_type"
                  value={identityForm.company_type_id}
                  onChange={(v) => setIdentityField('company_type_id', v)}
                  placeholder="Select company type..."
                  disabled={!editingIdentity}
                />
              </div>

              <div className="space-y-2">
                <Label>Company sub-types</Label>
                <div className="flex flex-wrap gap-2">
                  {subTypes.map((subTypeId) => (
                    <Badge key={subTypeId} className="flex items-center gap-1">
                      {resolveLabel(companySubTypeOptions, subTypeId)}
                      {editingIdentity && (
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-4 w-4 p-0"
                          aria-label={`Remove ${resolveLabel(companySubTypeOptions, subTypeId)}`}
                          onClick={() => setSubTypes((s) => s.filter((x) => x !== subTypeId))}
                        >
                          <X className="h-3 w-3" />
                        </Button>
                      )}
                    </Badge>
                  ))}
                </div>
                {editingIdentity && (
                  <RefSelect
                    category="company_sub_type"
                    value=""
                    placeholder="Add sub-type..."
                    onChange={(v) => {
                      if (v && !subTypes.includes(v)) setSubTypes((s) => [...s, v]);
                    }}
                  />
                )}
              </div>

              <div className="space-y-2">
                <Label>Tier</Label>
                <RefSelect
                  category="tier"
                  value={identityForm.tier_id}
                  onChange={(v) => setIdentityField('tier_id', v)}
                  placeholder="Select tier..."
                  disabled={!editingIdentity}
                />
              </div>

              <div className="space-y-2">
                <Label>Sector</Label>
                <RefSelect
                  category="sector"
                  value={identityForm.sector_id}
                  onChange={(v) => setIdentityField('sector_id', v)}
                  placeholder="Select sector..."
                  disabled={!editingIdentity}
                />
              </div>

              <div className="space-y-2">
                <Label>Sub-sector</Label>
                <RefSelect
                  category="sub_sector"
                  value={identityForm.sub_sector_id}
                  onChange={(v) => setIdentityField('sub_sector_id', v)}
                  placeholder="Select sub-sector..."
                  disabled={!editingIdentity}
                />
              </div>

              <div className="space-y-2">
                <Label>Description</Label>
                <Textarea
                  rows={3}
                  value={identityForm.description}
                  onChange={(e) => setIdentityField('description', e.target.value)}
                  disabled={!editingIdentity}
                />
              </div>

              <div className="space-y-2">
                <Label>Main phone</Label>
                <Input
                  type="tel"
                  value={identityForm.main_phone}
                  onChange={(e) => setIdentityField('main_phone', e.target.value)}
                  disabled={!editingIdentity}
                />
              </div>

              <div className="space-y-2">
                <Label>Parent company</Label>
                <Input
                  placeholder="Search parent company..."
                  value={identityForm.parent_company_id}
                  onChange={(e) => setIdentityField('parent_company_id', e.target.value)}
                  disabled={!editingIdentity}
                />
              </div>

              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Address</p>

              <div className="space-y-2">
                <Label>Street address</Label>
                <Input
                  value={identityForm.address}
                  onChange={(e) => setIdentityField('address', e.target.value)}
                  disabled={!editingIdentity}
                />
              </div>

              <div className="flex gap-2">
                <div className="flex-1 space-y-2">
                  <Label>City</Label>
                  <Input
                    value={identityForm.city}
                    onChange={(e) => setIdentityField('city', e.target.value)}
                    disabled={!editingIdentity}
                  />
                </div>
                <div className="flex-1 space-y-2">
                  <Label>State</Label>
                  <Input
                    value={identityForm.state}
                    onChange={(e) => setIdentityField('state', e.target.value)}
                    disabled={!editingIdentity}
                  />
                </div>
              </div>

              <div className="flex gap-2">
                <div className="flex-1 space-y-2">
                  <Label>Postal code</Label>
                  <Input
                    value={identityForm.postal_code}
                    onChange={(e) => setIdentityField('postal_code', e.target.value)}
                    disabled={!editingIdentity}
                  />
                </div>
                <div className="flex-1 space-y-2">
                  <Label>Country</Label>
                  <Input
                    value={identityForm.country}
                    onChange={(e) => setIdentityField('country', e.target.value)}
                    disabled={!editingIdentity}
                  />
                </div>
              </div>

              {editingIdentity && (
                <Button
                  className="w-full"
                  onClick={handleSaveIdentity}
                  disabled={updateMutation.isPending}
                >
                  Save changes
                </Button>
              )}
            </CardContent>
          </Card>

          {/* Card 2 — Investment Profile */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle>Investment Profile</CardTitle>
              <Button
                variant="ghost"
                size="icon"
                aria-label="Edit Investment Profile"
                onClick={() => setEditingProfile((v) => !v)}
              >
                <Edit3 className="h-4 w-4" />
              </Button>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">AUM &amp; Financials</p>

              <div className="space-y-2">
                <Label>AUM</Label>
                <div className="flex gap-2">
                  <Input
                    type="number"
                    className="flex-1"
                    placeholder="Amount"
                    value={profileForm.aum_amount}
                    onChange={(e) => setProfileField('aum_amount', e.target.value)}
                    disabled={!editingProfile}
                  />
                  <Input
                    className="w-16"
                    maxLength={3}
                    placeholder="USD"
                    value={profileForm.aum_currency}
                    onChange={(e) => setProfileField('aum_currency', e.target.value)}
                    disabled={!editingProfile}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>EBITDA</Label>
                <div className="flex gap-2">
                  <Input
                    type="number"
                    className="flex-1"
                    placeholder="Amount"
                    value={profileForm.ebitda_amount}
                    onChange={(e) => setProfileField('ebitda_amount', e.target.value)}
                    disabled={!editingProfile}
                  />
                  <Input
                    className="w-16"
                    maxLength={3}
                    placeholder="USD"
                    value={profileForm.ebitda_currency}
                    onChange={(e) => setProfileField('ebitda_currency', e.target.value)}
                    disabled={!editingProfile}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>EBITDA range</Label>
                <div className="flex gap-2">
                  <Input
                    type="number"
                    className="flex-1"
                    placeholder="Min"
                    value={profileForm.min_ebitda}
                    onChange={(e) => setProfileField('min_ebitda', e.target.value)}
                    disabled={!editingProfile}
                  />
                  <Input
                    type="number"
                    className="flex-1"
                    placeholder="Max"
                    value={profileForm.max_ebitda}
                    onChange={(e) => setProfileField('max_ebitda', e.target.value)}
                    disabled={!editingProfile}
                  />
                  <Input
                    className="w-16"
                    maxLength={3}
                    placeholder="USD"
                    value={profileForm.ebitda_range_currency}
                    onChange={(e) => setProfileField('ebitda_range_currency', e.target.value)}
                    disabled={!editingProfile}
                  />
                </div>
              </div>

              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Deal preferences</p>

              <div className="space-y-2">
                <Label>Typical bite size</Label>
                <div className="flex gap-2">
                  <Input
                    type="number"
                    className="flex-1"
                    placeholder="Low"
                    value={profileForm.typical_bite_size_low}
                    onChange={(e) => setProfileField('typical_bite_size_low', e.target.value)}
                    disabled={!editingProfile}
                  />
                  <Input
                    type="number"
                    className="flex-1"
                    placeholder="High"
                    value={profileForm.typical_bite_size_high}
                    onChange={(e) => setProfileField('typical_bite_size_high', e.target.value)}
                    disabled={!editingProfile}
                  />
                  <Input
                    className="w-16"
                    maxLength={3}
                    placeholder="USD"
                    value={profileForm.bite_size_currency}
                    onChange={(e) => setProfileField('bite_size_currency', e.target.value)}
                    disabled={!editingProfile}
                  />
                </div>
              </div>

              <div className="flex items-center gap-3">
                <Switch
                  checked={profileForm.co_invest}
                  onCheckedChange={(v) => setProfileField('co_invest', v)}
                  disabled={!editingProfile}
                />
                <Label>Co-invest</Label>
              </div>

              <div className="space-y-2">
                <Label>Transaction types</Label>
                <div className="flex flex-wrap gap-2">
                  {transactionTypes.map((ttId) => (
                    <Badge key={ttId} className="flex items-center gap-1">
                      {resolveLabel(transactionTypeOptions, ttId)}
                      {editingProfile && (
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-4 w-4 p-0"
                          aria-label={`Remove ${resolveLabel(transactionTypeOptions, ttId)}`}
                          onClick={() => setTransactionTypes((s) => s.filter((x) => x !== ttId))}
                        >
                          <X className="h-3 w-3" />
                        </Button>
                      )}
                    </Badge>
                  ))}
                </div>
                {editingProfile && (
                  <RefSelect
                    category="transaction_type"
                    value=""
                    placeholder="Add transaction type..."
                    onChange={(v) => {
                      if (v && !transactionTypes.includes(v)) setTransactionTypes((s) => [...s, v]);
                    }}
                  />
                )}
              </div>

              <div className="space-y-2">
                <Label>Sectors</Label>
                <div className="flex flex-wrap gap-2">
                  {sectorPrefs.map((sId) => (
                    <Badge key={sId} className="flex items-center gap-1">
                      {resolveLabel(sectorOptions, sId)}
                      {editingProfile && (
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-4 w-4 p-0"
                          aria-label={`Remove ${resolveLabel(sectorOptions, sId)}`}
                          onClick={() => setSectorPrefs((s) => s.filter((x) => x !== sId))}
                        >
                          <X className="h-3 w-3" />
                        </Button>
                      )}
                    </Badge>
                  ))}
                </div>
                {editingProfile && (
                  <RefSelect
                    category="sector"
                    value=""
                    placeholder="Add sector..."
                    onChange={(v) => {
                      if (v && !sectorPrefs.includes(v)) setSectorPrefs((s) => [...s, v]);
                    }}
                  />
                )}
              </div>

              <div className="space-y-2">
                <Label>Sub-sectors</Label>
                <div className="flex flex-wrap gap-2">
                  {subSectorPrefs.map((ssId) => (
                    <Badge key={ssId} className="flex items-center gap-1">
                      {resolveLabel(subSectorOptions, ssId)}
                      {editingProfile && (
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-4 w-4 p-0"
                          aria-label={`Remove ${resolveLabel(subSectorOptions, ssId)}`}
                          onClick={() => setSubSectorPrefs((s) => s.filter((x) => x !== ssId))}
                        >
                          <X className="h-3 w-3" />
                        </Button>
                      )}
                    </Badge>
                  ))}
                </div>
                {editingProfile && (
                  <RefSelect
                    category="sub_sector"
                    value=""
                    placeholder="Add sub-sector..."
                    onChange={(v) => {
                      if (v && !subSectorPrefs.includes(v)) setSubSectorPrefs((s) => [...s, v]);
                    }}
                  />
                )}
              </div>

              <div className="space-y-2">
                <Label>Preference notes</Label>
                <Textarea
                  rows={3}
                  value={profileForm.preference_notes}
                  onChange={(e) => setProfileField('preference_notes', e.target.value)}
                  disabled={!editingProfile}
                />
              </div>

              {editingProfile && (
                <Button
                  className="w-full"
                  onClick={handleSaveProfile}
                  disabled={updateMutation.isPending}
                >
                  Save changes
                </Button>
              )}
            </CardContent>
          </Card>

          {/* Card 3 — Internal */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle>Internal</CardTitle>
              <Button
                variant="ghost"
                size="icon"
                aria-label="Edit Internal"
                onClick={() => setEditingInternal((v) => !v)}
              >
                <Edit3 className="h-4 w-4" />
              </Button>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center gap-3">
                <Switch
                  checked={internalForm.watchlist}
                  onCheckedChange={(v) => setInternalField('watchlist', v)}
                  disabled={!editingInternal}
                />
                <Label>Watchlist</Label>
              </div>

              <div className="space-y-2">
                <Label>Coverage person</Label>
                <Select
                  value={internalForm.coverage_person_id}
                  onChange={(e) => setInternalField('coverage_person_id', e.target.value)}
                  disabled={!editingInternal}
                >
                  <option value="">Select coverage person</option>
                  {(users || []).map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.full_name || u.name || u.username}
                    </option>
                  ))}
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Contact frequency (days)</Label>
                <Input
                  type="number"
                  min="1"
                  value={internalForm.contact_frequency}
                  onChange={(e) => setInternalField('contact_frequency', e.target.value)}
                  disabled={!editingInternal}
                />
              </div>

              <div className="space-y-2">
                <Label>Legacy ID</Label>
                <Input
                  value={internalForm.legacy_id}
                  onChange={(e) => setInternalField('legacy_id', e.target.value)}
                  disabled={!editingInternal}
                />
              </div>

              {editingInternal && (
                <Button
                  className="w-full"
                  onClick={handleSaveInternal}
                  disabled={updateMutation.isPending}
                >
                  Save changes
                </Button>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Contacts Tab */}
        <TabsContent value="contacts" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Contacts</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {(contacts || []).length === 0 ? (
                <p className="text-sm text-muted-foreground">No contacts linked to this company.</p>
              ) : (
                (contacts || []).map((contact) => (
                  <div key={contact.id} className="rounded-xl bg-muted/40 p-4">
                    <p className="font-medium">{contact.first_name} {contact.last_name}</p>
                    <p className="text-sm text-muted-foreground">{contact.title || 'No title'}</p>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Deals Tab */}
        <TabsContent value="deals" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Deals</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {(deals || []).length === 0 ? (
                <p className="text-sm text-muted-foreground">No deals linked to this company.</p>
              ) : (
                (deals || []).map((deal) => (
                  <div key={deal.id} className="flex items-center justify-between rounded-xl bg-muted/40 p-4">
                    <div>
                      <p className="font-medium">{deal.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {deal.stage_name} • Updated {formatDate(deal.updated_at)}
                      </p>
                    </div>
                    <span>{formatCurrency(deal.value, deal.currency)}</span>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* LinkedIn Tab */}
        <TabsContent value="linkedin" className="space-y-4">
          <LinkedInPanel
            profile={company}
            onSync={() => syncMutation.mutate()}
            isSyncing={syncMutation.isPending}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}
