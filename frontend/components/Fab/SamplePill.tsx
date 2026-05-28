'use client';
import SAMPLE_STATUS_LABEL from '@/components/Fab/constants/sampleStatusLabel';
import Pill from '@/components/Manager/Pill';

type PillStyle = { label: string; bg: string; fg: string };
const SAMPLE_STATUS_MAP: Record<string, PillStyle> = SAMPLE_STATUS_LABEL;
const SamplePill = ({ status, size = 'sm' }: { status: string; size?: string }) => {
  const m = SAMPLE_STATUS_MAP[status] || { label: status, bg: '#ebebf0', fg: '#5a5a6e' };
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return <Pill {...(m as any)} size={size} />;
};
export default SamplePill;
export { SamplePill };
