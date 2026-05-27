"use client";
import React, { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Sidebar from '@/components/Shell/Sidebar';
import FAB_NAV_ITEMS from '@/components/Shell/FAB_NAV_ITEMS';
import TweaksUI from '@/components/App/TweaksUI';
import useTweaks from '@/components/Tweaks/useTweaks';
import { SESSION_KEY, TWEAK_DEFAULTS } from '@/components/App/constants';
import { makeFabNavigate, roleHome } from '@/lib/navigate';
import api from '@/lib/api';

function pathToFabPage(pathname: string): string {
  if (pathname.startsWith('/fab/requests/new')) return 'fab_new';
  if (pathname.startsWith('/fab/requests/'))   return 'fab_requests';
  if (pathname.startsWith('/fab/requests'))    return 'fab_requests';
  if (pathname.startsWith('/fab/drafts/'))     return 'fab_drafts';
  if (pathname.startsWith('/fab/drafts'))      return 'fab_drafts';
  return 'fab_dashboard';
}

type AuthState = { user: Record<string, unknown> | null; ok: boolean };

export default function FabLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [auth, setAuth] = useState<AuthState>({ user: null, ok: false });
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);

  useEffect(() => {
    const root = document.documentElement;
    root.style.setProperty('--tweak-fab-bg', t.fabBg);
  }, [t.fabBg]);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(SESSION_KEY);
      if (!stored) { router.replace('/login'); return; }
      const u = JSON.parse(stored);
      if (u.role !== 'fab_user') { router.replace(roleHome(u.role)); return; }
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setAuth({ user: u, ok: true });
    } catch { router.replace('/login'); }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (!auth.ok) return null;

  const navigate = makeFabNavigate(router.push.bind(router));
  const currentPage = pathToFabPage(pathname);

  const onLogout = () => {
    localStorage.removeItem(SESSION_KEY);
    api.auth.logout().catch(() => {});
    router.push('/login');
  };

  return (
    <div className="app" data-screen-label={`App · fab_user · ${currentPage}`}>
      <Sidebar
        route={{ page: currentPage }}
        navigate={navigate}
        navItems={FAB_NAV_ITEMS}
        sectionLabel="Requests"
        user={auth.user}
        onLogout={onLogout}
      />
      <main className="main">{children}</main>
      <TweaksUI t={t} setTweak={setTweak} />
    </div>
  );
}
