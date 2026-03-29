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
import StagingBanner from '@/components/StagingBanner';
import twgLogo from '@/assets/twg-logo.png';

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
    <div className="relative flex min-h-screen flex-col items-center justify-center bg-slate-50 p-6">
      <StagingBanner />

      <div className="flex w-full max-w-md flex-col items-center gap-6">
        <img src={twgLogo} alt="TWG Global" className="h-10 w-auto" />

        {/* App name — per D-03 */}
        <h1 className="text-3xl font-semibold text-slate-900">Nexus CRM</h1>

        {/* Sign-in card */}
        <Card className="w-full border-slate-200 bg-white shadow-soft">
          <CardContent className="pt-6">
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email" className="text-slate-700">Email</Label>
                <Input id="email" {...form.register('username')} placeholder="admin@demo.local" className="border-slate-200 bg-white text-slate-900 placeholder:text-slate-400" />
                {form.formState.errors.username && <p className="text-sm text-red-500">{form.formState.errors.username.message}</p>}
              </div>
              <div className="space-y-2">
                <Label htmlFor="password" className="text-slate-700">Password</Label>
                <Input id="password" type="password" {...form.register('password')} className="border-slate-200 bg-white text-slate-900" />
                {form.formState.errors.password && <p className="text-sm text-red-500">{form.formState.errors.password.message}</p>}
              </div>
              <Button type="submit" className="w-full bg-primary text-primary-foreground hover:bg-primary/90" disabled={form.formState.isSubmitting}>Sign in</Button>
            </form>
          </CardContent>
        </Card>

        {/* Backend status indicator — per D-03 */}
        <div className="flex items-center gap-1.5 text-xs">
          <span className={`h-2 w-2 rounded-full ${backendStatus === 'connected' ? 'bg-green-500' : backendStatus === 'unavailable' ? 'bg-red-500' : 'bg-yellow-400'}`} />
          <span className="text-slate-400">
            Backend: {backendStatus === 'connected' ? 'Connected' : backendStatus === 'unavailable' ? 'Unavailable' : 'Checking...'}
          </span>
        </div>
      </div>
    </div>
  );
}
