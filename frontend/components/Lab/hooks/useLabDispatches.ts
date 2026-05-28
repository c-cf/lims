'use client';
import React from 'react';
import api from '@/lib/api';

type ExpType = Awaited<ReturnType<typeof api.experimentTypes.list>>[number];
type Equipment = Awaited<ReturnType<typeof api.equipment.list>>[number];

const useLabDispatches = () => {
  const [dispatches, setDispatches] = React.useState<
    Awaited<ReturnType<typeof api.dispatches.list>>
  >([]);
  const [expById, setExpById] = React.useState<Map<number, ExpType>>(new Map());
  const [eqById, setEqById] = React.useState<Map<number, Equipment>>(new Map());
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);
  const refresh = React.useCallback(() => {
    if (!api) {
      setLoading(false);
      return;
    }
    setLoading(true);
    Promise.all([
      api.dispatches.list(),
      api.experimentTypes.list().catch((): ExpType[] => []),
      api.equipment.list().catch((): Equipment[] => []),
    ])
      .then(([ds, exps, eqs]) => {
        setDispatches(ds);
        setExpById(new Map(exps.map((e: ExpType) => [e.id, e])));
        setEqById(new Map(eqs.map((e: Equipment) => [e.id, e])));
        setError(null);
      })
      .catch((err) => setError(err.message || String(err)))
      .finally(() => setLoading(false));
  }, []);
  React.useEffect(() => {
    refresh();
  }, [refresh]);
  type Dispatch = Awaited<ReturnType<typeof api.dispatches.list>>[number];
  const enriched = dispatches.map((d: Dispatch) => ({
    ...d,
    experimentName: expById.get(d.experimentId)?.name || null,
    equipmentName: eqById.get(d.equipmentId)?.name || null,
  }));
  return { dispatches: enriched, loading, error, refresh };
};
export default useLabDispatches;
export { useLabDispatches };
