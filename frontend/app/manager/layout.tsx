'use client';
import React, { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Sidebar from '@/components/Shell/Sidebar';
import NAV_ITEMS from '@/components/Shell/NAV_ITEMS';
import TweaksUI from '@/components/App/TweaksUI';
import useTweaks from '@/components/Tweaks/useTweaks';
import { SESSION_KEY, TWEAK_DEFAULTS } from '@/components/App/constants';
import { makeMgrNavigate, roleHome } from '@/lib/navigate';
import api from '@/lib/api';

function pathToMgrPage(pathname: string): string {
  if (pathname.startsWith('/manager/requests/')) return 'mgr_all_requests';
  if (pathname.startsWith('/manager/requests')) return 'mgr_all_requests';
  if (pathname.startsWith('/manager/recipes')) return 'mgr_recipes';
  if (pathname.startsWith('/manager/reports')) return 'mgr_reports';
  if (pathname.startsWith('/manager/lab/samples')) return 'lab_samples';
  if (pathname.startsWith('/manager/lab/wips')) return 'lab_wip';
  if (pathname.startsWith('/manager/lab/dispatches')) return 'lab_dispatches';
  if (pathname.startsWith('/manager/lab/equipment')) return 'lab_equipment';
  if (pathname.startsWith('/manager/lab')) return 'lab_dashboard';
  return 'mgr_dashboard';
}

type AuthState = { user: Record<string, unknown> | null; ok: boolean };

export default function ManagerLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [auth, setAuth] = useState<AuthState>({ user: null, ok: false });
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(SESSION_KEY);
      if (!stored) {
        router.replace('/login');
        return;
      }
      const u = JSON.parse(stored);
      if (u.role !== 'lab_manager') {
        router.replace(roleHome(u.role));
        return;
      }
      setAuth({ user: u, ok: true });
    } catch {
      router.replace('/login');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (!auth.ok) return null;

  const navigate = makeMgrNavigate(router.push.bind(router));
  const currentPage = pathToMgrPage(pathname);

  const LAB_NAV = NAV_ITEMS.filter((n) => n.id !== 'dashboard').map((n) => ({
    ...n,
    id: 'lab_' + n.id,
  }));
  const MGR_NAV = [
    { id: 'mgr_dashboard', label: 'Dashboard', cn: '儀表板', icon: 'Home' },
    { id: 'mgr_all_requests', label: 'All Requests', cn: '全部申請', icon: 'ClipboardList' },
    { id: 'mgr_recipes', label: 'Recipes', cn: '食譜', icon: 'Layers' },
    { id: 'mgr_reports', label: 'Reports', cn: '報表', icon: 'TrendUp' },
  ];
  const navSections = [
    { label: 'Management', items: MGR_NAV },
    { label: 'Lab Operations', items: LAB_NAV },
  ];

  const onLogout = () => {
    localStorage.removeItem(SESSION_KEY);
    api.auth.logout().catch(() => {});
    router.push('/login');
  };

  return (
    <div className="app" data-screen-label={`App · lab_manager · ${currentPage}`}>
      <Sidebar
        route={{ page: currentPage }}
        navigate={navigate}
        navSections={navSections}
        user={auth.user}
        onLogout={onLogout}
      />
      <main className="main">{children}</main>
      <TweaksUI t={t} setTweak={setTweak} />
    </div>
  );
}
