import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { toast } from 'sonner';
import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

const schema = z.object({
  username: z.string().min(1, 'Email is required'),
  password: z.string().min(1, 'Password is required')
});

export default function LoginPage() {
  const navigate = useNavigate();
  const { login, isAuthenticated } = useAuth();
  const [backendStatus, setBackendStatus] = useState('checking');
  const form = useForm({
    resolver: zodResolver(schema),
    defaultValues: { username: '', password: '' }
  });

  useEffect(() => {
    if (isAuthenticated) navigate('/');
  }, [isAuthenticated, navigate]);

  useEffect(() => {
    fetch('/health')
      .then((r) => r.ok ? setBackendStatus('connected') : setBackendStatus('unavailable'))
      .catch(() => setBackendStatus('unavailable'));
  }, []);

  async function onSubmit(values) {
    try {
      await login(values);
      navigate('/');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Unable to sign in');
    }
  }

  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center bg-[radial-gradient(circle_at_top_left,_rgba(99,102,241,0.35),_transparent_35%),linear-gradient(135deg,_#0f172a,_#111827_50%,_#062b3b)] p-6">
      {/* Staging banner — per D-03 */}
      {import.meta.env.MODE !== 'production' && (
        <div className="absolute inset-x-0 top-0 bg-amber-500/90 py-1.5 text-center text-xs font-semibold text-black">
          {import.meta.env.MODE.toUpperCase()} ENVIRONMENT
        </div>
      )}

      <div className="flex w-full max-w-md flex-col items-center gap-6">
        {/* TWG Global logo placeholder — per D-03 */}
        {/* TODO: replace with actual logo */}
        <span className="text-lg font-bold tracking-widest text-white/80">TWG GLOBAL</span>

        {/* App name — per D-03 */}
        <h1 className="text-3xl font-semibold text-white">Nexus CRM</h1>

        {/* Sign-in card */}
        <Card className="w-full border-white/10 bg-slate-950/70 text-white shadow-2xl backdrop-blur">
          <CardContent className="pt-6">
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input id="email" {...form.register('username')} placeholder="admin@demo.local" className="border-white/10 bg-white/5 text-white placeholder:text-white/40" />
                {form.formState.errors.username && <p className="text-sm text-red-300">{form.formState.errors.username.message}</p>}
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input id="password" type="password" {...form.register('password')} className="border-white/10 bg-white/5 text-white placeholder:text-white/40" />
                {form.formState.errors.password && <p className="text-sm text-red-300">{form.formState.errors.password.message}</p>}
              </div>
              <Button type="submit" className="w-full" disabled={form.formState.isSubmitting}>Sign in</Button>
            </form>
          </CardContent>
        </Card>

        {/* Backend status indicator — per D-03 */}
        <div className="flex items-center gap-1.5 text-xs">
          <span className={`h-2 w-2 rounded-full ${backendStatus === 'connected' ? 'bg-green-400' : backendStatus === 'unavailable' ? 'bg-red-400' : 'bg-yellow-400'}`} />
          <span className="text-white/50">
            Backend: {backendStatus === 'connected' ? 'Connected' : backendStatus === 'unavailable' ? 'Unavailable' : 'Checking...'}
          </span>
        </div>
      </div>
    </div>
  );
}
