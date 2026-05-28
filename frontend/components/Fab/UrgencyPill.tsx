'use client';
import URGENCY_LABEL from '@/components/Manager/constants/urgencyLabel';
import Pill from '@/components/Manager/Pill';

type PillStyle = { label: string; bg: string; fg: string };
const URGENCY_MAP: Record<string, PillStyle> = URGENCY_LABEL;
const UrgencyPill = ({ urgency, size = 'sm' }: { urgency: string; size?: string }) => {
  const m = URGENCY_MAP[urgency] || URGENCY_MAP['1w'];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return <Pill {...(m as any)} size={size} />;
};
export default UrgencyPill;
export { UrgencyPill };
