'use client';

type TabRow = { status: string };
const TABS = [
  { id: 'all', label: 'All', filter: (r: TabRow) => r.status !== 'draft' },
  { id: 'pending', label: 'Pending Approval', filter: (r: TabRow) => r.status === 'submitted' },
  { id: 'in_progress', label: 'In Progress', filter: (r: TabRow) => r.status === 'in_progress' },
  { id: 'returned', label: 'Returned', filter: (r: TabRow) => r.status === 'returned' },
  { id: 'rejected', label: 'Rejected', filter: (r: TabRow) => r.status === 'rejected' },
  { id: 'cancelled', label: 'Cancelled', filter: (r: TabRow) => r.status === 'cancelled' },
];
export default TABS;
export { TABS };
