'use client';
import React from 'react';
import api from '@/lib/api';

type WipDetail = Awaited<ReturnType<typeof api.wips.get>>;
type SampleBrief = WipDetail['samples'][number];

const useWaferDetail = (id: number | string | null | undefined) => {
  const [data, setData] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);
  const refresh = React.useCallback(() => {
    if (id == null || !api) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    let cancelled = false;
    (async () => {
      try {
        const sample = await api.samples.get(id);
        if (cancelled) return;
        const [request, experiments] = await Promise.all([
          api.requests
            .get(sample.requestId)
            .catch((): Awaited<ReturnType<typeof api.requests.get>> | null => null),
          api.samples
            .getExperiments(sample.id)
            .catch((): Awaited<ReturnType<typeof api.samples.getExperiments>> => []),
        ]);
        let wip: WipDetail | null = null;
        if (sample.hasWip) {
          const wipList = await api.wips
            .list({ status: 'in_progress' })
            .catch((): Awaited<ReturnType<typeof api.wips.list>> => []);
          for (const row of wipList) {
            if (cancelled) return;
            const detail = await api.wips.get(row.id).catch((): WipDetail | null => null);
            if (detail?.samples?.some((s: SampleBrief) => s.id === sample.id)) {
              wip = detail;
              break;
            }
          }
        }
        if (cancelled) return;
        setData({ sample, request, wip, experiments });
      } catch (e) {
        if (!cancelled) setError(e.message || String(e));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [id]);
  React.useEffect(() => {
    const cleanup = refresh();
    return cleanup;
  }, [refresh]);
  return { data, loading, error, refresh };
};
export default useWaferDetail;
export { useWaferDetail };
