import { create } from 'zustand';

const savedCollapsed = localStorage.getItem('nexus-sidebar-collapsed') === 'true';

export const useUIStore = create((set) => ({
  sidebarCollapsed: savedCollapsed,
  toggleSidebar: () => set((state) => {
    const next = !state.sidebarCollapsed;
    localStorage.setItem('nexus-sidebar-collapsed', String(next));
    return { sidebarCollapsed: next };
  })
}));
