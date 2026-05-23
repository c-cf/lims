# lims-frontend API 與 lims-backend main Payload 對照

整理日期：2026-05-22

比對來源：

- 前端：`lims-frontend/src/api.js`
- 後端：`lims-backend` 的 `origin/main`（commit `b8013df7ec1adb805d0179e7e3d6aba08639bd0d`）

## 主要結論

`lims-frontend` 目前比較接近 `wiwi` branch 的後端，不是完全相容 `lims-backend main`。若直接接 `main`，最容易失敗或資料顯示不完整的是：

1. Recipe create/update：前端已偏向「recipe 不綁單一 equipment / 可多實驗種類」，但 `main` 仍是「recipe 必須綁單一 `equipment_id` + 單一 `experiment_type_id`」。
2. WIP create：前端送 `experiment_type_id` + `sample_ids`，`main` 要的是 `equipment_id` + `sample_ids`。
3. Dispatch create：前端送 `equipment_id` + `recipe_id`，`main` 要的是 `experiment_type_id` + `recipe_id`。
4. Request update：前端可能送 `experiment_type_ids`、`experiment_parameters`、`samples`，但 `main` 的 `RequestUpdateIn` 只支援 `title`、`note`。
5. Reports trends：前端呼叫 `/reports/trends`，`main` 沒有這個 endpoint。
6. Reports / dashboard 進階欄位：前端 dashboard/report 期待的多數統計欄位在 `main` 不存在。

## Auth

| Frontend method | Endpoint | Frontend payload | Backend main schema | 相容性 |
|---|---|---|---|---|
| `auth.login(username, password)` | `POST /auth/login` | `{ "username": string, "password": string }` | `LoginIn` 同前端 | 相容 |
| `auth.logout()` | `POST /auth/logout` | `{ "refresh_token": string }` | `RefreshIn` 同前端 | 相容 |
| internal refresh | `POST /auth/refresh` | `{ "refresh_token": string }` | `RefreshIn` 同前端 | 相容 |
| `auth.me()` | `GET /auth/me` | 無 | 無 payload | 相容 |

## Experiment Types

| Frontend method | Endpoint | Frontend query/payload | Backend main | 相容性 |
|---|---|---|---|---|
| `experimentTypes.list(q)` | `GET /experiment-types/?${query}` | `search?`, `lab_category?`, `is_active?` | 同樣支援這些 query | 相容 |

`main` 也有 create/update/delete experiment type，但 `src/api.js` 沒封裝。

## Equipment

### List

| Frontend method | Endpoint | Frontend query | Backend main query | 相容性 |
|---|---|---|---|---|
| `equipment.list(q)` | `GET /equipment/?${query}` | 任意 object | `search?`, `status?` | 基本相容 |

### Create

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

Backend main `EquipmentIn`：

```json
{
  "name": "QA-MULTI-01",
  "model_name": "Multi Tool",
  "capacity": 4,
  "experiment_type_ids": [1, 2]
}
```

相容性：部分相容。`parameters`、`status` 不是 main 的 schema 欄位。

### Update

Frontend payload：

```json
{
  "name": "QA-MULTI-01",
  "model_name": "Multi Tool",
  "capacity": 4,
  "status": "maintenance",
  "parameters": {}
}
```

Backend main `EquipmentUpdate`：

```json
{
  "name": "QA-MULTI-01",
  "model_name": "Multi Tool",
  "capacity": 4,
  "status": "maintenance"
}
```

相容性：部分相容。`parameters` 不是 main 的 schema 欄位。

### Capabilities

| Frontend method | Endpoint | Payload | Backend main schema | 相容性 |
|---|---|---|---|---|
| `equipment.setCapabilities(id, experimentTypeIds)` | `POST /equipment/{id}/capabilities` | `{ "experiment_type_ids": number[] }` | `CapabilitySetIn` | 相容 |

## Recipes

### List

| Frontend method | Endpoint | Query | Backend main query | 相容性 |
|---|---|---|---|---|
| `recipes.list(q)` | `GET /recipes/?${query}` | 任意 object | `equipment_id?`, `experiment_type_id?`, `is_active?` | 基本相容 |

Backend main response 是單一 equipment：

```json
{
  "id": 1,
  "name": "TCT_STD",
  "description": "",
  "equipment": { "id": 1, "name": "QA-TAT-01" },
  "experiment_type": { "id": 1, "name": "Temperature Cycling Test" },
  "parameters": {},
  "is_active": true
}
```

目前前端曾經針對新後端讀過 `equipments` / `experiment_types` 的需求，但 `main` 只有 `equipment` / `experiment_type`。

### Create

Frontend payload：

```json
{
  "name": "TCT_STD",
  "description": "",
  "experiment_type_id": 1,
  "parameters": {}
}
```

Backend main `RecipeIn`：

```json
{
  "name": "TCT_STD",
  "description": "",
  "equipment_id": 1,
  "experiment_type_id": 1,
  "parameters": {}
}
```

相容性：不完整。`main` 必填 `equipment_id`，前端目前 create 沒送。

### Update

Frontend payload：

```json
{
  "name": "TCT_STD",
  "description": "",
  "parameters": {}
}
```

Backend main `RecipeUpdate`：

```json
{
  "name": "TCT_STD",
  "description": "",
  "parameters": {}
}
```

相容性：相容，但 `main` 本來就不支援 update equipment / experiment type。

## Requests

### List / Get

| Frontend method | Endpoint | Payload/query | Backend main | 相容性 |
|---|---|---|---|---|
| `requests.list(q)` | `GET /requests/?${query}` | `status?` | `status?` | 相容 |
| `requests.get(id)` | `GET /requests/{id}` | 無 | 無 payload | 相容 |

### Create

Frontend payload：

```json
{
  "title": "051711",
  "note": "",
  "urgency": "1w",
  "experiment_type_ids": [1, 2],
  "experiment_parameters": {
    "1": {}
  },
  "samples": [
    { "wafer_id": "W001", "wafer_size": "200mm" }
  ]
}
```

Backend main `RequestIn`：

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

相容性：大致相容，但 `urgency` 不是 main 欄位。

### Update

Frontend 可能送：

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

Backend main `RequestUpdateIn`：

```json
{
  "title": "051711",
  "note": ""
}
```

相容性：不完整。`main` 不支援 draft 編輯時更新 experiments / samples。

### Actions

| Frontend method | Endpoint | Payload | Backend main | 相容性 |
|---|---|---|---|---|
| `requests.submit(id)` | `POST /requests/{id}/submit` | 無 | 無 | 相容 |
| `requests.approve(id)` | `POST /requests/{id}/approve` | 無 | 無 | 相容 |
| `requests.returnRequest(id, comment)` | `POST /requests/{id}/return` | `{ "comment": string }` | `CommentIn` | 相容 |
| `requests.reject(id, comment)` | `POST /requests/{id}/reject` | `{ "comment": string }` | `CommentIn` | 相容 |
| `requests.ship(id)` | `POST /requests/{id}/ship` | 無 | 無 | 相容 |
| `requests.cancel(id, reason)` | `POST /requests/{id}/cancel` | `{ "reason": string }` | `ReasonIn` | 相容 |
| `requests.close(id)` | `POST /requests/{id}/close` | 無 | 無 | 相容 |

## Samples

### List / Get

| Frontend method | Endpoint | Payload/query | Backend main | 相容性 |
|---|---|---|---|---|
| `samples.list(q)` | `GET /samples/?${query}` | `request_id?`, `status?` | 同 | 基本相容 |
| `samples.get(id)` | `GET /samples/{id}` | 無 | 無 | 基本相容 |

前端 normalizer 額外期待：

```json
{
  "has_wip": true,
  "received_at": "2026-05-22T00:00:00Z"
}
```

Backend main 沒有這兩個欄位，所以 `in_wip` 與倒數時間只能 fallback。

### Actions

| Frontend method | Endpoint | Payload | Backend main |
|---|---|---|---|
| `samples.receive(id)` | `POST /samples/{id}/receive` | 無 | 相容 |
| `samples.rejectReceiving(id, reason)` | `POST /samples/{id}/reject-receiving` | `{ "reason": string }` | 相容 |
| `samples.reportLost(id)` | `POST /samples/{id}/report-lost` | 無 | 相容 |
| `samples.void(id)` | `POST /samples/{id}/void` | 無 | 相容 |
| `samples.return(id)` | `POST /samples/{id}/return` | 無 | 相容 |

## WIP

### Create

Frontend payload：

```json
{
  "experiment_type_id": 1,
  "sample_ids": [1, 2],
  "note": ""
}
```

Backend main `WIPIn`：

```json
{
  "sample_ids": [1, 2],
  "equipment_id": 1,
  "note": ""
}
```

相容性：不相容。`main` 是 WIP 建立時選 equipment；目前前端設計是 dispatch 時選 equipment。

### Dispatch create

Frontend payload：

```json
{
  "equipment_id": 1,
  "recipe_id": 1,
  "estimated_duration_seconds": 3600,
  "note": ""
}
```

Backend main `DispatchIn`：

```json
{
  "experiment_type_id": 1,
  "recipe_id": 1,
  "note": ""
}
```

相容性：不相容。`main` 的 equipment 來自 WIP；目前前端是在 dispatch 選 equipment。

### Other WIP actions

| Frontend method | Endpoint | Payload | Backend main |
|---|---|---|---|
| `wips.list(q)` | `GET /wips/?${query}` | query | 基本相容 |
| `wips.get(id)` | `GET /wips/{id}/` | 無 | 相容 |
| `wips.complete(id)` | `POST /wips/{id}/complete/` | 無 | 相容 |
| `wips.abort(id)` | `POST /wips/{id}/abort/` | 無 | 相容 |

Backend main 有 `POST /wips/{id}/samples/`，但前端未封裝。

## Dispatches

### List / Get

| Frontend method | Endpoint | Payload/query | Backend main | 相容性 |
|---|---|---|---|---|
| `dispatches.list(q)` | `GET /dispatches/?${query}` | `status?`, `wip_id?`, `equipment_id?` | 同 | 基本相容 |
| `dispatches.get(id)` | `GET /dispatches/{id}/` | 無 | 無 | 相容 |

### Actions

| Frontend method | Endpoint | Payload | Backend main |
|---|---|---|---|
| `dispatches.start(id)` | `POST /dispatches/{id}/start/` | 無 | 相容 |
| `dispatches.unload(id)` | `POST /dispatches/{id}/unload/` | 無 | 相容 |
| `dispatches.recordResult(id, payload)` | `POST /dispatches/{id}/record-result/` | `{ "summary": string, "verdict": "pass" \| "fail", "data": object, "note": string }` | 相容 |
| `dispatches.complete(id)` | `POST /dispatches/{id}/complete/` | 無 | 相容 |
| `dispatches.reportException(id, note)` | `POST /dispatches/{id}/report-exception/` | `{ "note": string }` | 相容 |
| `dispatches.redispatch(id)` | `POST /dispatches/{id}/redispatch/` | 無 | 相容 |
| `dispatches.abort(id)` | `POST /dispatches/{id}/abort/` | 無 | 相容 |

## Reports

### Equipment utilization

Frontend 常用 query：

```json
{
  "period": "custom",
  "start_date": "2026-05-01",
  "end_date": "2026-05-22",
  "equipment_id": 1
}
```

Backend main query：

```json
{
  "period": "custom",
  "start_date": "2026-05-01",
  "end_date": "2026-05-22",
  "equipment_id": 1
}
```

相容性：基本相容，但 `main` 回傳欄位較少，只含 `equipment.id/name`、`wip_count`、`sample_count`。

### Request statistics

Frontend 常用 query：

```json
{
  "start_date": "2026-05-01",
  "end_date": "2026-05-22"
}
```

Backend main query：

```json
{
  "start_date": "2026-05-01",
  "end_date": "2026-05-22"
}
```

相容性：基本相容，但 `main` 回傳欄位較少，只含：

```json
{
  "period": { "start_date": "2026-05-01", "end_date": "2026-05-22" },
  "status_distribution": {},
  "average_tat_hours": null,
  "total_requests": 0
}
```

### Trends

| Frontend method | Endpoint | Backend main |
|---|---|---|
| `reports.trends(q)` | `GET /reports/trends?metric=...&days=...` | 不存在 |

## 建議

如果這個 `lims-frontend` 要接 `lims-backend main`，要先做相容層或回退前端流程：

1. Recipe create 改回送 `equipment_id`。
2. WIP create 改回送 `equipment_id`，不要送 `experiment_type_id`。
3. Dispatch create 改回送 `experiment_type_id`，不要送 `equipment_id`。
4. Draft request edit 只能改 `title/note`，或把 main 後端補成支援更新 experiments/samples。
5. Manager dashboard 不要依賴 `/reports/trends`，或先在 main 後端補 endpoint。
6. 若 sample countdown / in-WIP 顯示要正確，main 後端需補 `received_at`、`has_wip`。
