import { useEffect, useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import {
  BarChart3,
  BookOpen,
  Building2,
  Home,
  KanbanSquare,
  Linkedin,
  Settings,
  Sparkles,
  Users,
  Workflow,
  Zap
} from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { cn } from '@/lib/utils';
import AIQueryBar from './AIQueryBar';
import StagingBanner from './StagingBanner';
import twgLogo from '@/assets/twg-logo.png';

const navGroups = [
  {
    label: null,
    items: [{ name: 'Dashboard', href: '/', icon: Home, exact: true }]
  },
  {
    label: 'DEALS',
    items: [
      { name: 'Contacts', href: '/contacts', icon: Users },
      { name: 'Companies', href: '/companies', icon: Building2 },
      { name: 'Pipelines', href: '/pipelines', icon: KanbanSquare },
      { name: 'Boards', href: '/boards', icon: Workflow },
    ]
  },
  {
    label: 'TOOLS',
    items: [
      { name: 'Pages', href: '/pages', icon: BookOpen },
      { name: 'Automations', href: '/automations', icon: Zap },
      { name: 'Analytics', href: '/analytics', icon: BarChart3 },
      { name: 'AI', href: '/ai', icon: Sparkles },
      { name: 'LinkedIn', href: '/linkedin', icon: Linkedin },
    ]
  },
  {
    label: 'ADMIN',
    items: [
      { name: 'Admin', href: '/admin', icon: Settings },
      { name: 'Team Settings', href: '/settings/team', icon: Settings },
    ]
  }
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
    <div className="flex flex-col min-h-screen">
      <StagingBanner />
      <div className="flex flex-1">
        {/* Sidebar per D-02 */}
        <aside className="w-60 min-h-full flex flex-col bg-white border-r border-gray-200 sticky top-0 h-screen">
          {/* Logo header per D-12 */}
          <div className="px-5 py-5 border-b border-gray-200">
            <img src={twgLogo} alt="TWG Global" className="h-8 w-auto" />
            <p className="mt-1 text-xs font-semibold tracking-widest text-[#1a3868] uppercase">
              Nexus CRM
            </p>
          </div>

          {/* Nav list */}
          <nav className="flex-1 overflow-y-auto py-2">
            {navGroups.map((group, gi) => (
              <div key={gi}>
                {/* Section label per D-07 — only if group.label is not null */}
                {group.label && (
                  <span className="px-5 pt-4 pb-1 text-xs font-bold tracking-widest text-[#94a3b8] uppercase select-none block">
                    {group.label}
                  </span>
                )}
                {group.items.map((item) => (
                  <NavLink
                    key={item.href}
                    to={item.href}
                    end={item.exact}
                    className={({ isActive }) =>
                      cn(
                        'px-5 py-2 text-sm flex items-center gap-2 border-l-4 transition-colors',
                        isActive
                          ? 'border-[#1a3868] text-[#1a3868] font-semibold bg-gray-50'
                          : 'border-transparent text-[#475569] hover:text-[#1a3868] hover:bg-gray-50'
                      )
                    }
                  >
                    <item.icon className="h-4 w-4 shrink-0" />
                    <span>{item.name}</span>
                  </NavLink>
                ))}
              </div>
            ))}
          </nav>

          {/* User footer per D-13 */}
          <div className="px-5 py-4 border-t border-gray-200 mt-auto">
            <p className="text-xs text-[#475569] truncate">{user?.full_name || user?.username}</p>
            <p className="text-xs text-[#94a3b8] capitalize mb-3">{user?.role}</p>
            <button
              onClick={() => logout()}
              className="text-xs text-[#475569] hover:text-[#1a3868] font-medium"
            >
              Sign out
            </button>
          </div>
        </aside>

        {/* Main content per D-03 */}
        <main className="flex-1 bg-[#f8fafc] min-h-screen">
          <div className="p-6">
            <Outlet />
          </div>
        </main>
      </div>

      <AIQueryBar open={commandOpen} onOpenChange={setCommandOpen} />
    </div>
  );
}
