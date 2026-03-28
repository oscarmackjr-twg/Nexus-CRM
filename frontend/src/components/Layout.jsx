import { useEffect, useState } from 'react';
import { Link, NavLink, Outlet } from 'react-router-dom';
import {
  BarChart3,
  Bell,
  BookOpen,
  Building2,
  Home,
  KanbanSquare,
  Linkedin,
  Search,
  Settings,
  Sparkles,
  Users,
  Workflow,
  Zap
} from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { Avatar } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';
import AIQueryBar from './AIQueryBar';

const navItems = [
  { name: 'Dashboard', href: '/', icon: Home, exact: true },
  { name: 'Contacts', href: '/contacts', icon: Users },
  { name: 'Companies', href: '/companies', icon: Building2 },
  { name: 'Pipelines', href: '/pipelines', icon: KanbanSquare },
  { name: 'Boards', href: '/boards', icon: Workflow },
  { name: 'Pages', href: '/pages', icon: BookOpen },
  { name: 'Automations', href: '/automations', icon: Zap },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  { name: 'AI', href: '/ai', icon: Sparkles },
  { name: 'LinkedIn', href: '/linkedin', icon: Linkedin },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const [commandOpen, setCommandOpen] = useState(false);

  useEffect(() => {
    document.documentElement.classList.remove('dark');
  }, []);

  useEffect(() => {
    const handler = (event) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        setCommandOpen((open) => !open);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Top navigation bar */}
      <header className="fixed inset-x-0 top-0 z-30 bg-slate-900 text-slate-100 shadow-md">
        <div className="flex items-center gap-4 px-4 h-14">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 shrink-0 mr-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-blue-500 font-bold text-white text-sm">N</div>
            <span className="font-semibold text-sm hidden sm:block">Nexus CRM</span>
          </Link>

          {/* Nav links */}
          <nav className="flex items-center gap-1 flex-1 overflow-x-auto scrollbar-none">
            {navItems.map((item) => (
              <NavLink
                key={item.href}
                to={item.href}
                end={item.exact}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm whitespace-nowrap transition-colors',
                    isActive
                      ? 'bg-blue-600/40 text-blue-200'
                      : 'text-slate-300 hover:bg-slate-700/60 hover:text-white'
                  )
                }
              >
                <item.icon className="h-4 w-4 shrink-0" />
                <span>{item.name}</span>
              </NavLink>
            ))}
          </nav>

          {/* Right actions */}
          <div className="flex items-center gap-2 shrink-0">
            <Button
              variant="ghost"
              size="sm"
              className="text-slate-300 hover:text-white hover:bg-slate-700/60 hidden md:flex"
              onClick={() => setCommandOpen(true)}
            >
              <Search className="h-4 w-4 mr-1.5" />
              <span className="text-xs text-slate-400">⌘K</span>
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="text-slate-300 hover:text-white hover:bg-slate-700/60"
              onClick={() => setCommandOpen(true)}
            >
              <Sparkles className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="icon" className="text-slate-300 hover:text-white hover:bg-slate-700/60">
              <Bell className="h-4 w-4" />
            </Button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button className="rounded-full ml-1">
                  <Avatar alt={user?.full_name || user?.username} src={user?.avatar_url} className="h-8 w-8" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem asChild>
                  <Link to="/settings/team"><Settings className="mr-2 h-4 w-4" />Team settings</Link>
                </DropdownMenuItem>
                <DropdownMenuItem onSelect={() => logout()}>Sign out</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </header>

      {/* Page content — offset by navbar height */}
      <main className="pt-14 p-6">
        <Outlet />
      </main>

      <AIQueryBar open={commandOpen} onOpenChange={setCommandOpen} />
    </div>
  );
}
