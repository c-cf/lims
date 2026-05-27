type RouteObj = { page: string; id?: number | string; tab?: string };
type Push = (url: string) => void;

export function makeFabNavigate(push: Push) {
  return (r: RouteObj) => {
    switch (r.page) {
      case 'fab_dashboard': return push('/fab/dashboard');
      case 'fab_requests':  return push(`/fab/requests${r.tab ? `?tab=${r.tab}` : ''}`);
      case 'fab_drafts':    return push('/fab/drafts');
      case 'fab_new':       return push('/fab/requests/new');
      case 'fab_draft_edit':return push(`/fab/drafts/${r.id}`);
      case 'fab_request':   return push(`/fab/requests/${r.id}`);
      default:              return push('/fab/dashboard');
    }
  };
}

export function makeLabNavigate(push: Push, base = '/lab') {
  return (r: RouteObj) => {
    switch (r.page) {
      case 'lab_dashboard':       return push(`${base}/dashboard`);
      case 'lab_samples':         return push(`${base}/samples${r.tab ? `?tab=${r.tab}` : ''}`);
      case 'lab_wafer':           return push(`${base}/samples/${r.id}`);
      case 'lab_wip':             return push(`${base}/wips`);
      case 'lab_wip_detail':      return push(`${base}/wips/${r.id}`);
      case 'lab_dispatches':      return push(`${base}/dispatches${r.tab ? `?tab=${r.tab}` : ''}`);
      case 'lab_dispatch_detail': return push(`${base}/dispatches/${r.id}`);
      case 'lab_equipment':       return push(`${base}/equipment`);
      default:                    return push(`${base}/dashboard`);
    }
  };
}

export function makeMgrNavigate(push: Push) {
  return (r: RouteObj) => {
    // Manager lab pages use /manager/lab/* base
    if (r.page.startsWith('lab_')) return makeLabNavigate(push, '/manager/lab')(r);
    switch (r.page) {
      case 'mgr_dashboard':     return push('/manager/dashboard');
      case 'mgr_all_requests':  return push('/manager/requests');
      case 'mgr_request':       return push(`/manager/requests/${r.id}`);
      case 'mgr_recipes':       return push('/manager/recipes');
      case 'mgr_reports':       return push('/manager/reports');
      default:                  return push('/manager/dashboard');
    }
  };
}

export function roleHome(role: string): string {
  if (role === 'fab_user') return '/fab/dashboard';
  if (role === 'lab_manager') return '/manager/dashboard';
  if (role === 'lab_member' || role === 'lab_mem') return '/lab/dashboard';
  return '/login';
}
