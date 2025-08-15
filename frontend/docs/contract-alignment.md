# 前端与后端API契约对齐清单 v1

本文档记录前端实现与 `backend/docs/api-contract.md` 的严格对齐情况。

## 对齐原则

- ✅ 已实现并验证
- 🚧 部分实现/进行中
- ❌ 未实现
- ⚠️ 存在差异需要注意

## 类型定义对齐

### 基础类型
- ✅ `ExperimentStatus`: CREATED | RUNNING | COMPLETED | FAILED | CANCELLED
- ✅ `TaskStatus`: CREATED | RUNNING | COMPLETED | FAILED | CANCELLED  
- ✅ `HealthStatus`: healthy | degraded | unhealthy
- ✅ `FeatureType`: SIFT | ORB
- ✅ `RansacType`: STANDARD | PROSAC
- ✅ `ExportFormat`: json | csv | xlsx

### 错误模型
- ✅ `ApiError`: { error?, error_code?, message?, details?, request_id? }
- ✅ 支持两种错误格式：{ error: string } 和结构化错误

### 分页模型
- ✅ `Pagination`: { page, limit, total, total_pages, has_next, has_previous }
- ✅ 支持 page/per_page 和 start/limit 两种分页方式

## 端点对齐映射

### 健康检查 Health
| 端点 | 前端类型 | Zod Schema | Hook/组件 | 状态 |
|------|----------|------------|-----------|------|
| `GET /api/v1/health-doc/` | `HealthResponse` | `HealthResponseSchema` | 🚧 待实现 | 🚧 |
| `GET /api/v1/health-doc/detailed` | `HealthDetailedResponse` | `HealthDetailedResponseSchema` | 🚧 待实现 | 🚧 |
| `GET /api/v1/health-doc/ready` | `HealthReadyResponse` | `HealthReadyResponseSchema` | 🚧 待实现 | 🚧 |

### 配置 Config
| 端点 | 前端类型 | Zod Schema | Hook/组件 | 状态 |
|------|----------|------------|-----------|------|
| `GET /api/v1/config/client` | `ClientConfig` | `ClientConfigSchema` | 🚧 待实现 | 🚧 |
| `GET /api/v1/config/system` | `Record<string, unknown>` | - | 🚧 待实现 | 🚧 |
| `GET /api/v1/config/algorithms` | `AlgorithmConfig` | `AlgorithmConfigSchema` | 🚧 待实现 | 🚧 |
| `GET /api/v1/config/diagnostics` | `DiagnosticsConfig` | `DiagnosticsConfigSchema` | 🚧 待实现 | 🚧 |

### 实验 Experiments
| 端点 | 前端类型 | Zod Schema | Hook/组件 | 状态 |
|------|----------|------------|-----------|------|
| `GET /api/v1/experiments-doc/` | `ExperimentsListResponse` | `ExperimentsListResponseSchema` | 🚧 待实现 | 🚧 |
| `POST /api/v1/experiments-doc/` | `CreateExperimentResponse` | `CreateExperimentResponseSchema` | 🚧 待实现 | 🚧 |
| `GET /api/v1/experiments-doc/{id}` | `Experiment` | `ExperimentSchema` | 🚧 待实现 | 🚧 |
| `DELETE /api/v1/experiments-doc/{id}` | - | - | 🚧 待实现 | ❌ 405 |

### 结果 Results
| 端点 | 前端类型 | Zod Schema | Hook/组件 | 状态 |
|------|----------|------------|-----------|------|
| `GET /api/v1/results/{id}/overview` | `Record<string, unknown>` | - | 🚧 待实现 | 🚧 |
| `GET /api/v1/results/{id}/diagnose` | `Record<string, unknown>` | - | 🚧 待实现 | 🚧 |
| `GET /api/v1/results/{id}/{alg}` | `AlgorithmResultResponse` | `AlgorithmResultResponseSchema` | 🚧 待实现 | 🚧 |
| `GET /api/v1/results/{id}/{alg}/frames` | `FrameResultsResponse` | `FrameResultsResponseSchema` | 🚧 待实现 | 🚧 |
| `GET /api/v1/results/{id}/{alg}/pr-curve` | `PRCurveResponse` | `PRCurveResponseSchema` | 🚧 待实现 | 🚧 |
| `GET /api/v1/results/{id}/{alg}/trajectory` | `TrajectoryResponse` | `TrajectoryResponseSchema` | 🚧 待实现 | 🚧 |
| `GET /api/v1/results/{id}/export` | `Blob` | - | 🚧 待实现 | 🚧 |

### 任务 Tasks
| 端点 | 前端类型 | Zod Schema | Hook/组件 | 状态 |
|------|----------|------------|-----------|------|
| `GET /api/v1/tasks/` | `TaskResponse[]` | `z.array(TaskResponseSchema)` | 🚧 待实现 | 🚧 |
| `GET /api/v1/tasks/{id}` | `TaskResponse` | `TaskResponseSchema` | 🚧 待实现 | 🚧 |
| `POST /api/v1/tasks/{id}/cancel` | `TaskCancelResponse` | - | 🚧 待实现 | 🚧 |

### 事件 Events (SSE)
| 端点 | 前端类型 | Hook/组件 | 状态 |
|------|----------|-----------|------|
| `GET /api/v1/events/stream` | `SSEMessage` | `useSSE` | ✅ |

## 关键验证点

### PR曲线数据验证
- ✅ 空数组处理：`precisions: []` 表示无数据状态
- ✅ 数值范围验证：precision/recall 在 [0,1] 范围内
- ✅ 运行时 Zod 验证：防止渲染错误数据

### 轨迹数据验证
- ✅ `poses` 必需字段
- ✅ `gt` 和 `ref` 可选字段
- ✅ `include_reference` 参数控制 `ref` 字段返回

### 分页参数验证
- ✅ 支持 `page/per_page` (优先)
- ✅ 支持 `start/limit` (兼容)
- ✅ 参数范围验证：page ≥ 1, per_page ∈ [1,100], start ≥ 0, limit ∈ [1,1000]

### 错误处理验证
- ✅ 4xx 错误不重试
- ✅ 5xx 和网络错误有限重试
- ✅ 结构化错误解析
- ✅ request_id 追踪

## 实现的基础设施

### HTTP 客户端
- ✅ Axios 配置：baseURL `/api/v1`
- ✅ 请求拦截器：添加 request-id
- ✅ 响应拦截器：错误解析与重试逻辑
- ✅ 超时配置：30秒默认

### React Query 集成
- ✅ queryKeys 层次化管理
- ✅ 缓存策略：staleTime 5分钟，gcTime 10分钟
- ✅ 重试策略：4xx 不重试，其他错误最多2次

### 运行时验证
- ✅ Zod schemas 覆盖关键响应
- ✅ `validateApiResponse` 辅助函数
- ✅ 验证失败时错误UI降级

### 工具 Hooks
- ✅ `useApiBaseUrl`: 环境变量配置
- ✅ `usePagination`: 分页状态管理
- ✅ `useSSE`: Server-Sent Events 连接

## 测试覆盖

### 单元测试
- ✅ Zod schemas 验证测试
- ✅ usePagination hook 测试
- ✅ HTTP 客户端错误处理测试
- ✅ 分页转换函数测试

### 覆盖率目标
- 🚧 当前覆盖率：待测量
- 🎯 目标覆盖率：≥70%

## 已知差异与注意事项

### 文档路径差异
- ⚠️ 健康检查使用 `/health-doc/` 而非 `/health/`
- ⚠️ 实验使用 `/experiments-doc/` 而非 `/experiments/`
- 📝 前端严格按照 api-contract.md 实现

### 可选字段处理
- ⚠️ 轨迹 `gt` 字段：无GT时不返回，前端需处理 undefined
- ⚠️ PR曲线空数据：空数组而非 null，前端需正确识别

### 分页兼容性
- ✅ 优先使用 `page/per_page`
- ✅ 兼容 `start/limit` 用于帧结果等大数据集

## 下一步实施

1. **阶段3**: 实现 Config/Health 页面与 API 集成
2. **阶段4**: 实现 Experiments 功能与表单验证
3. **阶段5**: 实现 Results 可视化与数据验证
4. **阶段6**: 实现 Tasks 管理与 SSE 集成
5. **阶段7**: 性能优化与最终验证

## 更新记录

- **v1.0** (2025-01-13): 初始版本，基础类型与 schemas 完成
- 后续版本将记录各阶段的实现进展与验证结果
