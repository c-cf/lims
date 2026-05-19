// LIMS API client — single source of truth for HTTP calls to the Django backend.
//
// Mounted on window.api. Every UI module that needs server data should go
// through this object so that auth, error handling, and status-enum mapping
// live in exactly one place.
//
// The base URL is configurable via window.LIMS_API_BASE before the scripts
// load; falls back to the production host.

(function () {
  const DEFAULT_BASE = 'https://lims.cchuml.com/api';
  const BASE = (window.LIMS_API_BASE || DEFAULT_BASE).replace(/\/+$/, '');

  // ---------------------------------------------------------------------------
  // Token storage. localStorage works in normal hosting; for the standalone
  // single-file artifact we silently downgrade to an in-memory store.
  // ---------------------------------------------------------------------------
  const memStore = {};
  let useLocalStorage = true;
  try {
    const probe = '__lims_probe__';
    window.localStorage.setItem(probe, '1');
    window.localStorage.removeItem(probe);
  } catch (_e) {
    useLocalStorage = false;
  }
  const store = {
    get(k) {
      if (useLocalStorage) return window.localStorage.getItem(k);
      return memStore[k] || null;
    },
    set(k, v) {
      if (useLocalStorage) {
        if (v == null) window.localStorage.removeItem(k);
        else window.localStorage.setItem(k, v);
      } else {
        if (v == null) delete memStore[k];
        else memStore[k] = v;
      }
    },
    clear() {
      ['lims.access', 'lims.refresh', 'lims.user'].forEach(k => this.set(k, null));
    },
  };

  // ---------------------------------------------------------------------------
  // Status / role / shape adapters. Backend uses richer enums than the UI
  // renders — normalize at the wire boundary so component code stays clean.
  // ---------------------------------------------------------------------------

  // backend role -> frontend role (mostly for routing in shell.jsx)
  const ROLE_MAP = {
    fab_user: 'fab_user',
    lab_staff: 'lab_member',       // <-- key rename
    lab_manager: 'lab_manager',
  };
  const normalizeRole = (r) => ROLE_MAP[r] || r;

  // backend Request.status -> frontend status used by status pills.
  // 'approved' and 'sample_shipped' collapse into in_progress because the
  // current pill palette doesn't distinguish them.
  const REQUEST_STATUS_MAP = {
    draft: 'draft',
    pending_approval: 'submitted',
    approved: 'in_progress',
    sample_shipped: 'in_progress',
    in_progress: 'in_progress',
    exception: 'in_progress',
    completed: 'completed',
    closed: 'completed',
    returned: 'returned',
    rejected: 'rejected',
    cancelled: 'cancelled',
  };

  const SAMPLE_STATUS_MAP = {
    created: 'incoming',
    shipped: 'incoming',
    received: 'received',
    receiving_exception: 'rejected',
    split: 'received',
    processing_exception: 'in_wip',
    completed: 'completed',
    lost: 'rejected',
    returned: 'returned',
    voided: 'cancelled',
  };

  const DISPATCH_STATUS_MAP = {
    pending: 'pending',
    dispatched: 'dispatched',
    running: 'running',
    unloaded: 'unloaded',
    result_recorded: 'result_recorded',
    completed: 'result_recorded',
    execution_exception: 'exception',
    pending_redispatch: 'exception',
    aborted: 'aborted',
  };

  const EQUIPMENT_STATUS_MAP = {
    available: 'idle',
    maintenance: 'maintenance',
    disabled: 'maintenance',
  };

  // Display helpers — match the project's existing WIP-XXXX / DP-XXXX convention.
  const wipCode = (id) => `WIP-${String(id).padStart(4, '0')}`;
  const dispatchCode = (id) => `DP-${String(id).padStart(4, '0')}`;

  // ---------------------------------------------------------------------------
  // Request normalizers. Each turns a backend payload into the shape the
  // existing JSX expects. Keep these dumb (no business logic).
  // ---------------------------------------------------------------------------
  function normalizeRequestRow(r) {
    return {
      id: r.id,
      title: r.title,
      status: REQUEST_STATUS_MAP[r.status] || r.status,
      raw_status: r.status,                                  // keep for state-machine calls
      urgency: r.urgency || null,                            // backend gap: §2.2
      requester: r.requester,
      note: r.note,
      created: r.created_at,
      submitted: r.submitted_at,
      updated: r.updated_at,
      // these are filled in by the detail endpoint
      expIds: [],
      samples: [],
      history: [],
    };
  }

  function normalizeRequestDetail(r) {
    return {
      ...normalizeRequestRow(r),
      expIds: (r.experiment_types || []).map(et => et.id),
      experiment_types: r.experiment_types || [],
      samples: (r.samples || []).map(s => ({
        id: s.id,
        wafer: s.wafer_id,
        size: s.wafer_size,
        status: SAMPLE_STATUS_MAP[s.status] || s.status,
        raw_status: s.status,
      })),
      history: (r.approval_logs || []).map(log => ({
        action: log.action.toUpperCase(),
        by: log.reviewer?.username,
        at: log.created_at,
        note: log.comment || '',
      })),
      completed_at: r.completed_at,
      closed_at: r.closed_at,
    };
  }

  function normalizeSampleRow(s) {
    return {
      id: s.id,
      wafer: s.wafer_id,
      size: s.wafer_size,
      requestId: s.request_id,
      status: SAMPLE_STATUS_MAP[s.status] || s.status,
      raw_status: s.status,
      arrivedAt: s.received_at || s.updated_at || null,  // backend gap: §2.5
      created: s.created_at,
    };
  }

  function normalizeWip(w) {
    return {
      id: w.id,
      code: wipCode(w.id),
      sampleId: w.sample_id,
      status: w.status,
      note: w.note,
      created: w.created_at,
      completed: w.completed_at,
      dispatches: (w.dispatches || []).map(normalizeDispatch),
    };
  }

  function normalizeDispatch(d) {
    return {
      id: d.id,
      code: dispatchCode(d.id),
      wipId: d.wip_id,
      experimentId: d.experiment_type_id,
      experimentName: d.experiment_type_name,
      equipmentId: d.equipment_id,
      equipmentName: d.equipment_name,
      recipeId: d.recipe_id,
      recipeName: d.recipe_name,
      operator: d.created_by?.username || null,  // backend gap: §2.6 (created_by not yet exposed)
      status: DISPATCH_STATUS_MAP[d.status] || d.status,
      raw_status: d.status,
      dispatchedAt: d.dispatched_at,
      completedAt: d.completed_at,
      created: d.created_at,
      result: d.result ? {
        summary: d.result.summary,
        verdict: d.result.verdict,
        data: d.result.data,
        source: d.result.data_source,
      } : null,
    };
  }

  function normalizeEquipment(e) {
    return {
      id: e.id,
      name: e.name,
      model: e.model_name,
      capacity: e.capacity,
      status: EQUIPMENT_STATUS_MAP[e.status] || e.status,
      raw_status: e.status,
      capabilities: e.capabilities || [],
    };
  }

  function normalizeRecipe(r) {
    return {
      id: r.id,
      name: r.name,
      description: r.description,
      // Recipe.equipment is currently required on the backend (see §2.3). For
      // now we surface it; the UI ignores it once §2.3 lands.
      equipmentId: r.equipment?.id || null,
      equipmentName: r.equipment?.name || null,
      experimentId: r.experiment_type?.id || null,
      experimentName: r.experiment_type?.name || null,
      params: r.parameters || {},
      active: r.is_active,
    };
  }

  // ---------------------------------------------------------------------------
  // Core fetch with auth + 401 refresh-once retry.
  // ---------------------------------------------------------------------------
  let refreshInflight = null;

  async function rawFetch(path, opts) {
    const url = path.startsWith('http') ? path : `${BASE}${path}`;
    const access = store.get('lims.access');
    const headers = Object.assign(
      { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      access ? { 'Authorization': `Bearer ${access}` } : {},
      (opts && opts.headers) || {}
    );
    const init = Object.assign({}, opts || {}, { headers });
    if (init.body && typeof init.body !== 'string') {
      init.body = JSON.stringify(init.body);
    }
    return fetch(url, init);
  }

  async function call(path, opts) {
    let res = await rawFetch(path, opts);
    if (res.status === 401 && store.get('lims.refresh') && path !== '/auth/refresh') {
      // Single concurrent refresh; subsequent callers await the same promise.
      if (!refreshInflight) refreshInflight = doRefresh();
      const refreshed = await refreshInflight;
      refreshInflight = null;
      if (refreshed) {
        res = await rawFetch(path, opts);
      }
    }
    if (!res.ok) {
      let detail = `${res.status} ${res.statusText}`;
      try {
        const body = await res.json();
        if (body && body.detail) detail = body.detail;
      } catch (_e) { /* non-json error */ }
      const err = new Error(detail);
      err.status = res.status;
      throw err;
    }
    if (res.status === 204) return null;
    const ct = res.headers.get('Content-Type') || '';
    if (ct.includes('application/json')) return res.json();
    return res.text();
  }

  async function doRefresh() {
    const refresh = store.get('lims.refresh');
    if (!refresh) return false;
    try {
      const out = await rawFetch('/auth/refresh', {
        method: 'POST',
        body: JSON.stringify({ refresh_token: refresh }),
      }).then(r => r.ok ? r.json() : Promise.reject());
      store.set('lims.access', out.access_token);
      store.set('lims.refresh', out.refresh_token);
      return true;
    } catch (_e) {
      store.clear();
      return false;
    }
  }

  // ---------------------------------------------------------------------------
  // Public API
  // ---------------------------------------------------------------------------
  const api = {
    base: BASE,

    auth: {
      async login(username, password) {
        const out = await call('/auth/login', {
          method: 'POST',
          body: JSON.stringify({ username, password }),
        });
        store.set('lims.access', out.access_token);
        store.set('lims.refresh', out.refresh_token);
        const user = {
          id: out.id,
          username: out.username,
          role: normalizeRole(out.role),
          raw_role: out.role,
          department: out.department,
        };
        store.set('lims.user', JSON.stringify(user));
        return user;
      },
      async logout() {
        const refresh = store.get('lims.refresh');
        try {
          if (refresh) await call('/auth/logout', { method: 'POST', body: { refresh_token: refresh } });
        } catch (_e) { /* don't care */ }
        store.clear();
      },
      async me() {
        const out = await call('/auth/me');
        return {
          id: out.id,
          username: out.username,
          role: normalizeRole(out.role),
          raw_role: out.role,
          department: out.department,
        };
      },
      cachedUser() {
        try {
          const raw = store.get('lims.user');
          return raw ? JSON.parse(raw) : null;
        } catch (_e) {
          return null;
        }
      },
    },

    experimentTypes: {
      async list(q = {}) {
        const usp = new URLSearchParams(q);
        const out = await call(`/experiment-types/?${usp}`);
        return out.map(e => ({ id: e.id, name: e.name, description: e.description, labCategory: e.lab_category }));
      },
    },

    equipment: {
      async list(q = {}) {
        const usp = new URLSearchParams(q);
        const out = await call(`/equipment/?${usp}`);
        return out.map(normalizeEquipment);
      },
      async create(payload) {
        // payload = { name, model_name, capacity, experiment_type_ids? }
        const out = await call('/equipment/', { method: 'POST', body: payload });
        return normalizeEquipment(out);
      },
      async update(id, payload) {
        const out = await call(`/equipment/${id}`, { method: 'PATCH', body: payload });
        return normalizeEquipment(out);
      },
      async setCapabilities(id, experimentTypeIds) {
        const out = await call(`/equipment/${id}/capabilities`, {
          method: 'POST', body: { experiment_type_ids: experimentTypeIds },
        });
        return normalizeEquipment(out);
      },
    },

    recipes: {
      async list(q = {}) {
        const usp = new URLSearchParams(q);
        const out = await call(`/recipes/?${usp}`);
        return out.map(normalizeRecipe);
      },
      async create(payload) {
        // payload = { name, description?, equipment_id, experiment_type_id, parameters }
        // §2.3: equipment_id will be optional once backend lands the change.
        const out = await call('/recipes/', { method: 'POST', body: payload });
        return normalizeRecipe(out);
      },
      async update(id, payload) {
        const out = await call(`/recipes/${id}`, { method: 'PATCH', body: payload });
        return normalizeRecipe(out);
      },
      async remove(id) {
        const out = await call(`/recipes/${id}`, { method: 'DELETE' });
        return normalizeRecipe(out);
      },
    },

    requests: {
      async list(q = {}) {
        const usp = new URLSearchParams(q);
        const out = await call(`/requests/?${usp}`);
        return out.map(normalizeRequestRow);
      },
      async get(id) {
        const out = await call(`/requests/${id}`);
        return normalizeRequestDetail(out);
      },
      async create(payload) {
        // payload = { title, note?, experiment_type_ids, experiment_parameters?, samples }
        // urgency goes here once §2.2 lands.
        const out = await call('/requests/', { method: 'POST', body: payload });
        return normalizeRequestDetail(out);
      },
      async update(id, payload) {
        const out = await call(`/requests/${id}`, { method: 'PATCH', body: payload });
        return normalizeRequestDetail(out);
      },
      async submit(id) {
        return normalizeRequestDetail(await call(`/requests/${id}/submit`, { method: 'POST' }));
      },
      async approve(id) {
        return normalizeRequestDetail(await call(`/requests/${id}/approve`, { method: 'POST' }));
      },
      async returnRequest(id, comment) {
        return normalizeRequestDetail(await call(`/requests/${id}/return`, {
          method: 'POST', body: { comment },
        }));
      },
      async reject(id, comment) {
        return normalizeRequestDetail(await call(`/requests/${id}/reject`, {
          method: 'POST', body: { comment },
        }));
      },
      async ship(id) {
        return normalizeRequestDetail(await call(`/requests/${id}/ship`, { method: 'POST' }));
      },
      async cancel(id, reason) {
        return normalizeRequestDetail(await call(`/requests/${id}/cancel`, {
          method: 'POST', body: { reason },
        }));
      },
      async close(id) {
        return normalizeRequestDetail(await call(`/requests/${id}/close`, { method: 'POST' }));
      },
    },

    samples: {
      async list(q = {}) {
        const usp = new URLSearchParams(q);
        const out = await call(`/samples/?${usp}`);
        return out.map(normalizeSampleRow);
      },
      async get(id) {
        return normalizeSampleRow(await call(`/samples/${id}`));
      },
      async receive(id) {
        return normalizeSampleRow(await call(`/samples/${id}/receive`, { method: 'POST' }));
      },
      async rejectReceiving(id, reason = '') {
        return normalizeSampleRow(await call(`/samples/${id}/reject-receiving`, {
          method: 'POST', body: { reason },
        }));
      },
      async reportLost(id) {
        return normalizeSampleRow(await call(`/samples/${id}/report-lost`, { method: 'POST' }));
      },
      async void(id) {
        return normalizeSampleRow(await call(`/samples/${id}/void`, { method: 'POST' }));
      },
      async return(id) {
        return normalizeSampleRow(await call(`/samples/${id}/return`, { method: 'POST' }));
      },
    },

    wips: {
      async list(q = {}) {
        const usp = new URLSearchParams(q);
        const out = await call(`/wips/?${usp}`);
        return out.map(w => ({
          id: w.id,
          code: wipCode(w.id),
          sampleId: w.sample_id,
          status: w.status,
          note: w.note,
          completed: w.completed_at,
          created: w.created_at,
        }));
      },
      async get(id) {
        return normalizeWip(await call(`/wips/${id}/`));
      },
      async create(sampleId, note = '') {
        return normalizeWip(await call('/wips/', {
          method: 'POST', body: { sample_id: sampleId, note },
        }));
      },
      async createDispatch(wipId, payload) {
        // payload = { experiment_type_id, equipment_id, recipe_id, note? }
        return normalizeWip(await call(`/wips/${wipId}/dispatches/`, {
          method: 'POST', body: payload,
        }));
      },
      async complete(id) {
        return normalizeWip(await call(`/wips/${id}/complete/`, { method: 'POST' }));
      },
      async abort(id) {
        return normalizeWip(await call(`/wips/${id}/abort/`, { method: 'POST' }));
      },
    },

    dispatches: {
      async list(q = {}) {
        const usp = new URLSearchParams(q);
        const out = await call(`/dispatches/?${usp}`);
        return out.map(d => ({
          id: d.id,
          code: dispatchCode(d.id),
          wipId: d.wip_id,
          experimentId: d.experiment_type_id,
          equipmentId: d.equipment_id,
          recipeId: d.recipe_id,
          status: DISPATCH_STATUS_MAP[d.status] || d.status,
          raw_status: d.status,
          dispatchedAt: d.dispatched_at,
          completedAt: d.completed_at,
          created: d.created_at,
        }));
      },
      async get(id) {
        return normalizeDispatch(await call(`/dispatches/${id}/`));
      },
      async start(id) {
        return normalizeDispatch(await call(`/dispatches/${id}/start/`, { method: 'POST' }));
      },
      async unload(id) {
        return normalizeDispatch(await call(`/dispatches/${id}/unload/`, { method: 'POST' }));
      },
      async recordResult(id, payload) {
        // payload = { summary, verdict: 'pass'|'fail', data?, note? }
        return normalizeDispatch(await call(`/dispatches/${id}/record-result/`, {
          method: 'POST', body: payload,
        }));
      },
      async complete(id) {
        return normalizeDispatch(await call(`/dispatches/${id}/complete/`, { method: 'POST' }));
      },
      async reportException(id, note = '') {
        return normalizeDispatch(await call(`/dispatches/${id}/report-exception/`, {
          method: 'POST', body: { note },
        }));
      },
      async redispatch(id) {
        return normalizeDispatch(await call(`/dispatches/${id}/redispatch/`, { method: 'POST' }));
      },
      async abort(id) {
        return normalizeDispatch(await call(`/dispatches/${id}/abort/`, { method: 'POST' }));
      },
    },

    reports: {
      async equipmentUtilization(q) {
        // q = { period, start_date, end_date, equipment_id? }
        const usp = new URLSearchParams(q);
        return call(`/reports/equipment-utilization?${usp}`);
      },
      async requestStatistics(q) {
        const usp = new URLSearchParams(q);
        return call(`/reports/request-statistics?${usp}`);
      },
    },
  };

  window.api = api;
  window.LIMS_STATUS_MAPS = {
    request: REQUEST_STATUS_MAP,
    sample: SAMPLE_STATUS_MAP,
    dispatch: DISPATCH_STATUS_MAP,
    equipment: EQUIPMENT_STATUS_MAP,
    role: ROLE_MAP,
  };
})();
