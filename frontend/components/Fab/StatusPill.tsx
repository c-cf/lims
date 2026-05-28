'use client';
import STATUS_LABEL from '@/components/Manager/constants/statusLabel';
import Pill from '@/components/Manager/Pill';

type PillStyle = { label: string; bg: string; fg: string };
const STATUS_MAP: Record<string, PillStyle> = STATUS_LABEL;
const StatusPill = ({ status, size = 'md' }: { status: string; size?: string }) => {
  const m = STATUS_MAP[status] || { label: status, bg: '#ebebf0', fg: '#5a5a6e' };
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return <Pill {...(m as any)} size={size} />;
};
export default StatusPill;
export { StatusPill };
