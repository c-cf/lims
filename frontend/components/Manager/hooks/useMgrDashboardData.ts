'use client';
import React from 'react';
import api from '@/lib/api';

type Request = Awaited<ReturnType<typeof api.requests.list>>[number];

const useMgrDashboardData = () => {
  const [requests, setRequests] = React.useState<Request[]>([]);
  const [equipmentCount, setEquipmentCount] = React.useState(0);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);
  const refresh = React.useCallback(() => {
    if (!api) {
      setLoading(false);
      return;
    }
    setLoading(true);
    Promise.all([
      api.requests.list(),
      api.equipment.list().catch((): Awaited<ReturnType<typeof api.equipment.list>> => []),
    ])
      .then(([rs, eqs]) => {
        setRequests(rs);
        setEquipmentCount(eqs.length);
        setError(null);
      })
      .catch((err) => setError(err.message || String(err)))
      .finally(() => setLoading(false));
  }, []);
  React.useEffect(() => {
    refresh();
  }, [refresh]);
  return { requests, equipmentCount, loading, error, refresh };
};
export default useMgrDashboardData;
export { useMgrDashboardData };
