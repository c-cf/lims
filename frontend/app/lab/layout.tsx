'use client';
import React, { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Sidebar from '@/components/Shell/Sidebar';
import NAV_ITEMS from '@/components/Shell/NAV_ITEMS';
import TweaksUI from '@/components/App/TweaksUI';
import useTweaks from '@/components/Tweaks/useTweaks';
import { SESSION_KEY, TWEAK_DEFAULTS } from '@/components/App/constants';
import { makeLabNavigate, roleHome } from '@/lib/navigate';
import api from '@/lib/api';

function pathToLabPage(pathname: string): string {
  if (pathname.startsWith('/lab/samples/')) return 'lab_samples';
  if (pathname.startsWith('/lab/samples')) return 'lab_samples';
  if (pathname.startsWith('/lab/wips/')) return 'lab_wip';
  if (pathname.startsWith('/lab/wips')) return 'lab_wip';
  if (pathname.startsWith('/lab/dispatches/')) return 'lab_dispatches';
  if (pathname.startsWith('/lab/dispatches')) return 'lab_dispatches';
  if (pathname.startsWith('/lab/equipment')) return 'lab_equipment';
  return 'lab_dashboard';
}

type AuthState = { user: Record<string, unknown> | null; ok: boolean };

export default function LabLayout({ children }: { children: React.ReactNode }) {
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
      if (u.role !== 'lab_member' && u.role !== 'lab_mem') {
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

  const navigate = makeLabNavigate(router.push.bind(router));
  const currentPage = pathToLabPage(pathname);
  const LAB_NAV = NAV_ITEMS.map((n) => ({ ...n, id: 'lab_' + n.id }));

  const onLogout = () => {
    localStorage.removeItem(SESSION_KEY);
    api.auth.logout().catch(() => {});
    router.push('/login');
  };

  return (
    <div className="app" data-screen-label={`App · lab_member · ${currentPage}`}>
      <Sidebar
        route={{ page: currentPage }}
        navigate={navigate}
        navItems={LAB_NAV}
        sectionLabel="Lab Operations"
        sublabel="Lab Member"
        user={auth.user}
        onLogout={onLogout}
      />
      <main className="main">{children}</main>
      <TweaksUI t={t} setTweak={setTweak} />
    </div>
  );
}
