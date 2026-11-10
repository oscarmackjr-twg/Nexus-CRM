import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Plus } from 'lucide-react';
import { toast } from 'sonner';
import { createContact } from '@/api/contacts';
import { createCompany } from '@/api/companies';
import { createDeal } from '@/api/deals';
import { getPipelines } from '@/api/pipelines';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

const CONFIG = {
  contact: { label: 'Contact', create: createContact, key: 'contacts', path: 'contacts', fields: [['first_name', 'First name'], ['last_name', 'Last name'], ['email', 'Email', 'email']] },
  company: { label: 'Company', create: createCompany, key: 'companies', path: 'companies', fields: [['name', 'Company name']] },
  deal: { label: 'Deal', create: createDeal, key: 'deals', path: 'deals', fields: [['name', 'Deal name']] },
};

export function CoreRecordCreateDialog({ entity, navigate }) {
  const config = CONFIG[entity];
  const [open, setOpen] = useState(false);
  const [values, setValues] = useState({});
  const [error, setError] = useState('');
  const queryClient = useQueryClient();
  const pipelinesQuery = useQuery({ queryKey: ['pipelines'], queryFn: getPipelines, enabled: open && entity === 'deal' });
  const selectedPipeline = useMemo(() => (pipelinesQuery.data || []).find((item) => item.id === values.pipeline_id), [pipelinesQuery.data, values.pipeline_id]);
  const mutation = useMutation({
    mutationFn: config.create,
    onSuccess: async (record) => {
      await queryClient.invalidateQueries({ queryKey: [config.key] });
      setOpen(false); setValues({}); setError(''); toast.success(`${config.label} created`); navigate(`/${config.path}/${record.id}`);
    },
    onError: () => setError(`We could not create this ${config.label.toLowerCase()}. Your entries were kept—please try again.`),
  });
  const submit = (event) => {
    event.preventDefault();
    const required = entity === 'contact'
      ? ['first_name', 'last_name']
      : entity === 'company'
        ? ['name']
        : ['name', 'pipeline_id', 'stage_id'];
    if (required.some((key) => !values[key])) return setError('Complete the required fields to continue.');
    const providedValues = Object.fromEntries(Object.entries(values).filter(([, value]) => value !== ''));
    const payload = entity === 'deal' ? { ...providedValues, value: Number(providedValues.value || 0) } : providedValues;
    mutation.mutate(payload);
  };
  return <Dialog open={open} onOpenChange={setOpen}>
    <Button onClick={() => setOpen(true)}><Plus className="h-4 w-4" />New {config.label}</Button>
    <DialogContent><DialogHeader><DialogTitle>New {config.label}</DialogTitle><DialogDescription>Create a core record without leaving this list.</DialogDescription></DialogHeader>
      <form onSubmit={submit} noValidate className="space-y-4">{config.fields.map(([key, label, type]) => <div key={key} className="space-y-2"><Label htmlFor={`${entity}-${key}`}>{label}</Label><Input id={`${entity}-${key}`} type={type || 'text'} value={values[key] || ''} onChange={(e) => setValues((current) => ({ ...current, [key]: e.target.value }))} /></div>)}
      {entity === 'deal' && <><div className="space-y-2"><Label htmlFor="deal-pipeline">Pipeline</Label><select id="deal-pipeline" className="h-9 w-full rounded-md border px-3 text-sm" value={values.pipeline_id || ''} onChange={(e) => setValues((current) => ({ ...current, pipeline_id: e.target.value, stage_id: '' }))}><option value="">Select a pipeline</option>{(pipelinesQuery.data || []).map((pipeline) => <option key={pipeline.id} value={pipeline.id}>{pipeline.name}</option>)}</select></div><div className="space-y-2"><Label htmlFor="deal-stage">Stage</Label><select id="deal-stage" disabled={!selectedPipeline} className="h-9 w-full rounded-md border px-3 text-sm" value={values.stage_id || ''} onChange={(e) => setValues((current) => ({ ...current, stage_id: e.target.value }))}><option value="">Select a stage</option>{(selectedPipeline?.stages || []).map((stage) => <option key={stage.id} value={stage.id}>{stage.name}</option>)}</select></div><div className="space-y-2"><Label htmlFor="deal-value">Value (optional)</Label><Input id="deal-value" type="number" min="0" value={values.value || ''} onChange={(e) => setValues((current) => ({ ...current, value: e.target.value }))} /></div></>}
      {error ? <p role="alert" className="text-sm text-destructive">{error}</p> : null}<DialogFooter><Button type="submit" disabled={mutation.isPending}>{mutation.isPending ? 'Creating…' : `Create ${config.label}`}</Button></DialogFooter></form>
    </DialogContent></Dialog>;
}
