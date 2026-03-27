import { useEffect, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';
import { toast } from 'sonner';
import { getAISuggestions } from '@/api/ai';
import { getBoards, getBoard } from '@/api/boards';
import { getContacts } from '@/api/contacts';
import { getDeals } from '@/api/deals';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { formatCurrency, formatDate } from '@/lib/utils';
import { useAuth } from '@/hooks/useAuth';

const chartColors = ['#6366F1', '#8B5CF6', '#06B6D4', '#10B981', '#F59E0B'];

function SectionCard({ title, description, children }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const { user } = useAuth();
  const dashboardQuery = useQuery({
    queryKey: ['dashboard', user?.id],
    queryFn: async () => {
      const [deals, contacts, boards, suggestions] = await Promise.all([
        getDeals({ size: 100 }),
        getContacts({ size: 100 }),
        getBoards(),
        getAISuggestions().catch(() => [])
      ]);
      const boardDetails = await Promise.all(boards.slice(0, 3).map((board) => getBoard(board.id).catch(() => null)));
      return { deals, contacts, suggestions, boardDetails: boardDetails.filter(Boolean) };
    }
  });

  useEffect(() => {
    if (dashboardQuery.isError) {
      toast.error('Dashboard data failed to load');
    }
  }, [dashboardQuery.isError]);

  const data = dashboardQuery.data;
  const tasks = useMemo(() => {
    const today = new Date().toISOString().slice(0, 10);
    return (data?.boardDetails || [])
      .flatMap((board) => board.columns.flatMap((column) => column.tasks))
      .filter((task) => task.due_date && task.due_date <= today)
      .slice(0, 8);
  }, [data]);

  const recentActivities = useMemo(() => data?.deals.items.flatMap((deal) => ({ ...deal, activity_hint: deal.updated_at })).sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at)).slice(0, 10) || [], [data]);
  const leadsByStage = useMemo(() => {
    const counts = new Map();
    (data?.contacts.items || []).forEach((contact) => counts.set(contact.lifecycle_stage, (counts.get(contact.lifecycle_stage) || 0) + 1));
    return [...counts.entries()].map(([name, value]) => ({ name, value }));
  }, [data]);

  const totalOpenValue = (data?.deals.items || []).filter((deal) => deal.status === 'open').reduce((sum, deal) => sum + deal.value, 0);
  const wonLast30 = (data?.deals.items || []).filter((deal) => deal.status === 'won' && deal.actual_close_date && (Date.now() - new Date(deal.actual_close_date).getTime()) < 30 * 86400000);
  const closedLast30 = (data?.deals.items || []).filter((deal) => deal.actual_close_date && (Date.now() - new Date(deal.actual_close_date).getTime()) < 30 * 86400000);
  const myDeals = (data?.deals.items || []).filter((deal) => deal.owner_id === user?.id).sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at)).slice(0, 5);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold">Deal command center</h1>
        <p className="text-muted-foreground">Pipeline health, deal metrics, and AI recommendations.</p>
      </div>
      {dashboardQuery.isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-64 w-full" />)}</div>
      ) : (
        <>
          <div className="grid gap-4 md:grid-cols-3">
            <SectionCard title="Open pipeline" description="Total value across active deals"><p className="text-3xl font-semibold">{formatCurrency(totalOpenValue)}</p></SectionCard>
            <SectionCard title="Status mix" description="Open, won, and lost deal counts">
              <div className="flex gap-2">
                {['open', 'won', 'lost'].map((status) => <Badge key={status}>{status}: {(data?.deals.items || []).filter((deal) => deal.status === status).length}</Badge>)}
              </div>
            </SectionCard>
            <SectionCard title="30-day win rate" description="Closed won ratio over the last 30 days">
              <p className="text-3xl font-semibold">{closedLast30.length ? `${Math.round((wonLast30.length / closedLast30.length) * 100)}%` : 'N/A'}</p>
            </SectionCard>
          </div>
          <div className="grid gap-4 xl:grid-cols-[1.3fr,1fr]">
            <SectionCard title="My deals" description="Most recently updated deals you own">
              <div className="space-y-3">{myDeals.length ? myDeals.map((deal) => <div key={deal.id} className="flex items-center justify-between rounded-xl bg-muted/40 px-4 py-3"><div><p className="font-medium">{deal.name}</p><p className="text-xs text-muted-foreground">{deal.stage_name}</p></div><span>{formatCurrency(deal.value, deal.currency)}</span></div>) : <p className="text-sm text-muted-foreground">No owned deals found.</p>}</div>
            </SectionCard>
            <SectionCard title="Leads by stage" description="Lifecycle distribution">
              {leadsByStage.length ? (
                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={leadsByStage} dataKey="value" nameKey="name" innerRadius={60} outerRadius={90}>
                        {leadsByStage.map((entry, index) => <Cell key={entry.name} fill={chartColors[index % chartColors.length]} />)}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              ) : <p className="text-sm text-muted-foreground">No contacts found.</p>}
            </SectionCard>
          </div>
          <div className="grid gap-4 xl:grid-cols-3">
            <SectionCard title="Today's tasks" description="Due today or overdue from active boards">
              <div className="space-y-3">{tasks.length ? tasks.map((task) => <div key={task.id} className="rounded-xl bg-muted/40 px-4 py-3"><p className="font-medium">{task.title}</p><p className="text-xs text-muted-foreground">Due {formatDate(task.due_date)} • {task.priority}</p></div>) : <p className="text-sm text-muted-foreground">Nothing due today.</p>}</div>
            </SectionCard>
            <SectionCard title="Recent activity" description="Latest deal updates">
              <div className="space-y-3">{recentActivities.length ? recentActivities.map((deal) => <div key={deal.id} className="rounded-xl bg-muted/40 px-4 py-3"><p className="font-medium">{deal.name}</p><p className="text-xs text-muted-foreground">Updated {formatDate(deal.updated_at, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })}</p></div>) : <p className="text-sm text-muted-foreground">No recent activity.</p>}</div>
            </SectionCard>
            <SectionCard title="AI suggestions" description="Proactive recommendations">
              <div className="space-y-3">{(data?.suggestions || []).length ? data.suggestions.map((item, index) => <div key={`${item.title}-${index}`} className="rounded-xl border border-primary/10 bg-primary/5 px-4 py-3"><div className="mb-2 flex items-center gap-2"><Badge variant="accent">{item.priority}</Badge><span className="text-sm font-medium">{item.title}</span></div><p className="text-sm text-muted-foreground">{item.description}</p></div>) : <p className="text-sm text-muted-foreground">No AI suggestions available.</p>}</div>
            </SectionCard>
          </div>
        </>
      )}
    </div>
  );
}
