'use client';

import type api from '@/lib/api';

type Request = Awaited<ReturnType<typeof api.requests.list>>[number];

const ALL_REQ_TABS = [
  { id: 'pending', label: 'Pending Approval', filter: (r: Request) => r.status === 'submitted' },
  { id: 'all', label: 'All', filter: () => true },
  { id: 'in_progress', label: 'In Progress', filter: (r: Request) => r.status === 'in_progress' },
  { id: 'completed', label: 'Completed', filter: (r: Request) => r.status === 'completed' },
  { id: 'returned', label: 'Returned', filter: (r: Request) => r.status === 'returned' },
  { id: 'rejected', label: 'Rejected', filter: (r: Request) => r.status === 'rejected' },
];
export default ALL_REQ_TABS;
export { ALL_REQ_TABS };
