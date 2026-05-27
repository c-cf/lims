"use client";
import React, { use, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { makeLabNavigate } from '@/lib/navigate';
import { ink } from '@/lib/colors';
import LabDashboard from '@/components/Lab/LabDashboard';
import LabSamples from '@/components/Lab/LabSamples';
import LabWaferDetail from '@/components/Lab/LabWaferDetail';
import LabWipList from '@/components/Lab/LabWipList';
import LabWipDetail from '@/components/Lab/LabWipDetail';
import LabDispatchList from '@/components/Lab/LabDispatchList';
import LabDispatchDetail from '@/components/Lab/LabDispatchDetail';
import LabEquipment from '@/components/Lab/LabEquipment';

export default function LabPage({ params }: { params: Promise<{ path?: string[] }> }) {
  const { path = [] } = use(params);
  const searchParams = useSearchParams();
  const router = useRouter();
  const navigate = makeLabNavigate(router.push.bind(router));
  const [toast, setToast] = useState(null);

  const showToast = (msg: string) => {
    setToast({ msg, t: Date.now() });
    setTimeout(() => setToast(null), 2200);
  };

  const [seg0, seg1] = path;

  let page: React.ReactNode;
  if (!seg0 || seg0 === 'dashboard') {
    page = <LabDashboard navigate={navigate} />;
  } else if (seg0 === 'samples') {
    if (seg1) {
      page = <LabWaferDetail id={Number(seg1)} navigate={navigate} showToast={showToast} />;
    } else {
      page = <LabSamples navigate={navigate} defaultTab={searchParams.get('tab') || 'all'} showToast={showToast} />;
    }
  } else if (seg0 === 'wips') {
    if (seg1) {
      page = <LabWipDetail id={Number(seg1)} navigate={navigate} showToast={showToast} />;
    } else {
      page = <LabWipList navigate={navigate} showToast={showToast} />;
    }
  } else if (seg0 === 'dispatches') {
    if (seg1) {
      page = <LabDispatchDetail id={Number(seg1)} navigate={navigate} showToast={showToast} />;
    } else {
      page = <LabDispatchList navigate={navigate} defaultTab={searchParams.get('tab') || 'active'} />;
    }
  } else if (seg0 === 'equipment') {
    page = <LabEquipment navigate={navigate} canManage={false} showToast={showToast} />;
  } else {
    page = <LabDashboard navigate={navigate} />;
  }

  return (
    <>
      {page}
      {toast && (
        <div style={{
          position: 'fixed', bottom: 28, left: '50%', transform: 'translateX(-50%)',
          padding: '12px 20px', borderRadius: 10, background: ink, color: '#fff',
          fontSize: 14, fontWeight: 500, boxShadow: '0 12px 36px rgba(20,20,28,0.32)',
          animation: 'slide-in 0.18s ease-out', zIndex: 300,
        }}>{toast.msg}</div>
      )}
    </>
  );
}
