import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUIStore } from '@/store/useUIStore';
import client from '@/api/client';

export function useAuth() {
  const { user, setUser, clearUser } = useUIStore();
  const navigate = useNavigate();

  const isAuthenticated = !!user;

  const login = useCallback(async (credentials) => {
    const params = new URLSearchParams();
    params.append('username', credentials.username);
    params.append('password', credentials.password);

    const { data } = await client.post('/auth/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });

    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);

    const { data: me } = await client.get('/auth/me');
    setUser(me);
    return me;
  }, [setUser]);

  const logout = useCallback(async () => {
    try {
      const refresh_token = localStorage.getItem('refresh_token');
      if (refresh_token) {
        await client.post('/auth/logout', { refresh_token });
      }
    } catch {
      // ignore
    }
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    clearUser();
    navigate('/login');
  }, [clearUser, navigate]);

  return { user, isAuthenticated, login, logout };
}
