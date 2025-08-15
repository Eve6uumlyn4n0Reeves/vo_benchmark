# API Migration Guide

## Overview

The VO-Benchmark API has been restructured to resolve route conflicts and provide better documentation. This guide helps you migrate from legacy endpoints to the new documented API.

## Route Changes

### Primary API Endpoints (Recommended)

These endpoints are fully documented with OpenAPI/Swagger and should be used for all new integrations:

- **Documentation**: `/api/v1/docs/` - Interactive API explorer
- **Experiments**: `/api/v1/experiments/` - Experiment management (documented)
- **Health**: `/api/v1/health/` - System health checks (documented)
- **Configuration**: `/api/v1/config/` - System configuration (documented)

### Legacy API Endpoints (Deprecated)

These endpoints have been moved to avoid conflicts and will be removed in a future version:

- **Tasks**: `/api/v1/legacy/tasks/` (was `/api/v1/tasks/`)
- **Experiments**: `/api/v1/legacy/experiments/` (was `/api/v1/experiments/`)
- **Results**: `/api/v1/legacy/results/` (was `/api/v1/results/`)

## Migration Steps

### 1. Update Frontend API Calls

**Before:**
```javascript
// Old endpoints
fetch('/api/v1/experiments/')
fetch('/api/v1/tasks/task-id')
fetch('/api/v1/results/exp-id')
```

**After:**
```javascript
// New documented endpoints (recommended)
fetch('/api/v1/experiments/')  // Uses documented API
fetch('/api/v1/legacy/tasks/task-id')  // Legacy fallback
fetch('/api/v1/legacy/results/exp-id')  // Legacy fallback
// Config runtime (frontend will fetch this at startup via fetch, not ApiClient)
fetch('/api/v1/config/client')
```

### 2. Response Format Changes

The documented API may return different response formats:

**Legacy experiments list:**
```json
[
  {"experiment_id": "exp1", "name": "Test", ...},
  {"experiment_id": "exp2", "name": "Test2", ...}
]
```

**Documented experiments list:**
```json
{
  "experiments": [
    {"experiment_id": "exp1", "name": "Test", ...},
    {"experiment_id": "exp2", "name": "Test2", ...}
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 2,
    "pages": 1
  }
}
```

### 3. Error Handling
### 4. WebSocket vs Polling

- 当前版本后端 `/ws` 返回 404 并提示使用轮询端点；前端已在 `ExperimentsPage` 中仅在已连接且收到消息时才处理 WS 更新。
- 建议：启用 WebSocket 前先实现后端 `/ws`，再将 `useExperimentWebSocket` 的 `autoConnect` 打开并移除降级逻辑。


The documented API provides consistent error responses:

```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Invalid request data",
  "details": [...],
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Timeline

- **Phase 1** (Current): Both APIs available, legacy moved to `/legacy/` prefix
- **Phase 2** (Next release): Legacy endpoints marked as deprecated in responses
- **Phase 3** (Future release): Legacy endpoints removed

## Testing

Use the interactive API documentation at `/api/v1/docs/` to test the new endpoints and understand the expected request/response formats.

## Support

If you encounter issues during migration, please:
1. Check the API documentation at `/api/v1/docs/`
2. Review this migration guide
3. Test with the legacy endpoints if needed
4. Report any inconsistencies or missing functionality
