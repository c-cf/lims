'use client';

const PriorityMarker = ({ priority }: { priority: string }) => {
  const colorMap: Record<string, string> = {
    high: '#f59e0b',
    urgent: '#ef4444',
    normal: 'transparent',
  };
  const c = colorMap[priority] || 'transparent';
  return (
    <span
      style={{ display: 'inline-block', width: 3, height: 28, borderRadius: 2, background: c }}
    />
  );
};
export default PriorityMarker;
export { PriorityMarker };
