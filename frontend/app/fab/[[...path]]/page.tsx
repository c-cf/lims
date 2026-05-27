"use client";
import React, { use, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { makeFabNavigate } from '@/lib/navigate';
import FabDashboard from '@/components/Fab/FabDashboard';
import FabRequestList from '@/components/Fab/FabRequestList';
import FabNewRequest from '@/components/Fab/FabNewRequest';
import FabDraftEdit from '@/components/Fab/FabDraftEdit';
import FabRequestDetail from '@/components/Fab/FabRequestDetail';

export default function FabPage({ params }: { params: Promise<{ path?: string[] }> }) {
  const { path = [] } = use(params);
  const searchParams = useSearchParams();
  const router = useRouter();
  const navigate = makeFabNavigate(router.push.bind(router));
  const [toast, setToast] = useState(null);

  const showToast = (msg: string) => {
    setToast({ msg, t: Date.now() });
    setTimeout(() => setToast(null), 2200);
  };

  const [seg0, seg1] = path;

  let page: React.ReactNode;
  if (!seg0 || seg0 === 'dashboard') {
    page = <FabDashboard navigate={navigate} />;
  } else if (seg0 === 'requests') {
    if (seg1 === 'new') {
      page = <FabNewRequest navigate={navigate} showToast={showToast} />;
    } else if (seg1) {
      page = <FabRequestDetail id={Number(seg1)} navigate={navigate} showToast={showToast} />;
    } else {
      page = <FabRequestList navigate={navigate} initialTab={searchParams.get('tab') || 'all'} />;
    }
  } else if (seg0 === 'drafts') {
    if (seg1) {
      page = <FabDraftEdit id={Number(seg1)} navigate={navigate} showToast={showToast} />;
    } else {
      page = <FabRequestList navigate={navigate} drafts titleOverride="Drafts" />;
    }
  } else {
    page = <FabDashboard navigate={navigate} />;
  }

  return (
    <>
      {page}
      {toast && (
        <div style={{
          position: 'fixed', bottom: 28, left: '50%', transform: 'translateX(-50%)',
          padding: '12px 20px', borderRadius: 10, background: '#1e1e24', color: '#fff',
          fontSize: 14, fontWeight: 500, boxShadow: '0 12px 36px rgba(30,30,36,0.32)',
          animation: 'slide-in 0.18s ease-out', zIndex: 100,
        }}>{toast.msg}</div>
      )}
    </>
  );
}
