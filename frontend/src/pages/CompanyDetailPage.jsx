import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useParams } from 'react-router-dom';
import { toast } from 'sonner';
import { getCompany, getCompanyContacts, getCompanyDeals, syncCompanyLinkedIn } from '@/api/companies';
import LinkedInPanel from '@/components/LinkedInPanel';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { formatCurrency, formatDate } from '@/lib/utils';

export default function CompanyDetailPage() {
  const { id } = useParams();
  const queryClient = useQueryClient();
  const companyQuery = useQuery({ queryKey: ['company', id], queryFn: () => getCompany(id) });
  const contactsQuery = useQuery({ queryKey: ['company', id, 'contacts'], queryFn: () => getCompanyContacts(id) });
  const dealsQuery = useQuery({ queryKey: ['company', id, 'deals'], queryFn: () => getCompanyDeals(id) });
  const syncMutation = useMutation({
    mutationFn: () => syncCompanyLinkedIn(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['company', id] });
      toast.success('Company synced with LinkedIn');
    }
  });

  if (companyQuery.isLoading) return <Skeleton className="h-[620px] w-full" />;
  const company = companyQuery.data;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold">{company.name}</h1>
        <p className="text-muted-foreground">{company.industry || 'Unknown industry'}{company.website ? ` \u2022 ${company.website}` : ''}</p>
      </div>
      <div className="grid gap-6 xl:grid-cols-[320px,1fr]">
        <div className="space-y-4">
          <Card><CardHeader><CardTitle>{company.name}</CardTitle></CardHeader><CardContent className="space-y-2"><p className="text-sm text-muted-foreground">{company.website || 'No website'}</p><p>{company.industry || 'Unknown industry'}</p><div className="flex gap-2"><Badge>{company.size_range || 'Unknown size'}</Badge><Badge variant="accent">{company.owner_name || 'Unassigned'}</Badge></div></CardContent></Card>
          <LinkedInPanel profile={company} onSync={() => syncMutation.mutate()} isSyncing={syncMutation.isPending} />
        </div>
        <div className="space-y-4">
          <Card><CardHeader><CardTitle>Stakeholders</CardTitle></CardHeader><CardContent className="space-y-3">{(contactsQuery.data || []).map((contact) => <div key={contact.id} className="rounded-xl bg-muted/40 p-4"><p className="font-medium">{contact.first_name} {contact.last_name}</p><p className="text-sm text-muted-foreground">{contact.title || 'No title'}</p></div>)}</CardContent></Card>
          <Card><CardHeader><CardTitle>Deals</CardTitle></CardHeader><CardContent className="space-y-3">{(dealsQuery.data || []).map((deal) => <div key={deal.id} className="flex items-center justify-between rounded-xl bg-muted/40 p-4"><div><p className="font-medium">{deal.name}</p><p className="text-sm text-muted-foreground">{deal.stage_name} • Updated {formatDate(deal.updated_at)}</p></div><span>{formatCurrency(deal.value, deal.currency)}</span></div>)}</CardContent></Card>
        </div>
      </div>
    </div>
  );
}
