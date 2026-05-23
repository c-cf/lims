# lims-frontend API 與 lims-backend Payload 對照

整理日期：2026-05-22

比對來源：

- 前端：`lims-frontend/src/api.js`
- 後端：`lims-backend` 目前工作區 `wiwi` branch 的 `api.py` / `schemas.py`

## 共通規則

- 前端 API base：`window.LIMS_API_BASE || "/api"`
- Docker / Railway 建議讓前端呼叫同源 `/api`，由 nginx 反向代理到 backend。
- 除 `POST /auth/login`、`POST /auth/refresh` 外，後端 API 預設需要 `Authorization: Bearer <access_token>`。
- 前端 `call()` 會把非字串 body 自動 `JSON.stringify()`，所以表格中的 object 都會送成 JSON。

## 目前主要不一致

| 範圍 | 前端送出 / 期待 | 後端目前預設 schema | 影響 |
|---|---|---|---|
| Equipment create/update | 送 `parameters`，create 可能送 `status` | `EquipmentIn` 不接受 `parameters/status`；`EquipmentUpdate` 不接受 `parameters` | 參數與初始狀態不會被正式保存；若後端嚴格拒絕 extra field 會 422 |
| Recipe create | 只送 `experiment_type_id`，沒有送 `equipment_ids` | `RecipeIn` 必填 `equipment_ids`，且支援 `experiment_type_ids` | 新增 recipe 很可能失敗或無法設定可用機台 / 多實驗種類 |
| Recipe output | 前端 normalizer 主要讀 `experiment_type` | 後端同時回 `experiment_type` 與 `experiment_types` | 多實驗種類 recipe 會被前端壓成單一實驗種類 |
| WIP create | 前端送 `experiment_type_id` + `sample_ids` | `WIPIn` 只接受 `sample_ids` + `note`；後端從 samples 推導實驗種類一致性 | `experiment_type_id` 對目前後端無效 |
| Dispatch create | 前端可送 `estimated_duration_seconds` | `DispatchIn` 只接受 `equipment_id`、`recipe_id`、`note` | 估計時間不會被後端保存 |
| Request create/update | 前端註解與部分 UI 有 `urgency` | `RequestIn/RequestUpdateIn` 沒有 `urgency` | TAT/urgency 若要正式化需後端欄位 |
| Sample output | 前端 normalizer 讀 `has_wip`、`received_at` | `SampleListOut/SampleDetailOut` 沒有這兩個欄位 | 前端只能 fallback；倒數時間可能顯示為未開始 |
| Dispatch output | 前端讀 `created_by`、`estimated_duration_seconds` | `DispatchListOut/DispatchDetailOut` 沒有這些欄位 | operator/估計時間顯示為空 |
| Reports trends | 前端呼叫 `/reports/trends` | 後端目前沒有 `/reports/trends` | Manager dashboard 趨勢圖 API 會失敗 |
| Operation logs | 後端有 `/reports/operation-logs` | `src/api.js` 沒封裝 | Reports 頁若要用 operation logs，應補 frontend API wrapper |

## Auth

### `auth.login(username, password)`

| 項目 | 內容 |
|---|---|
| Frontend endpoint | `POST /auth/login` |
| Frontend payload | `{ "username": string, "password": string }` |
| Backend schema | `LoginIn` |
| Backend payload | `{ "username": string, "password": string }` |
| Response | `TokenOut`: `access_token`, `refresh_token`, `id`, `username`, `role`, `department` |

### `auth.logout()`

| 項目 | 內容 |
|---|---|
| Frontend endpoint | `POST /auth/logout` |
| Frontend payload | `{ "refresh_token": string }` |
| Backend schema | `RefreshIn` |
| Backend payload | `{ "refresh_token": string }` |

### `auth.me()`

| 項目 | 內容 |
|---|---|
| Frontend endpoint | `GET /auth/me` |
| Payload | 無 |
| Response | `UserOut`: `id`, `username`, `role`, `department` |

### Internal refresh

| 項目 | 內容 |
|---|---|
| Frontend endpoint | `POST /auth/refresh` |
| Frontend payload | `{ "refresh_token": string }` |
| Backend schema | `RefreshIn` |
| Backend payload | `{ "refresh_token": string }` |

## Experiment Types

### `experimentTypes.list(q)`

| 項目 | 內容 |
|---|---|
| Frontend endpoint | `GET /experiment-types/?${query}` |
| Frontend query | 任意 object，常用：`search`, `lab_category`, `is_active` |
| Backend query | `search?: string`, `lab_category?: string`, `is_active?: bool` |
| Payload | 無 |

後端還支援但目前 `src/api.js` 未封裝：

- `POST /experiment-types/`
- `GET /experiment-types/{id}`
- `PATCH /experiment-types/{id}`
- `DELETE /experiment-types/{id}`

後端 create payload：

```json
{
  "name": "Temperature Cycling Test",
  "description": "",
  "lab_category": "RA"
}
```

## Equipment

### `equipment.list(q)`

| 項目 | 內容 |
|---|---|
| Frontend endpoint | `GET /equipment/?${query}` |
| Frontend query | 任意 object |
| Backend query | `search?: string`, `status?: "available" | "maintenance" | "disabled"` |
| Payload | 無 |

### `equipment.create({ name, modelName, capacity, status, experimentTypeIds, parameters })`

Frontend payload：

```json
{
  "name": "QA-MULTI-01",
  "model_name": "Multi Tool",
  "capacity": 4,
  "experiment_type_ids": [1, 2],
  "parameters": {},
  "status": "available"
}
```

Backend `EquipmentIn` 預設 payload：

```json
{
  "name": "QA-MULTI-01",
  "model_name": "Multi Tool",
  "capacity": 4,
  "experiment_type_ids": [1, 2]
}
```

差異：`parameters`、`status` 不是目前後端 create schema 的欄位。

### `equipment.update(id, { name, modelName, capacity, status, parameters })`

Frontend payload 只送有值欄位：

```json
{
  "name": "QA-MULTI-01",
  "model_name": "Multi Tool",
  "capacity": 4,
  "status": "maintenance",
  "parameters": {}
}
```

Backend `EquipmentUpdate` 預設 payload：

```json
{
  "name": "QA-MULTI-01",
  "model_name": "Multi Tool",
  "capacity": 4,
  "status": "maintenance"
}
```

差異：`parameters` 不是目前後端 update schema 的欄位。

### `equipment.setCapabilities(id, experimentTypeIds)`

| 項目 | 內容 |
|---|---|
| Frontend endpoint | `POST /equipment/{id}/capabilities` |
| Frontend payload | `{ "experiment_type_ids": number[] }` |
| Backend schema | `CapabilitySetIn` |
| Backend payload | `{ "experiment_type_ids": number[] }` |

## Recipes

### `recipes.list(q)`

| 項目 | 內容 |
|---|---|
| Frontend endpoint | `GET /recipes/?${query}` |
| Frontend query | 任意 object |
| Backend query | `equipment_id?: int`, `experiment_type_id?: int`, `is_active?: bool` |
| Payload | 無 |

Backend response 重點：

```json
{
  "id": 1,
  "name": "QA_MULTI_TCT_CP_VALIDATION_V1",
  "description": "",
  "equipments": [{ "id": 1, "name": "QA-MULTI-01" }],
  "experiment_type": { "id": 1, "name": "Temperature Cycling Test" },
  "experiment_types": [
    { "id": 1, "name": "Temperature Cycling Test" },
    { "id": 2, "name": "Circuit Probing" }
  ],
  "parameters": {},
  "is_active": true
}
```

前端目前 `normalizeRecipe()` 主要使用 `experiment_type`，尚未完整呈現 `experiment_types` 與 `equipments`。

### `recipes.create({ name, description, experimentTypeId, parameters })`

Frontend payload：

```json
{
  "name": "TCT_STD_-40_125_500CYC",
  "description": "",
  "experiment_type_id": 1,
  "parameters": {
    "cycles": 500,
    "profile": "standard"
  }
}
```

Backend `RecipeIn` 預設 payload：

```json
{
  "name": "TCT_STD_-40_125_500CYC",
  "description": "",
  "equipment_ids": [1, 2],
  "experiment_type_id": 1,
  "experiment_type_ids": [1],
  "parameters": {
    "cycles": 500,
    "profile": "standard"
  }
}
```

差異：後端目前要求 `equipment_ids` 至少一筆；多實驗種類應送 `experiment_type_ids`。

### `recipes.update(id, { name, description, parameters })`

Frontend payload 只送有值欄位：

```json
{
  "name": "TCT_STD_-40_125_500CYC",
  "description": "",
  "parameters": {
    "cycles": 500
  }
}
```

Backend `RecipeUpdate` 預設 payload：

```json
{
  "name": "TCT_STD_-40_125_500CYC",
  "description": "",
  "parameters": {},
  "equipment_ids": [1, 2],
  "experiment_type_ids": [1, 2]
}
```

差異：前端目前未送 `equipment_ids`、`experiment_type_ids`，所以 edit recipe 無法完整調整 qualified equipment / 多實驗種類。

### `recipes.remove(id)`

| 項目 | 內容 |
|---|---|
| Frontend endpoint | `DELETE /recipes/{id}` |
| Payload | 無 |
| Backend behavior | soft delete，回傳 `RecipeOut` |

## Requests

### `requests.list(q)`

| 項目 | 內容 |
|---|---|
| Frontend endpoint | `GET /requests/?${query}` |
| Frontend query | 任意 object |
| Backend query | `status?: RequestStatus` |
| Payload | 無 |

### `requests.get(id)`

| 項目 | 內容 |
|---|---|
| Frontend endpoint | `GET /requests/{id}` |
| Payload | 無 |
| Response | `RequestDetailOut` |

### `requests.create(payload)`

Frontend payload 由 New Request 組出，格式：

```json
{
  "title": "051711",
  "note": "",
  "urgency": "1w",
  "experiment_type_ids": [1, 2],
  "experiment_parameters": {
    "1": {},
    "2": {}
  },
  "samples": [
    { "wafer_id": "W001", "wafer_size": "200mm" }
  ]
}
```

Backend `RequestIn` 預設 payload：

```json
{
  "title": "051711",
  "note": "",
  "experiment_type_ids": [1, 2],
  "experiment_parameters": {
    "1": {},
    "2": {}
  },
  "samples": [
    { "wafer_id": "W001", "wafer_size": "200mm" }
  ]
}
```

差異：`urgency` 不是目前後端 schema 欄位。

### `requests.update(id, payload)`

Frontend payload 可送：

```json
{
  "title": "051711",
  "note": "",
  "experiment_type_ids": [1, 2],
  "experiment_parameters": {
    "1": {},
    "2": {}
  },
  "samples": [
    { "wafer_id": "W001", "wafer_size": "200mm" }
  ]
}
```

Backend `RequestUpdateIn` 預設 payload：

```json
{
  "title": "051711",
  "note": "",
  "experiment_type_ids": [1, 2],
  "experiment_parameters": {
    "1": {}
  },
  "samples": [
    { "wafer_id": "W001", "wafer_size": "200mm" }
  ]
}
```

注意：後端只允許更新 `draft` 或 `returned` 狀態。

### Request actions

| Frontend method | Endpoint | Frontend payload | Backend schema |
|---|---|---|---|
| `requests.submit(id)` | `POST /requests/{id}/submit` | 無 | 無 |
| `requests.approve(id)` | `POST /requests/{id}/approve` | 無 | 無 |
| `requests.returnRequest(id, comment)` | `POST /requests/{id}/return` | `{ "comment": string }` | `CommentIn` |
| `requests.reject(id, comment)` | `POST /requests/{id}/reject` | `{ "comment": string }` | `CommentIn` |
| `requests.ship(id)` | `POST /requests/{id}/ship` | 無 | 無 |
| `requests.cancel(id, reason)` | `POST /requests/{id}/cancel` | `{ "reason": string }` | `ReasonIn` |
| `requests.close(id)` | `POST /requests/{id}/close` | 無 | 無 |

## Samples

### `samples.list(q)`

| 項目 | 內容 |
|---|---|
| Frontend endpoint | `GET /samples/?${query}` |
| Frontend query | 任意 object |
| Backend query | `request_id?: int`, `status?: SampleStatus` |
| Payload | 無 |

Backend `SampleListOut` 目前：

```json
{
  "id": 1,
  "wafer_id": "W001",
  "wafer_size": "200mm",
  "status": "received",
  "request_id": 1,
  "created_at": "2026-05-22T00:00:00Z",
  "updated_at": "2026-05-22T00:00:00Z"
}
```

前端 normalizer 另外會讀：

```json
{
  "has_wip": true,
  "received_at": "2026-05-22T00:00:00Z"
}
```

但這兩個欄位不在目前後端 `SampleListOut` / `SampleDetailOut` schema。

### `samples.get(id)`

| 項目 | 內容 |
|---|---|
| Frontend endpoint | `GET /samples/{id}` |
| Payload | 無 |
| Backend response | `SampleDetailOut` |

### Sample actions

| Frontend method | Endpoint | Frontend payload | Backend schema |
|---|---|---|---|
| `samples.receive(id)` | `POST /samples/{id}/receive` | 無 | 無 |
| `samples.rejectReceiving(id, reason)` | `POST /samples/{id}/reject-receiving` | `{ "reason": string }` | `ReasonOptionalIn` |
| `samples.reportLost(id)` | `POST /samples/{id}/report-lost` | 無 | 後端 endpoint 目前無 payload |
| `samples.void(id)` | `POST /samples/{id}/void` | 無 | 後端 endpoint 目前無 payload |
| `samples.return(id)` | `POST /samples/{id}/return` | 無 | 後端 endpoint 目前無 payload |

後端有但前端未封裝：

| Endpoint | Payload |
|---|---|
| `GET /samples/{id}/experiment-status` | 無 |

## WIP

### `wips.list(q)`

| 項目 | 內容 |
|---|---|
| Frontend endpoint | `GET /wips/?${query}` |
| Frontend query | 任意 object |
| Backend query | `status?: WIPStatus`, 依 `apps/wip/api.py` 實作 |
| Payload | 無 |

### `wips.get(id)`

| 項目 | 內容 |
|---|---|
| Frontend endpoint | `GET /wips/{id}/` |
| Payload | 無 |
| Backend response | `WIPDetailOut` |

### `wips.create({ experimentTypeId, sampleIds, note })`

Frontend payload：

```json
{
  "experiment_type_id": 1,
  "sample_ids": [1, 2],
  "note": ""
}
```

Backend `WIPIn` 預設 payload：

```json
{
  "sample_ids": [1, 2],
  "note": ""
}
```

差異：後端目前不需要也不使用 `experiment_type_id`；WIP 的實驗一致性由 sample 所屬 request 的 pending experiment types 驗證。

### `wips.createDispatch(wipId, { equipmentId, recipeId, estimatedDurationSeconds, note })`

Frontend payload：

```json
{
  "equipment_id": 1,
  "recipe_id": 1,
  "estimated_duration_seconds": 3600,
  "note": ""
}
```

Backend `DispatchIn` 預設 payload：

```json
{
  "equipment_id": 1,
  "recipe_id": 1,
  "note": ""
}
```

差異：`estimated_duration_seconds` 不是目前後端 schema 欄位。

### WIP actions

| Frontend method | Endpoint | Payload |
|---|---|---|
| `wips.complete(id)` | `POST /wips/{id}/complete/` | 無 |
| `wips.abort(id)` | `POST /wips/{id}/abort/` | 無 |

後端有但前端未封裝：

| Endpoint | Backend payload |
|---|---|
| `POST /wips/{id}/samples/` | `{ "sample_ids": number[] }` |
| `POST /wips/{id}/dismantle/` | 無 |

## Dispatches

### `dispatches.list(q)`

| 項目 | 內容 |
|---|---|
| Frontend endpoint | `GET /dispatches/?${query}` |
| Frontend query | 任意 object |
| Backend query | `status?: DispatchStatus`, `wip_id?: int`, `equipment_id?: int` |
| Payload | 無 |

### `dispatches.get(id)`

| 項目 | 內容 |
|---|---|
| Frontend endpoint | `GET /dispatches/{id}/` |
| Payload | 無 |
| Backend response | `DispatchDetailOut` |

### Dispatch actions

| Frontend method | Endpoint | Frontend payload | Backend schema |
|---|---|---|---|
| `dispatches.start(id)` | `POST /dispatches/{id}/start/` | 無 | 無 |
| `dispatches.unload(id)` | `POST /dispatches/{id}/unload/` | 無 | 無 |
| `dispatches.recordResult(id, payload)` | `POST /dispatches/{id}/record-result/` | 見下方 | `ExperimentResultIn` |
| `dispatches.complete(id)` | `POST /dispatches/{id}/complete/` | 無 | 無 |
| `dispatches.reportException(id, note)` | `POST /dispatches/{id}/report-exception/` | `{ "note": string }` | `ExceptionReportIn` |
| `dispatches.redispatch(id)` | `POST /dispatches/{id}/redispatch/` | 無 | 無 |
| `dispatches.abort(id)` | `POST /dispatches/{id}/abort/` | 無 | 無 |

Frontend `recordResult` payload：

```json
{
  "summary": "All checks passed.",
  "verdict": "pass",
  "data": {
    "cycles": 500,
    "failures": 0
  },
  "note": ""
}
```

Backend `ExperimentResultIn` 預設 payload：

```json
{
  "summary": "All checks passed.",
  "verdict": "pass",
  "data": {},
  "note": ""
}
```

前端接受 `data` 是 JSON string，送出前會轉成 object；後端只接受 object。

## Automation

`src/api.js` 目前未封裝 automation API。

後端有：

| Endpoint | Backend payload |
|---|---|
| `POST /automation/equipment-result/` | `{ "dispatch_id": number, "summary": string, "verdict": "pass" | "fail", "data": object }` |

## Reports

### `reports.equipmentUtilization(q)`

| 項目 | 內容 |
|---|---|
| Frontend endpoint | `GET /reports/equipment-utilization?${query}` |
| Payload | 無 |
| Backend query | `period`, `start_date`, `end_date`, `equipment_id?`, `equipment_type?`, `experiment_type_id?`, `recipe_id?`, `dispatch_status?` |

Frontend 常用 query：

```json
{
  "period": "custom",
  "start_date": "2026-05-01",
  "end_date": "2026-05-22"
}
```

### `reports.requestStatistics(q)`

| 項目 | 內容 |
|---|---|
| Frontend endpoint | `GET /reports/request-statistics?${query}` |
| Payload | 無 |
| Backend query | `start_date`, `end_date`, `date_type?`, `request_status?`, `experiment_type_id?`, `fab_user_id?`, `has_exception?`, `has_aborted_wip?`, `completed_only?`, `overdue_only?` |

Frontend 常用 query：

```json
{
  "start_date": "2026-05-01",
  "end_date": "2026-05-22"
}
```

### `reports.trends(q)`

| 項目 | 內容 |
|---|---|
| Frontend endpoint | `GET /reports/trends?${query}` |
| Frontend query | `{ "metric": "requests_per_day", "days": 30 }` |
| Backend 狀態 | 目前 `lims-backend/apps/reports/api.py` 沒有 `/reports/trends` |

這是目前 Manager dashboard 趨勢圖最明確的 API 缺口。

### Backend reports endpoint not wrapped by frontend

| Endpoint | Query |
|---|---|
| `GET /reports/operation-logs` | `start_date?`, `end_date?`, `actor_id?`, `action?` |

## 建議修正順序

1. 先修 `reports.trends`：Manager dashboard 明確會呼叫，但 backend 沒有 endpoint。
2. 修 `recipes.create/update/list normalizer`：補 `equipment_ids`、`experiment_type_ids`，並在前端顯示多實驗種類。
3. 修 `samples.list/get` response：補 `has_wip`、`received_at`，讓倒數與 in_wip 狀態可穩定顯示。
4. 修 `equipment.create/update`：決定 backend 是否正式支援 `parameters`；若不支援，前端不要送。
5. 修 `wips.create`：移除前端無效的 `experiment_type_id`，或後端 schema 正式支援並使用它。
6. 修 `dispatch.create`：若 UI 要顯示 estimated duration，後端新增欄位；否則前端不要送。
7. 補 `operation-logs` wrapper：如果 Reports 頁要顯示操作紀錄，應在 `src/api.js` 加 `reports.operationLogs(q)`。
