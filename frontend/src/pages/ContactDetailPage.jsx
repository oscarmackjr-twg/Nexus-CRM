import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { Edit3, ExternalLink, Linkedin, PlusCircle, X } from 'lucide-react';
import { toast } from 'sonner';
import { getBoards, getBoard } from '@/api/boards';
import { getContact, getContactActivities, getContactDeals, logContactActivity, syncContactLinkedIn, updateContact } from '@/api/contacts';
import { getContactInsights } from '@/api/ai';
import { logActivity } from '@/api/deals';
import { getRefData } from '@/api/refData';
import { getUsers } from '@/api/users';
import LinkedInPanel from '@/components/LinkedInPanel';
import { RefSelect } from '@/components/RefSelect';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { formatCurrency, formatDate } from '@/lib/utils';

const activitySchema = z.object({
  activity_type: z.string().min(1),
  notes: z.string().optional(),
  occurred_at: z.string().min(1),
  dealId: z.string().optional(),
});

export default function ContactDetailPage() {
  const { id } = useParams();
  const queryClient = useQueryClient();
  const [activityOpen, setActivityOpen] = useState(false);

  // Per-card editing state
  const [editingIdentity, setEditingIdentity] = useState(false);
  const [editingPreferences, setEditingPreferences] = useState(false);
  const [editingCoverage, setEditingCoverage] = useState(false);

  const contactQuery = useQuery({ queryKey: ['contact', id], queryFn: () => getContact(id) });
  const dealsQuery = useQuery({ queryKey: ['contact', id, 'deals'], queryFn: () => getContactDeals(id) });
  const activitiesQuery = useQuery({ queryKey: ['contact', id, 'activities'], queryFn: () => getContactActivities(id, { limit: 50 }) });
  const insightsQuery = useQuery({ queryKey: ['contact', id, 'insights'], queryFn: () => getContactInsights(id), retry: false });
  const tasksQuery = useQuery({
    queryKey: ['contact', id, 'tasks'],
    queryFn: async () => {
      const boards = await getBoards();
      const detail = await Promise.all(boards.slice(0, 4).map((board) => getBoard(board.id).catch(() => null)));
      return detail.filter(Boolean).flatMap((board) => board.columns.flatMap((column) => column.tasks)).filter((task) => task.contact_id === id);
    }
  });

  const { data: users } = useQuery({ queryKey: ['users'], queryFn: getUsers });
  const { data: sectorOptions } = useQuery({ queryKey: ['ref', 'sector'], queryFn: () => getRefData('sector') });
  const { data: subSectorOptions } = useQuery({ queryKey: ['ref', 'sub_sector'], queryFn: () => getRefData('sub_sector') });

  const contact = contactQuery.data;

  // Local JSONB / M2M state — initialized from contact data after load
  const [identityForm, setIdentityForm] = useState(null);
  const [employment, setEmployment] = useState([]);
  const [boardSeats, setBoardSeats] = useState([]);
  const [sectors, setSectors] = useState([]);
  const [subSectors, setSubSectors] = useState([]);
  const [contactFrequency, setContactFrequency] = useState('');
  const [coveragePersons, setCoveragePersons] = useState([]);
  const [legacyId, setLegacyId] = useState('');

  // Sync local state from contact once loaded
  useMemo(() => {
    if (contact && identityForm === null) {
      setIdentityForm({
        contact_type_id: contact.contact_type_id || '',
        primary_contact: contact.primary_contact || false,
        business_phone: contact.business_phone || '',
        mobile_phone: contact.mobile_phone || '',
        linkedin_url: contact.linkedin_url || '',
        assistant_name: contact.assistant_name || '',
        assistant_email: contact.assistant_email || '',
        assistant_phone: contact.assistant_phone || '',
        address: contact.address || '',
        city: contact.city || '',
        state: contact.state || '',
        postal_code: contact.postal_code || '',
        country: contact.country || '',
      });
      setEmployment(contact.previous_employment || []);
      setBoardSeats(contact.board_memberships || []);
      setSectors(contact.sector || []);
      setSubSectors(contact.sub_sector || []);
      setContactFrequency(contact.contact_frequency || '');
      setCoveragePersons(contact.coverage_persons || []);
      setLegacyId(contact.legacy_id || '');
    }
  }, [contact, identityForm]);

  const resolveLabel = (options, id) => options?.find((o) => o.id === id)?.label || id;

  const updateMutation = useMutation({
    mutationFn: (payload) => updateContact(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contact', id] });
      toast.success('Contact updated');
    },
    onError: () => toast.error('Could not save changes. Check your connection and try again.')
  });

  const syncMutation = useMutation({
    mutationFn: () => syncContactLinkedIn(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contact', id] });
      toast.success('LinkedIn sync completed');
    },
    onError: (error) => toast.error(error.response?.data?.detail || 'LinkedIn sync failed')
  });

  const logMutation = useMutation({
    mutationFn: async ({ dealId, ...payload }) => {
      if (dealId) {
        return logActivity(dealId, payload);
      }
      return logContactActivity(id, payload);
    },
    onSuccess: () => {
      setActivityOpen(false);
      queryClient.invalidateQueries({ queryKey: ['contact', id, 'activities'] });
      toast.success('Activity logged');
    }
  });

  const activityForm = useForm({
    resolver: zodResolver(activitySchema),
    defaultValues: { dealId: '', activity_type: 'note', notes: '', occurred_at: new Date().toISOString().slice(0, 10) }
  });

  const saveIdentity = () => {
    updateMutation.mutate({
      ...identityForm,
      previous_employment: employment,
      board_memberships: boardSeats,
    }, {
      onSuccess: () => setEditingIdentity(false)
    });
  };

  const savePreferences = () => {
    updateMutation.mutate({
      sector: sectors,
      sub_sector: subSectors,
      contact_frequency: contactFrequency ? Number(contactFrequency) : null,
    }, {
      onSuccess: () => setEditingPreferences(false)
    });
  };

  const saveCoverage = () => {
    updateMutation.mutate({
      coverage_persons: coveragePersons.map((p) => p.id),
      legacy_id: legacyId || null,
    }, {
      onSuccess: () => setEditingCoverage(false)
    });
  };

  const updateEmployment = (idx, field, value) => {
    setEmployment((prev) => prev.map((entry, i) => i === idx ? { ...entry, [field]: value } : entry));
  };

  const updateBoardSeat = (idx, field, value) => {
    setBoardSeats((prev) => prev.map((entry, i) => i === idx ? { ...entry, [field]: value } : entry));
  };

  const linkedDeals = dealsQuery.data || [];
  const timeline = activitiesQuery.data || [];
  const tasks = tasksQuery.data || [];

  const linkedInData = useMemo(() => ({
    linkedin_member_id: contact?.linkedin_member_id,
    linkedin_profile_url: contact?.linkedin_profile_url,
    linkedin_synced_at: contact?.linkedin_synced_at
  }), [contact]);

  if (contactQuery.isLoading) return <div className="space-y-4"><Skeleton className="h-12 w-64" /><Skeleton className="h-[540px] w-full" /></div>;

  const isSaving = updateMutation.isPending;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold">
            {contact.first_name} {contact.last_name}
            {contact.primary_contact && (
              <Badge variant="accent" className="ml-2">Primary</Badge>
            )}
          </h1>
          <p className="text-muted-foreground">{contact.company_name || 'No company linked'}</p>
        </div>
        <Button onClick={() => setActivityOpen(true)}><PlusCircle className="h-4 w-4 mr-1" />Log activity</Button>
      </div>

      <Tabs defaultValue="profile" className="space-y-4">
        <TabsList>
          <TabsTrigger value="profile">Profile</TabsTrigger>
          <TabsTrigger value="timeline">Timeline</TabsTrigger>
          <TabsTrigger value="deals">Deals</TabsTrigger>
          <TabsTrigger value="tasks">Tasks</TabsTrigger>
          <TabsTrigger value="linkedin">LinkedIn</TabsTrigger>
        </TabsList>

        {/* Profile Tab */}
        <TabsContent value="profile" className="space-y-4">
          <div className="grid gap-6 xl:grid-cols-[1fr,1fr]">
            <div className="space-y-4">
              {/* Card 1 — Identity */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle className="text-base font-semibold">Identity</CardTitle>
                  <Button
                    variant="ghost"
                    size="icon"
                    aria-label="Edit Identity"
                    onClick={() => setEditingIdentity(!editingIdentity)}
                  >
                    <Edit3 className="h-4 w-4" />
                  </Button>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Contact details</p>
                  <div className="space-y-3">
                    <div className="space-y-1">
                      <Label>Contact type</Label>
                      <RefSelect
                        category="contact_type"
                        value={identityForm?.contact_type_id || ''}
                        onChange={(v) => setIdentityForm((f) => ({ ...f, contact_type_id: v }))}
                        placeholder="Select contact type"
                        disabled={!editingIdentity}
                      />
                    </div>
                    <div className="flex items-center gap-3">
                      <Switch
                        checked={identityForm?.primary_contact || false}
                        onCheckedChange={(v) => setIdentityForm((f) => ({ ...f, primary_contact: v }))}
                        disabled={!editingIdentity}
                      />
                      <Label>Primary contact</Label>
                    </div>
                    <div className="space-y-1">
                      <Label>Business phone</Label>
                      <Input
                        type="tel"
                        value={identityForm?.business_phone || ''}
                        onChange={(e) => setIdentityForm((f) => ({ ...f, business_phone: e.target.value }))}
                        disabled={!editingIdentity}
                        placeholder="Business phone"
                      />
                    </div>
                    <div className="space-y-1">
                      <Label>Mobile phone</Label>
                      <Input
                        type="tel"
                        value={identityForm?.mobile_phone || ''}
                        onChange={(e) => setIdentityForm((f) => ({ ...f, mobile_phone: e.target.value }))}
                        disabled={!editingIdentity}
                        placeholder="Mobile phone"
                      />
                    </div>
                    <div className="space-y-1">
                      <Label>LinkedIn URL</Label>
                      {editingIdentity ? (
                        <Input
                          type="url"
                          value={identityForm?.linkedin_url || ''}
                          onChange={(e) => setIdentityForm((f) => ({ ...f, linkedin_url: e.target.value }))}
                          placeholder="https://linkedin.com/in/..."
                        />
                      ) : (
                        identityForm?.linkedin_url ? (
                          <a
                            href={identityForm.linkedin_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-1 text-sm text-accent hover:underline"
                            aria-label="Open LinkedIn profile"
                          >
                            {identityForm.linkedin_url}
                            <ExternalLink className="h-3 w-3" />
                          </a>
                        ) : (
                          <p className="text-sm text-muted-foreground">No LinkedIn URL</p>
                        )
                      )}
                    </div>
                  </div>

                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Assistant</p>
                  <div className="space-y-3">
                    <div className="space-y-1">
                      <Label>Name</Label>
                      <Input
                        value={identityForm?.assistant_name || ''}
                        onChange={(e) => setIdentityForm((f) => ({ ...f, assistant_name: e.target.value }))}
                        disabled={!editingIdentity}
                        placeholder="Assistant name"
                      />
                    </div>
                    <div className="space-y-1">
                      <Label>Email</Label>
                      <Input
                        type="email"
                        value={identityForm?.assistant_email || ''}
                        onChange={(e) => setIdentityForm((f) => ({ ...f, assistant_email: e.target.value }))}
                        disabled={!editingIdentity}
                        placeholder="Assistant email"
                      />
                    </div>
                    <div className="space-y-1">
                      <Label>Phone</Label>
                      <Input
                        type="tel"
                        value={identityForm?.assistant_phone || ''}
                        onChange={(e) => setIdentityForm((f) => ({ ...f, assistant_phone: e.target.value }))}
                        disabled={!editingIdentity}
                        placeholder="Assistant phone"
                      />
                    </div>
                  </div>

                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Address</p>
                  <div className="space-y-3">
                    <div className="space-y-1">
                      <Label>Street address</Label>
                      <Input
                        value={identityForm?.address || ''}
                        onChange={(e) => setIdentityForm((f) => ({ ...f, address: e.target.value }))}
                        disabled={!editingIdentity}
                        placeholder="Street address"
                      />
                    </div>
                    <div className="flex gap-2">
                      <div className="flex-1 space-y-1">
                        <Label>City</Label>
                        <Input
                          value={identityForm?.city || ''}
                          onChange={(e) => setIdentityForm((f) => ({ ...f, city: e.target.value }))}
                          disabled={!editingIdentity}
                          placeholder="City"
                        />
                      </div>
                      <div className="flex-1 space-y-1">
                        <Label>State</Label>
                        <Input
                          value={identityForm?.state || ''}
                          onChange={(e) => setIdentityForm((f) => ({ ...f, state: e.target.value }))}
                          disabled={!editingIdentity}
                          placeholder="State"
                        />
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <div className="flex-1 space-y-1">
                        <Label>Postal code</Label>
                        <Input
                          value={identityForm?.postal_code || ''}
                          onChange={(e) => setIdentityForm((f) => ({ ...f, postal_code: e.target.value }))}
                          disabled={!editingIdentity}
                          placeholder="Postal code"
                        />
                      </div>
                      <div className="flex-1 space-y-1">
                        <Label>Country</Label>
                        <Input
                          value={identityForm?.country || ''}
                          onChange={(e) => setIdentityForm((f) => ({ ...f, country: e.target.value }))}
                          disabled={!editingIdentity}
                          placeholder="Country"
                        />
                      </div>
                    </div>
                  </div>

                  {editingIdentity && (
                    <Button
                      className="w-full"
                      onClick={saveIdentity}
                      disabled={isSaving}
                    >
                      Save changes
                    </Button>
                  )}
                </CardContent>
              </Card>

              {/* Employment History Card */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle className="text-base font-semibold">Employment history</CardTitle>
                  <Button
                    variant="ghost"
                    size="icon"
                    aria-label="Edit Employment history"
                    onClick={() => setEditingIdentity(!editingIdentity)}
                  >
                    <Edit3 className="h-4 w-4" />
                  </Button>
                </CardHeader>
                <CardContent className="space-y-3">
                  {employment.length === 0 && !editingIdentity && (
                    <p className="text-sm text-muted-foreground">No previous employment recorded.</p>
                  )}
                  {employment.map((entry, i) => (
                    <div key={i} className="flex gap-3 items-center">
                      <Input
                        className="flex-1"
                        value={entry.company || ''}
                        placeholder="Company"
                        onChange={(e) => updateEmployment(i, 'company', e.target.value)}
                        disabled={!editingIdentity}
                      />
                      <Input
                        className="flex-1"
                        value={entry.title || ''}
                        placeholder="Title"
                        onChange={(e) => updateEmployment(i, 'title', e.target.value)}
                        disabled={!editingIdentity}
                      />
                      <Input
                        className="w-20"
                        value={entry.from || ''}
                        placeholder="From"
                        onChange={(e) => updateEmployment(i, 'from', e.target.value)}
                        disabled={!editingIdentity}
                      />
                      <Input
                        className="w-20"
                        value={entry.to || ''}
                        placeholder="present"
                        onChange={(e) => updateEmployment(i, 'to', e.target.value)}
                        disabled={!editingIdentity}
                      />
                      {editingIdentity && (
                        <Button
                          variant="ghost"
                          size="icon"
                          aria-label="Remove position"
                          onClick={() => setEmployment((e) => e.filter((_, j) => j !== i))}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  ))}
                  {editingIdentity && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setEmployment((e) => [...e, { company: '', title: '', from: '', to: '' }])}
                    >
                      + Add position
                    </Button>
                  )}
                  {editingIdentity && (
                    <Button
                      className="w-full"
                      onClick={saveIdentity}
                      disabled={isSaving}
                    >
                      Save changes
                    </Button>
                  )}
                </CardContent>
              </Card>

              {/* Board Memberships Card */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle className="text-base font-semibold">Board memberships</CardTitle>
                  <Button
                    variant="ghost"
                    size="icon"
                    aria-label="Edit Board memberships"
                    onClick={() => setEditingIdentity(!editingIdentity)}
                  >
                    <Edit3 className="h-4 w-4" />
                  </Button>
                </CardHeader>
                <CardContent className="space-y-3">
                  {boardSeats.length === 0 && !editingIdentity && (
                    <p className="text-sm text-muted-foreground">No board memberships recorded.</p>
                  )}
                  {boardSeats.map((entry, i) => (
                    <div key={i} className="flex gap-3 items-center">
                      <Input
                        className="flex-1"
                        value={entry.company || ''}
                        placeholder="Company"
                        onChange={(e) => updateBoardSeat(i, 'company', e.target.value)}
                        disabled={!editingIdentity}
                      />
                      <Input
                        className="flex-1"
                        value={entry.title || ''}
                        placeholder="Title"
                        onChange={(e) => updateBoardSeat(i, 'title', e.target.value)}
                        disabled={!editingIdentity}
                      />
                      {editingIdentity && (
                        <Button
                          variant="ghost"
                          size="icon"
                          aria-label="Remove board seat"
                          onClick={() => setBoardSeats((s) => s.filter((_, j) => j !== i))}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  ))}
                  {editingIdentity && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setBoardSeats((s) => [...s, { company: '', title: '' }])}
                    >
                      + Add board seat
                    </Button>
                  )}
                  {editingIdentity && (
                    <Button
                      className="w-full"
                      onClick={saveIdentity}
                      disabled={isSaving}
                    >
                      Save changes
                    </Button>
                  )}
                </CardContent>
              </Card>
            </div>

            <div className="space-y-4">
              {/* Card 2 — Investment Preferences */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle className="text-base font-semibold">Investment Preferences</CardTitle>
                  <Button
                    variant="ghost"
                    size="icon"
                    aria-label="Edit Investment Preferences"
                    onClick={() => setEditingPreferences(!editingPreferences)}
                  >
                    <Edit3 className="h-4 w-4" />
                  </Button>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Sectors */}
                  <div className="space-y-2">
                    <Label>Sectors</Label>
                    <div className="flex flex-wrap gap-2">
                      {sectors.map((sectorId) => (
                        <Badge key={sectorId} className="flex items-center gap-1">
                          {resolveLabel(sectorOptions, sectorId)}
                          {editingPreferences && (
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-4 w-4 p-0"
                              aria-label={`Remove ${resolveLabel(sectorOptions, sectorId)}`}
                              onClick={() => setSectors((s) => s.filter((x) => x !== sectorId))}
                            >
                              <X className="h-3 w-3" />
                            </Button>
                          )}
                        </Badge>
                      ))}
                    </div>
                    {editingPreferences && (
                      <RefSelect
                        category="sector"
                        value=""
                        placeholder="Add sector..."
                        onChange={(sectorId) => {
                          if (sectorId && !sectors.includes(sectorId)) {
                            setSectors((s) => [...s, sectorId]);
                          }
                        }}
                      />
                    )}
                  </div>

                  {/* Sub-sectors */}
                  <div className="space-y-2">
                    <Label>Sub-sectors</Label>
                    <div className="flex flex-wrap gap-2">
                      {subSectors.map((subId) => (
                        <Badge key={subId} className="flex items-center gap-1">
                          {resolveLabel(subSectorOptions, subId)}
                          {editingPreferences && (
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-4 w-4 p-0"
                              aria-label={`Remove ${resolveLabel(subSectorOptions, subId)}`}
                              onClick={() => setSubSectors((s) => s.filter((x) => x !== subId))}
                            >
                              <X className="h-3 w-3" />
                            </Button>
                          )}
                        </Badge>
                      ))}
                    </div>
                    {editingPreferences && (
                      <RefSelect
                        category="sub_sector"
                        value=""
                        placeholder="Add sub-sector..."
                        onChange={(subId) => {
                          if (subId && !subSectors.includes(subId)) {
                            setSubSectors((s) => [...s, subId]);
                          }
                        }}
                      />
                    )}
                  </div>

                  {/* Contact frequency */}
                  <div className="space-y-1">
                    <Label>Contact frequency (days)</Label>
                    <Input
                      type="number"
                      min="1"
                      value={contactFrequency}
                      onChange={(e) => setContactFrequency(e.target.value)}
                      disabled={!editingPreferences}
                      placeholder="e.g. 30"
                    />
                  </div>

                  {editingPreferences && (
                    <Button
                      className="w-full"
                      onClick={savePreferences}
                      disabled={isSaving}
                    >
                      Save changes
                    </Button>
                  )}
                </CardContent>
              </Card>

              {/* Card 3 — Internal Coverage */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle className="text-base font-semibold">Internal Coverage</CardTitle>
                  <Button
                    variant="ghost"
                    size="icon"
                    aria-label="Edit Internal Coverage"
                    onClick={() => setEditingCoverage(!editingCoverage)}
                  >
                    <Edit3 className="h-4 w-4" />
                  </Button>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>Coverage persons</Label>
                    <div className="flex flex-wrap gap-2">
                      {coveragePersons.length === 0 && !editingCoverage && (
                        <p className="text-sm text-muted-foreground">No coverage persons assigned.</p>
                      )}
                      {coveragePersons.map((p) => (
                        <Badge key={p.id} className="flex items-center gap-1">
                          {p.name}
                          {editingCoverage && (
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-4 w-4 p-0"
                              aria-label={`Remove ${p.name}`}
                              onClick={() => setCoveragePersons((cp) => cp.filter((x) => x.id !== p.id))}
                            >
                              <X className="h-3 w-3" />
                            </Button>
                          )}
                        </Badge>
                      ))}
                    </div>
                    {editingCoverage && (
                      <select
                        className="flex h-10 w-full rounded-xl border bg-background px-3 text-sm"
                        value=""
                        onChange={(e) => {
                          const userId = e.target.value;
                          const user = users?.find((u) => u.id === userId);
                          if (user && !coveragePersons.find((p) => p.id === user.id)) {
                            setCoveragePersons((cp) => [
                              ...cp,
                              { id: user.id, name: user.full_name || user.name }
                            ]);
                          }
                        }}
                      >
                        <option value="">Add coverage person...</option>
                        {users?.map((u) => (
                          <option key={u.id} value={u.id}>{u.full_name || u.name}</option>
                        ))}
                      </select>
                    )}
                  </div>

                  <div className="space-y-1">
                    <Label>Legacy ID</Label>
                    <Input
                      value={legacyId}
                      onChange={(e) => setLegacyId(e.target.value)}
                      disabled={!editingCoverage}
                      placeholder="Legacy ID"
                    />
                  </div>

                  {editingCoverage && (
                    <Button
                      className="w-full"
                      onClick={saveCoverage}
                      disabled={isSaving}
                    >
                      Save changes
                    </Button>
                  )}
                </CardContent>
              </Card>

              {/* AI Insight */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base font-semibold">
                    <Linkedin className="h-4 w-4" />AI contact insight
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {insightsQuery.data ? (
                    <div className="space-y-3">
                      <p className="text-sm">{insightsQuery.data.summary}</p>
                      <div className="flex flex-wrap gap-2">
                        {insightsQuery.data.recommended_actions.map((action) => (
                          <Badge key={action} variant="secondary">{action}</Badge>
                        ))}
                      </div>
                    </div>
                  ) : <p className="text-sm text-muted-foreground">No AI contact insight available.</p>}
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        {/* Timeline Tab */}
        <TabsContent value="timeline" className="space-y-3">
          {timeline.length === 0 && (
            <p className="text-sm text-muted-foreground">No activities yet. Use Log activity to record a call, meeting, email, or note.</p>
          )}
          {timeline.map((item) => (
            <Card key={item.id}>
              <CardContent className="p-4">
                <div className="mb-2 flex items-center justify-between">
                  <Badge>{item.activity_type}</Badge>
                  <span className="text-xs text-muted-foreground">{formatDate(item.occurred_at)}</span>
                </div>
                <p className="font-medium">{item.title || 'Activity'}</p>
                <p className="text-sm text-muted-foreground">{item.notes || item.body || 'No notes'}</p>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        {/* Deals Tab */}
        <TabsContent value="deals" className="space-y-3">
          {linkedDeals.map((deal) => (
            <Card key={deal.id}>
              <CardContent className="flex items-center justify-between p-4">
                <div>
                  <p className="font-medium">{deal.name}</p>
                  <p className="text-sm text-muted-foreground">{deal.stage_name}</p>
                </div>
                <span>{formatCurrency(deal.value, deal.currency)}</span>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        {/* Tasks Tab */}
        <TabsContent value="tasks" className="space-y-3">
          {tasks.length ? tasks.map((task) => (
            <Card key={task.id}>
              <CardContent className="p-4">
                <p className="font-medium">{task.title}</p>
                <p className="text-sm text-muted-foreground">{task.priority} • Due {task.due_date ? formatDate(task.due_date) : 'N/A'}</p>
              </CardContent>
            </Card>
          )) : <p className="text-sm text-muted-foreground">No linked tasks found.</p>}
        </TabsContent>

        {/* LinkedIn Tab */}
        <TabsContent value="linkedin" className="space-y-4">
          <LinkedInPanel profile={linkedInData} onSync={() => syncMutation.mutate()} isSyncing={syncMutation.isPending} />
          <Card>
            <CardContent className="space-y-2 p-4">
              <p className="font-medium">LinkedIn profile data</p>
              <p className="text-sm text-muted-foreground">Member ID: {contact.linkedin_member_id || 'Not synced'}</p>
              <p className="text-sm text-muted-foreground">Profile URL: {contact.linkedin_profile_url || 'Unavailable'}</p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Log Activity Dialog */}
      <Dialog open={activityOpen} onOpenChange={setActivityOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Log activity</DialogTitle>
          </DialogHeader>
          <form
            className="space-y-3"
            onSubmit={activityForm.handleSubmit((values) => logMutation.mutate(values))}
          >
            <div className="space-y-2">
              <Label>Type</Label>
              <select
                className="flex h-10 w-full rounded-xl border bg-background px-3 text-sm"
                {...activityForm.register('activity_type')}
              >
                <option value="call">Call</option>
                <option value="meeting">Meeting</option>
                <option value="email">Email</option>
                <option value="note">Note</option>
              </select>
            </div>
            <div className="space-y-2">
              <Label>Date</Label>
              <Input type="date" {...activityForm.register('occurred_at')} />
            </div>
            <div className="space-y-2">
              <Label>Notes</Label>
              <Textarea rows={4} {...activityForm.register('notes')} />
            </div>
            <div className="space-y-2">
              <Label>Linked deal</Label>
              <select
                className="flex h-10 w-full rounded-xl border bg-background px-3 text-sm"
                {...activityForm.register('dealId')}
              >
                <option value="">No deal (contact-level)</option>
                {linkedDeals.map((deal) => (
                  <option key={deal.id} value={deal.id}>{deal.name}</option>
                ))}
              </select>
            </div>
            <Button type="submit" className="w-full" disabled={logMutation.isPending}>Log activity</Button>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
