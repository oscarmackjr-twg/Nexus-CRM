import { useEffect, useState } from 'react';
import { Link, NavLink, Outlet } from 'react-router-dom';
import {
  BarChart3,
  Bell,
  BookOpen,
  Building2,
  ChevronLeft,
  ChevronRight,
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
import { useUIStore } from '@/store/useUIStore';
import { useAuth } from '@/hooks/useAuth';
import { Avatar } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';
import TeamSelector from './TeamSelector';
import AIQueryBar from './AIQueryBar';

const navSections = [
  { label: 'Dashboard', items: [{ name: 'Dashboard', href: '/', icon: Home }] },
  { label: 'CRM', items: [{ name: 'Contacts', href: '/contacts', icon: Users }, { name: 'Companies', href: '/companies', icon: Building2 }, { name: 'Pipelines', href: '/pipelines', icon: KanbanSquare }] },
  { label: 'Work', items: [{ name: 'Boards', href: '/boards', icon: Workflow }, { name: 'Pages', href: '/pages', icon: BookOpen }] },
  { label: 'Automation', items: [{ name: 'Automations', href: '/automations', icon: Zap }] },
  { label: 'Analytics', items: [{ name: 'Analytics', href: '/analytics', icon: BarChart3 }] },
  { label: 'AI', items: [{ name: 'AI Assistant', href: '/ai', icon: Sparkles }] },
  { label: 'LinkedIn', items: [{ name: 'LinkedIn', href: '/linkedin', icon: Linkedin }] }
];

export default function Layout() {
  const { sidebarCollapsed, toggleSidebar } = useUIStore();
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
      <div className="fixed inset-0 -z-10 bg-gradient-to-br from-primary/8 via-transparent to-accent/10" />
      <div className="fixed inset-0 -z-10 surface-grid opacity-50" />
      <aside className={cn('fixed inset-y-0 left-0 z-30 flex flex-col bg-slate-900 text-slate-100 transition-all', sidebarCollapsed ? 'w-16' : 'w-60')}>
        <div className="flex items-center justify-between px-4 py-4">
          <Link to="/" className="flex items-center gap-3 overflow-hidden">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-primary font-bold text-white">N</div>
            {!sidebarCollapsed && <div><p className="font-semibold">Nexus CRM</p><p className="text-xs text-muted-foreground">Revenue OS</p></div>}
          </Link>
          <Button variant="ghost" size="icon" onClick={toggleSidebar}>
            {sidebarCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </Button>
        </div>
        <div className="flex-1 space-y-6 overflow-auto px-3 pb-4">
          {navSections.map((section) => (
            <div key={section.label} className="space-y-2">
              {!sidebarCollapsed && <p className="px-2 text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">{section.label}</p>}
              <div className="space-y-1">
                {section.items.map((item) => (
                  <NavLink
                    key={item.href}
                    to={item.href}
                    className={({ isActive }) => cn('flex items-center gap-3 rounded-xl px-3 py-2 text-sm text-slate-300 transition hover:bg-slate-700/60 hover:text-white', isActive && 'bg-blue-600/30 text-blue-300')}
                  >
                    <item.icon className="h-4 w-4 shrink-0" />
                    {!sidebarCollapsed && <span>{item.name}</span>}
                  </NavLink>
                ))}
              </div>
            </div>
          ))}
        </div>
        <div className="space-y-3 border-t border-slate-700 p-3">
          {!sidebarCollapsed && <TeamSelector />}
          <div className="flex items-center gap-3 rounded-2xl bg-slate-800 p-2">
            <Avatar alt={user?.full_name || user?.username} src={user?.avatar_url} />
            {!sidebarCollapsed && (
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-slate-100">{user?.full_name || user?.username}</p>
                <Link to="/settings/team" className="text-xs text-slate-400 hover:text-slate-200">Settings</Link>
              </div>
            )}
          </div>
        </div>
      </aside>
      <div className={cn('transition-all', sidebarCollapsed ? 'pl-16' : 'pl-60')}>
        <header className="sticky top-0 z-20 border-b bg-background/80 backdrop-blur">
          <div className="flex items-center gap-3 px-6 py-4">
            <div className="relative flex-1">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input readOnly value="" placeholder="Search everything... (Cmd+K)" className="pl-9" onClick={() => setCommandOpen(true)} />
            </div>
            <Button variant="outline" onClick={() => setCommandOpen(true)}>
              <Sparkles className="h-4 w-4" />
              AI Quick Query
            </Button>
            <Button variant="ghost" size="icon"><Bell className="h-4 w-4" /></Button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button className="rounded-full"><Avatar alt={user?.full_name || user?.username} src={user?.avatar_url} className="h-9 w-9" /></button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem asChild><Link to="/settings/team"><Settings className="mr-2 h-4 w-4" />Team settings</Link></DropdownMenuItem>
                <DropdownMenuItem onSelect={() => logout()}>Sign out</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>
        <main className="p-6">
          <Outlet />
        </main>
      </div>
      <AIQueryBar open={commandOpen} onOpenChange={setCommandOpen} />
    </div>
  );
}
