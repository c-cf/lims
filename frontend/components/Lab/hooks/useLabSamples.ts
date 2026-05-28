'use client';
import React from 'react';
import api from '@/lib/api';

type Sample = Awaited<ReturnType<typeof api.samples.list>>[number];
type Request = Awaited<ReturnType<typeof api.requests.list>>[number];

const useLabSamples = () => {
  const [samples, setSamples] = React.useState<Sample[]>([]);
  const [requestsById, setRequestsById] = React.useState<Map<number, Request>>(new Map());
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);
  const refresh = React.useCallback(() => {
    if (!api || !api.samples) {
      setLoading(false);
      return;
    }
    setLoading(true);
    Promise.all([api.samples.list(), api.requests.list().catch((): Request[] => [])])
      .then(([ss, rs]) => {
        const visible = ss.filter((s: Sample) => s.raw_status !== 'created');
        setSamples(visible);
        setRequestsById(new Map(rs.map((r: Request) => [r.id, r])));
        setError(null);
      })
      .catch((err) => setError(err.message || String(err)))
      .finally(() => setLoading(false));
  }, []);
  React.useEffect(() => {
    refresh();
  }, [refresh]);
  const wafers = samples.map((s) => ({
    ...s,
    urgency: requestsById.get(s.requestId)?.urgency || '1w',
  }));
  return { wafers, loading, error, refresh };
};
export default useLabSamples;
export { useLabSamples };
