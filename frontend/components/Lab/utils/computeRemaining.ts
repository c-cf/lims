'use client';
import URGENCY_DAYS from '@/components/Lab/constants/urgencyDays';

const computeRemaining = (w: { arrivedAt?: string | null; status: string; urgency: string }) => {
  if (!w.arrivedAt) return null;
  if (w.status === 'incoming' || w.status === 'rejected') return null;
  const days = URGENCY_DAYS[w.urgency as keyof typeof URGENCY_DAYS] ?? 7;
  const start = new Date(w.arrivedAt.replace(' ', 'T') + ':00').getTime();
  const deadline = start + days * 86400000;
  return deadline - Date.now();
};
export default computeRemaining;
export { computeRemaining };
