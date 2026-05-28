'use client';
import WipCreationModalInner from '@/components/Lab/WipCreationModalInner';

const WipCreationModal = ({
  open,
  onClose,
  onSaved,
}: {
  open: boolean;
  onClose: () => void;
  onSaved?: (wip: unknown) => void;
}) => {
  if (!open) return null;
  return <WipCreationModalInner onClose={onClose} onSaved={onSaved} />;
};
export default WipCreationModal;
export { WipCreationModal };
