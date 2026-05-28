'use client';
import React from 'react';
import api from '@/lib/api';

type SampleWithId = { id: number | string };

const useSampleExperimentsForRequest = (samples: SampleWithId[] | null | undefined) => {
  const [byId, setById] = React.useState<Record<string, unknown>>({});
  const [loading, setLoading] = React.useState(false);
  const ids = (samples || []).map((s) => s.id).filter((v): v is number | string => v != null);
  const key = ids.join(',');
  React.useEffect(() => {
    if (!api || !api.samples || ids.length === 0) {
      setById({});
      return;
    }
    let cancelled = false;
    setLoading(true);
    Promise.all(
      ids.map((sid) =>
        api.samples
          .getExperiments(sid)
          .then((rows): [number | string, unknown[]] => [sid, rows])
          .catch((): [number | string, unknown[]] => [sid, []]),
      ),
    )
      .then((pairs) => {
        if (cancelled) return;
        const next: Record<string, unknown> = {};
        pairs.forEach(([sid, rows]) => {
          next[String(sid)] = rows;
        });
        setById(next);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- keyed by ids.join(","); listing ids array would create a new ref each render and cause infinite loops
  }, [key]);
  return { byId, loading };
};
export default useSampleExperimentsForRequest;
export { useSampleExperimentsForRequest };
