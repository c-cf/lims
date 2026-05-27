"use client";
import React, { use, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { makeMgrNavigate, makeLabNavigate } from '@/lib/navigate';
import { ink } from '@/lib/colors';
import MgrDashboard from '@/components/Manager/MgrDashboard';
import MgrAllRequests from '@/components/Manager/MgrAllRequests';
import MgrRequestDetail from '@/components/Manager/MgrRequestDetail';
import MgrRecipes from '@/components/Manager/MgrRecipes';
import MgrReports from '@/components/Manager/MgrReports';
import LabDashboard from '@/components/Lab/LabDashboard';
import LabSamples from '@/components/Lab/LabSamples';
import LabWaferDetail from '@/components/Lab/LabWaferDetail';
import LabWipList from '@/components/Lab/LabWipList';
import LabWipDetail from '@/components/Lab/LabWipDetail';
import LabDispatchList from '@/components/Lab/LabDispatchList';
import LabDispatchDetail from '@/components/Lab/LabDispatchDetail';
import LabEquipment from '@/components/Lab/LabEquipment';

export default function ManagerPage({ params }: { params: Promise<{ path?: string[] }> }) {
  const { path = [] } = use(params);
  const searchParams = useSearchParams();
  const router = useRouter();
  const navigate = makeMgrNavigate(router.push.bind(router));
  // Lab navigate within manager context uses /manager/lab/* base
  const labNavigate = makeLabNavigate(router.push.bind(router), '/manager/lab');
  const [toast, setToast] = useState(null);

  const showToast = (msg: string) => {
    setToast({ msg, t: Date.now() });
    setTimeout(() => setToast(null), 2200);
  };

  const [seg0, seg1, seg2] = path;

  let page: React.ReactNode;

  // /manager/lab/... — lab operations for manager (with canManage=true)
  if (seg0 === 'lab') {
    if (!seg1 || seg1 === 'dashboard') {
      page = <LabDashboard navigate={labNavigate} />;
    } else if (seg1 === 'samples') {
      if (seg2) {
        page = <LabWaferDetail id={Number(seg2)} navigate={labNavigate} showToast={showToast} />;
      } else {
        page = <LabSamples navigate={labNavigate} defaultTab={searchParams.get('tab') || 'all'} showToast={showToast} />;
      }
    } else if (seg1 === 'wips') {
      if (seg2) {
        page = <LabWipDetail id={Number(seg2)} navigate={labNavigate} showToast={showToast} />;
      } else {
        page = <LabWipList navigate={labNavigate} showToast={showToast} />;
      }
    } else if (seg1 === 'dispatches') {
      if (seg2) {
        page = <LabDispatchDetail id={Number(seg2)} navigate={labNavigate} showToast={showToast} />;
      } else {
        page = <LabDispatchList navigate={labNavigate} defaultTab={searchParams.get('tab') || 'active'} />;
      }
    } else if (seg1 === 'equipment') {
      page = <LabEquipment navigate={labNavigate} canManage={true} showToast={showToast} />;
    } else {
      page = <LabDashboard navigate={labNavigate} />;
    }
  } else if (!seg0 || seg0 === 'dashboard') {
    page = <MgrDashboard navigate={navigate} />;
  } else if (seg0 === 'requests') {
    if (seg1) {
      page = <MgrRequestDetail id={Number(seg1)} navigate={navigate} showToast={showToast} />;
    } else {
      page = <MgrAllRequests navigate={navigate} />;
    }
  } else if (seg0 === 'recipes') {
    page = <MgrRecipes showToast={showToast} />;
  } else if (seg0 === 'reports') {
    page = <MgrReports />;
  } else {
    page = <MgrDashboard navigate={navigate} />;
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
