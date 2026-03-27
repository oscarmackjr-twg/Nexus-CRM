import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { Edit3, Linkedin, PlusCircle } from 'lucide-react';
import { toast } from 'sonner';
import { getBoards, getBoard } from '@/api/boards';
import { getContact, getContactActivities, getContactDeals, syncContactLinkedIn, updateContact } from '@/api/contacts';
import { getContactInsights } from '@/api/ai';
import { logActivity } from '@/api/deals';
import LinkedInPanel from '@/components/LinkedInPanel';
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

const activitySchema = z.object({
  dealId: z.string().min(1, 'Choose a deal'),
  activity_type: z.string().min(1),
  title: z.string().min(1),
  body: z.string().optional(),
  occurred_at: z.string().min(1)
});

export default function ContactDetailPage() {
  const { id } = useParams();
  const queryClient = useQueryClient();
  const [activityOpen, setActivityOpen] = useState(false);
  const [editing, setEditing] = useState(false);
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

  const updateMutation = useMutation({
    mutationFn: (payload) => updateContact(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contact', id] });
      setEditing(false);
      toast.success('Contact updated');
    }
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
    mutationFn: ({ dealId, ...payload }) => logActivity(dealId, payload),
    onSuccess: () => {
      setActivityOpen(false);
      toast.success('Activity logged');
    }
  });

  const contact = contactQuery.data;
  const editForm = useForm({
    values: {
      first_name: contact?.first_name || '',
      last_name: contact?.last_name || '',
      email: contact?.email || '',
      phone: contact?.phone || '',
      title: contact?.title || '',
      lifecycle_stage: contact?.lifecycle_stage || 'lead'
    }
  });
  const activityForm = useForm({
    resolver: zodResolver(activitySchema),
    defaultValues: { dealId: '', activity_type: 'note', title: '', body: '', occurred_at: new Date().toISOString().slice(0, 16) }
  });

  const linkedDeals = dealsQuery.data || [];
  const timeline = activitiesQuery.data || [];
  const tasks = tasksQuery.data || [];

  const linkedInData = useMemo(() => ({
    linkedin_member_id: contact?.linkedin_member_id,
    linkedin_profile_url: contact?.linkedin_profile_url,
    linkedin_synced_at: contact?.linkedin_synced_at
  }), [contact]);

  if (contactQuery.isLoading) return <div className="space-y-4"><Skeleton className="h-12 w-64" /><Skeleton className="h-[540px] w-full" /></div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold">{contact.first_name} {contact.last_name}</h1>
          <p className="text-muted-foreground">{contact.company_name || 'No company linked'}</p>
        </div>
        <Button onClick={() => setActivityOpen(true)}><PlusCircle className="h-4 w-4" />Log activity</Button>
      </div>
      <div className="grid gap-6 xl:grid-cols-[320px,1fr]">
      <div className="space-y-4">
        <Card>
          <CardHeader className="flex-row items-center justify-between">
            <CardTitle>Contact info</CardTitle>
            <Button variant="ghost" size="icon" onClick={() => setEditing((open) => !open)}><Edit3 className="h-4 w-4" /></Button>
          </CardHeader>
          <CardContent className="space-y-3">
            {editing ? (
              <form className="space-y-3" onSubmit={editForm.handleSubmit((values) => updateMutation.mutate(values))}>
                {['first_name', 'last_name', 'email', 'phone', 'title', 'lifecycle_stage'].map((field) => <Input key={field} {...editForm.register(field)} placeholder={field.replace('_', ' ')} />)}
                <Button type="submit" className="w-full">Save changes</Button>
              </form>
            ) : (
              <>
                <div><p className="text-3xl font-semibold">{contact.first_name} {contact.last_name}</p><p className="text-sm text-muted-foreground">{contact.title || 'No title'}</p></div>
                <p className="text-sm">{contact.email || 'No email'}</p>
                <p className="text-sm">{contact.phone || 'No phone'}</p>
                <div className="flex flex-wrap gap-2">{contact.tags.length ? contact.tags.map((tag) => <Badge key={tag}>{tag}</Badge>) : <Badge>untagged</Badge>}</div>
                <Badge variant="accent">{contact.lifecycle_stage}</Badge>
              </>
            )}
          </CardContent>
        </Card>
        <LinkedInPanel profile={linkedInData} onSync={() => syncMutation.mutate()} isSyncing={syncMutation.isPending} />
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><Linkedin className="h-4 w-4" />AI contact insight</CardTitle></CardHeader>
          <CardContent>
            {insightsQuery.data ? (
              <div className="space-y-3">
                <p className="text-sm">{insightsQuery.data.summary}</p>
                <div className="flex flex-wrap gap-2">{insightsQuery.data.recommended_actions.map((action) => <Badge key={action} variant="secondary">{action}</Badge>)}</div>
              </div>
            ) : <p className="text-sm text-muted-foreground">No AI contact insight available.</p>}
          </CardContent>
        </Card>
      </div>
      <div className="space-y-4">
        <Tabs defaultValue="timeline" className="space-y-4">
          <TabsList>
            <TabsTrigger value="timeline">Timeline</TabsTrigger>
            <TabsTrigger value="deals">Deals</TabsTrigger>
            <TabsTrigger value="tasks">Tasks</TabsTrigger>
            <TabsTrigger value="linkedin">LinkedIn</TabsTrigger>
          </TabsList>
          <TabsContent value="timeline" className="space-y-3">
            {timeline.map((item) => <Card key={item.id}><CardContent className="p-4"><div className="mb-2 flex items-center justify-between"><Badge>{item.activity_type}</Badge><span className="text-xs text-muted-foreground">{formatDate(item.occurred_at)}</span></div><p className="font-medium">{item.title || 'Activity'}</p><p className="text-sm text-muted-foreground">{item.body || 'No notes'}</p></CardContent></Card>)}
          </TabsContent>
          <TabsContent value="deals" className="space-y-3">
            {linkedDeals.map((deal) => <Card key={deal.id}><CardContent className="flex items-center justify-between p-4"><div><p className="font-medium">{deal.name}</p><p className="text-sm text-muted-foreground">{deal.stage_name}</p></div><span>{formatCurrency(deal.value, deal.currency)}</span></CardContent></Card>)}
          </TabsContent>
          <TabsContent value="tasks" className="space-y-3">
            {tasks.length ? tasks.map((task) => <Card key={task.id}><CardContent className="p-4"><p className="font-medium">{task.title}</p><p className="text-sm text-muted-foreground">{task.priority} • Due {task.due_date ? formatDate(task.due_date) : 'N/A'}</p></CardContent></Card>) : <p className="text-sm text-muted-foreground">No linked tasks found.</p>}
          </TabsContent>
          <TabsContent value="linkedin">
            <Card><CardContent className="space-y-2 p-4"><p className="font-medium">LinkedIn profile data</p><p className="text-sm text-muted-foreground">Member ID: {contact.linkedin_member_id || 'Not synced'}</p><p className="text-sm text-muted-foreground">Profile URL: {contact.linkedin_profile_url || 'Unavailable'}</p></CardContent></Card>
          </TabsContent>
        </Tabs>
      </div>
      </div>

      <Dialog open={activityOpen} onOpenChange={setActivityOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Log activity</DialogTitle></DialogHeader>
          <form className="space-y-3" onSubmit={activityForm.handleSubmit((values) => logMutation.mutate(values))}>
            <div className="space-y-2"><Label>Linked deal</Label><select className="flex h-10 w-full rounded-xl border bg-background px-3" {...activityForm.register('dealId')}><option value="">Select deal</option>{linkedDeals.map((deal) => <option key={deal.id} value={deal.id}>{deal.name}</option>)}</select></div>
            <Input placeholder="Type" {...activityForm.register('activity_type')} />
            <Input placeholder="Title" {...activityForm.register('title')} />
            <Textarea placeholder="Body" {...activityForm.register('body')} />
            <Input type="datetime-local" {...activityForm.register('occurred_at')} />
            <Button type="submit" className="w-full">Save activity</Button>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
