import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useParams } from 'react-router-dom';
import { toast } from 'sonner';
import { getBoard, getBoards } from '@/api/boards';
import { getDeal, getDealActivities, logActivity, scoreDeal, updateDeal } from '@/api/deals';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { Textarea } from '@/components/ui/textarea';
import { formatCurrency, formatDate } from '@/lib/utils';

function DealScoreCard({ dealId }) {
  const scoreQuery = useQuery({ queryKey: ['deal-score', dealId], queryFn: () => scoreDeal(dealId), retry: false });
  const score = scoreQuery.data?.ai_score;
  return (
    <Card>
      <CardHeader><CardTitle>AI insights</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-4">
          <div className="flex h-24 w-24 items-center justify-center rounded-full border-8 border-primary/15 text-xl font-semibold">{score == null ? 'N/A' : Math.round(score)}</div>
          <div>
            <p className="font-medium">{score == null ? 'Not scored' : `Confidence: ${scoreQuery.data?.confidence}`}</p>
            <p className="text-sm text-muted-foreground">{scoreQuery.data?.next_action || 'Score this deal to get next-best action guidance.'}</p>
          </div>
        </div>
        <div className="space-y-2">
          {(scoreQuery.data?.factors || []).map((factor, index) => <div key={index} className="rounded-xl bg-muted/40 px-3 py-2 text-sm">{factor.label || factor.factor || JSON.stringify(factor)}</div>)}
        </div>
      </CardContent>
    </Card>
  );
}

export default function DealDetailPage() {
  const { id } = useParams();
  const queryClient = useQueryClient();
  const [draftTitle, setDraftTitle] = useState('');
  const [draftBody, setDraftBody] = useState('');
  const dealQuery = useQuery({ queryKey: ['deal', id], queryFn: () => getDeal(id) });
  const activitiesQuery = useQuery({ queryKey: ['deal', id, 'activities'], queryFn: () => getDealActivities(id, { size: 50 }) });
  const tasksQuery = useQuery({
    queryKey: ['deal', id, 'tasks'],
    queryFn: async () => {
      const boards = await getBoards();
      const details = await Promise.all(boards.slice(0, 4).map((board) => getBoard(board.id).catch(() => null)));
      return details.filter(Boolean).flatMap((board) => board.columns.flatMap((column) => column.tasks)).filter((task) => task.deal_id === id);
    }
  });

  const updateMutation = useMutation({
    mutationFn: (payload) => updateDeal(id, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['deal', id] })
  });
  const logMutation = useMutation({
    mutationFn: (payload) => logActivity(id, payload),
    onSuccess: () => {
      setDraftBody('');
      setDraftTitle('');
      queryClient.invalidateQueries({ queryKey: ['deal', id, 'activities'] });
      toast.success('Activity logged');
    }
  });

  const deal = dealQuery.data;
  if (dealQuery.isLoading) return <Skeleton className="h-[640px] w-full" />;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="space-y-2">
          <Input className="h-auto border-0 px-0 text-3xl font-semibold shadow-none focus-visible:ring-0" value={deal.name} onChange={(e) => updateMutation.mutate({ name: e.target.value })} />
          <div className="flex flex-wrap items-center gap-2">
            <Badge>{deal.status}</Badge>
            <span className="text-sm text-muted-foreground">{deal.pipeline_name} / {deal.stage_name}</span>
            <span className="text-sm text-muted-foreground">Close {deal.expected_close_date ? formatDate(deal.expected_close_date) : 'TBD'}</span>
          </div>
        </div>
        <div className="text-right">
          <p className="text-3xl font-semibold">{formatCurrency(deal.value, deal.currency)}</p>
          <p className="text-sm text-muted-foreground">{Math.round(deal.probability * 100)}% probability</p>
        </div>
      </div>
      <div className="grid gap-6 xl:grid-cols-[280px,1fr,320px]">
        <Card>
          <CardHeader><CardTitle>Deal info</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div><p className="text-sm text-muted-foreground">Owner</p><p>{deal.owner_name}</p></div>
            <div><p className="text-sm text-muted-foreground">Contact</p><p>{deal.contact_name || 'No contact linked'}</p></div>
            <div><p className="text-sm text-muted-foreground">Company</p><p>{deal.company_name || 'No company linked'}</p></div>
            <div>
              <p className="mb-2 text-sm text-muted-foreground">Probability</p>
              <input type="range" min="0" max="1" step="0.05" value={deal.probability} onChange={(e) => updateMutation.mutate({ probability: Number(e.target.value) })} className="w-full" />
            </div>
            <Badge variant="accent">AI {deal.ai_score ?? 'Not scored'}</Badge>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Activity timeline</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap gap-2">
              {['call', 'email', 'meeting', 'note', 'linkedin_message'].map((type) => <Button key={type} variant="outline" size="sm" onClick={() => setDraftTitle(type)}>{type}</Button>)}
            </div>
            <Input placeholder="Activity title" value={draftTitle} onChange={(e) => setDraftTitle(e.target.value)} />
            <Textarea placeholder="Notes" value={draftBody} onChange={(e) => setDraftBody(e.target.value)} />
            <Button onClick={() => logMutation.mutate({ activity_type: draftTitle || 'note', title: draftTitle || 'Note', body: draftBody, occurred_at: new Date().toISOString() })}>Log activity</Button>
            <div className="space-y-3">
              {(activitiesQuery.data?.items || []).map((item) => <div key={item.id} className="rounded-xl bg-muted/40 px-4 py-3"><div className="mb-2 flex items-center justify-between"><Badge>{item.activity_type}</Badge><span className="text-xs text-muted-foreground">{formatDate(item.occurred_at)}</span></div><p className="font-medium">{item.title}</p><p className="text-sm text-muted-foreground">{item.body}</p></div>)}
            </div>
          </CardContent>
        </Card>
        <div className="space-y-4">
          <DealScoreCard dealId={id} />
          <Card>
            <CardHeader><CardTitle>Tasks</CardTitle></CardHeader>
            <CardContent className="space-y-3">{(tasksQuery.data || []).map((task) => <div key={task.id} className="rounded-xl bg-muted/40 p-3"><p className="font-medium">{task.title}</p><p className="text-xs text-muted-foreground">{task.priority} • {task.status}</p></div>)}</CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle>Files</CardTitle></CardHeader>
            <CardContent><p className="text-sm text-muted-foreground">File uploads are not yet exposed by the backend. This panel is ready for attachment metadata once that route lands.</p></CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
