'use client';
import AddDispatchModalInner from '@/components/Lab/AddDispatchModalInner';
type Wip = { id: number; experimentId: number; experimentName?: string; sampleCount: number };

const AddDispatchModal = ({
  open,
  onClose,
  wip,
  onCreated,
}: {
  open: boolean;
  onClose: () => void;
  wip: Wip;
  onCreated?: () => void;
}) => {
  if (!open || !wip) return null;
  return <AddDispatchModalInner onClose={onClose} wip={wip} onCreated={onCreated} />;
};
export default AddDispatchModal;
export { AddDispatchModal };
