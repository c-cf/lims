'use client';
import React, { useState } from 'react';
import Sidebar from '@/components/Shell/Sidebar';
import FAB_NAV_ITEMS from '@/components/Shell/FAB_NAV_ITEMS';
import FabApp from '@/components/Fab/FabApp';
import type { AppShellProps } from '@/lib/types';
export default function FabRoot({ user, onLogout, tweaksUI }: AppShellProps) {
  const [route, setRoute] = useState<{ page: string; tab?: string; id?: number | string }>({
    page: 'fab_dashboard',
  });
  const navigate = (r: { page: string; tab?: string; id?: number | string }) => setRoute(r);
  const navFromSidebar = (r: { page: string; tab?: string; id?: number | string }) => {
    if (r.page === 'fab_requests') setRoute({ page: 'fab_requests', tab: 'all' });
    else setRoute(r);
  };
  return (
    <div className="app" data-screen-label={`App · fab_user · ${route.page}`}>
      <Sidebar
        route={route}
        navigate={navFromSidebar}
        navItems={FAB_NAV_ITEMS}
        sectionLabel="Requests"
        user={user}
        onLogout={onLogout}
      />
      <main className="main">
        <FabApp route={route} navigate={navigate} />
      </main>
      {tweaksUI}
    </div>
  );
}
