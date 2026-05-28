'use client';
import React from 'react';
import api from '@/lib/api';

const useLabDashboardData = () => {
  const [samples, setSamples] = React.useState([]);
  const [wips, setWips] = React.useState([]);
  const [dispatches, setDispatches] = React.useState([]);
  const [equipment, setEquipment] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);
  const refresh = React.useCallback(() => {
    if (!api) {
      setLoading(false);
      return;
    }
    setLoading(true);
    Promise.all([
      api.samples.list(),
      api.wips.list(),
      api.dispatches.list(),
      api.equipment.list().catch((): Awaited<ReturnType<typeof api.equipment.list>> => []),
      api.experimentTypes
        .list()
        .catch((): Awaited<ReturnType<typeof api.experimentTypes.list>> => []),
    ])
      .then(([ss, ws, ds, eqs, exps]) => {
        setSamples(ss.filter((s: { raw_status: string }) => s.raw_status !== 'created'));
        setWips(ws);
        setEquipment(eqs);
        type NamedRow = { id: number; name?: string };
        const expById = new Map((exps as NamedRow[]).map((e: NamedRow) => [e.id, e] as const));
        const eqById = new Map((eqs as NamedRow[]).map((e: NamedRow) => [e.id, e] as const));
        setDispatches(
          ds.map((d: { experimentId: number; equipmentId: number }) => ({
            ...d,
            experimentName: expById.get(d.experimentId)?.name || null,
            equipmentName: eqById.get(d.equipmentId)?.name || null,
          })),
        );
        setError(null);
      })
      .catch((err) => setError(err.message || String(err)))
      .finally(() => setLoading(false));
  }, []);
  React.useEffect(() => {
    refresh();
  }, [refresh]);
  return { samples, wips, dispatches, equipment, loading, error, refresh };
};
export default useLabDashboardData;
export { useLabDashboardData };
