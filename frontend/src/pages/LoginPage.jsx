import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { toast } from 'sonner';
import { useAuth } from '@/hooks/useAuth';
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
    <div className="min-h-screen flex flex-col bg-[#f8fafc]">
      <StagingBanner />

      <div className="flex-1 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8">
          <div>
            <img src={twgLogo} alt="TWG Global" className="mx-auto h-12 w-auto" />
            <h2 className="mt-4 text-center text-3xl font-bold text-[#1a3868]">Nexus CRM</h2>
            <p className="mt-2 text-center text-sm text-gray-600">Sign in to your account</p>
            <p className="mt-1 text-center text-xs text-gray-500" aria-live="polite">
              {backendStatus === 'connected' ? 'Backend connected' : backendStatus === 'unavailable' ? 'Backend unavailable' : 'Checking backend...'}
            </p>
          </div>

          <form className="mt-8 space-y-6" onSubmit={form.handleSubmit(onSubmit)}>
            <div className="rounded-md shadow-sm -space-y-px">
              <div>
                <label htmlFor="username" className="sr-only">Username</label>
                <input
                  id="username"
                  type="text"
                  placeholder="Email"
                  {...form.register('username')}
                  className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-[#1a3868] focus:border-[#1a3868] focus:z-10 sm:text-sm"
                />
                {form.formState.errors.username && (
                  <p className="mt-1 text-xs text-red-500">{form.formState.errors.username.message}</p>
                )}
              </div>
              <div>
                <label htmlFor="password" className="sr-only">Password</label>
                <input
                  id="password"
                  type="password"
                  placeholder="Password"
                  {...form.register('password')}
                  className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-[#1a3868] focus:border-[#1a3868] focus:z-10 sm:text-sm"
                />
                {form.formState.errors.password && (
                  <p className="mt-1 text-xs text-red-500">{form.formState.errors.password.message}</p>
                )}
              </div>
            </div>

            <div>
              <button
                type="submit"
                disabled={form.formState.isSubmitting}
                className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-[#1a3868] hover:bg-[#15305a] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#1a3868] disabled:opacity-60"
              >
                Sign in
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
