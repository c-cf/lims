// Shared cross-app types. Keep this file small — only types used by 2+ roots.

import type { ReactNode } from 'react';

export type User = {
  id: number;
  username: string;
  role: string;
  raw_role: string;
  department: string;
};

// All three role apps share a tiny router shape: a "page" key plus optional
// tab + id. The id is polymorphic (request id, sample id, dispatch id…).
export type Route = {
  page: string;
  tab?: string;
  id?: number | string;
};

export type Navigate = (r: Route) => void;

export type ShowToast = (msg: string) => void;

export type OnLogout = () => void;

export type AppShellProps = {
  user: User;
  onLogout: OnLogout;
  tweaksUI: ReactNode;
};
