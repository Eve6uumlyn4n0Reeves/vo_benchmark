# 诊断与排障（Windows 优先）

本指南旨在快速定位“看不到数据”“曲线空白”“SSE 没心跳”等常见问题，并提供命令级解决方案。

## 一、统一存储根与目录结构

- 唯一真实来源（SSOT）：ConfigManager.storage.results_root
- 应用启动时会将 OutputDirectoryManager 指向 `${RESULTS_ROOT}/experiments`
- 历史遗留：若你此前使用过双层目录 `experiments/experiments/<id>`，请执行迁移脚本

步骤：
1) Dry-run 迁移
```
python backend/scripts/migrate_results_root.py --root "<RESULTS_ROOT>"
```
2) 执行迁移（带备份）
```
python backend/scripts/migrate_results_root.py --root "<RESULTS_ROOT>" --apply --backup
```

验证：
- GET /api/v1/config/diagnostics → results_root 与 visible_experiments 正确

## 二、PR 曲线空白/报错

症状：
- 前端 PR 图为空白或显示“暂无数据”
- /api/v1/results/{exp}/{alg}/pr-curve 返回 500："PR curve computation requires scikit-learn"

解决：
1) 安装 scikit-learn（与 numpy/scipy 版本匹配）
```
cd backend
pip install -r requirements.txt
```
2) 如果不希望现算，前端可仅展示预计算结果，或后端设置特征开关禁用现算（如后续提供）
3) 通过 /api/v1/results/{exp}/{alg} 检查是否有可用分数/标签数据

## 三、SSE 无心跳/断开

症状：
- 浏览器 Network 中 /api/v1/events/ 无数据或很快断开

排查：
- 开发环境（Vite）代理：确认未对 SSE 路由做 gzip/缓冲；仓库默认已关闭
- 生产（Nginx）配置：仅对 /api/v1/events/ 关闭 proxy_buffering 与 gzip，参考 frontend/nginx.conf
- 多进程/多实例：In‑Memory 事件总线不支持跨进程广播 → 使用 Redis 模式

启用 Redis 模式：
```
# 环境变量
set EVENT_BUS=redis
set REDIS_URL=redis://localhost:6379/0
# 安装依赖
cd backend
pip install -r requirements.txt
```

验证：
- 多个后端进程下，创建任务/追加日志能被单一浏览器 EventSource 持续接收

## 四、数据“看得见、点不动/空结果”

- 使用诊断接口：
```
GET /api/v1/results/{experiment_id}/diagnose
```
- 检查返回字段：
  - storage_root：当前后端使用的根路径
  - visible_keys：可见存储键（前 100 条）
  - algorithms：后端解析出的算法 key 列表
  - per_algorithm.{alg}.metrics_exists/frames_exists：文件级可见性

## 五、Windows 常见坑

- 路径分隔符：统一使用 Python Path 处理；环境变量建议使用绝对路径
- 端口占用：
```
netstat -ano | findstr :5000
# taskkill /PID <pid> /F
```
- venv 激活：
```
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 六、快速健康检查

- 健康：/api/v1/health-doc/、/api/v1/health-doc/detailed、/api/v1/health-doc/ready
- 依赖：health-detailed 会检测 OpenCV/NumPy/Flask 等
- 任务：/api/v1/tasks/、/api/v1/tasks/{id}、/api/v1/tasks/{id}/logs
- 配置：/api/v1/config/system、/api/v1/config/algorithms、/api/v1/config/diagnostics

## 七、自动化测试/冒烟

- 后端：
```
cd backend
pytest -q
```
- 前端连通性（dev）：
```
cd frontend
npm run check:connect
```

## 八、常见错误对照

- 500 PR 曲线缺依赖：安装 scikit-learn
- 轨迹 success_rate 始终为 0：升级至修复后的版本（已改从 metrics 读取）
- 看不到新实验：检查 OutputDirectoryManager 根是否正确（见一），或 pipeline 是否成功落盘

---

如需要更多帮助，请附上：系统、Python/Node 版本、后端日志、/config/diagnostics 响应片段。
