# VO-Benchmark：视觉里程计特征匹配评测平台

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 16+](https://img.shields.io/badge/node.js-16+-green.svg)](https://nodejs.org/)
[![React](https://img.shields.io/badge/React-18-blue.svg)](https://reactjs.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3+-red.svg)](https://flask.palletsprojects.com/)

一个专业的视觉里程计特征匹配评测与可视化平台，基于 Flask（后端）与 React + Vite（前端）构建。支持多种数据集格式、算法对比、实时监控和详细的性能分析。

## ✨ 核心特性

### 🗂️ 数据集管理
- **多格式支持**: TUM RGB-D、KITTI、EuRoC MAV（可扩展）
- **智能检测**: 自动识别数据集格式和结构
- **路径配置**: 支持多路径扫描和环境变量配置
- **验证工具**: 数据完整性检查和统计信息

### 🧪 实验管理
- **批量实验**: 支持多算法、多参数组合的批量测试
- **实时监控**: 基于 Server-Sent Events (SSE) 的实时进度更新
- **结果存储**: 高效的文件系统存储，支持压缩和序列化
- **任务队列**: 内存任务管理，无需外部依赖

### 📊 结果分析
- **轨迹可视化**: 2D/3D 轨迹对比，支持多视角切换
- **PR 曲线**: 精确度-召回率曲线分析，AUC 计算
- **性能指标**: RMSE、ATE、RPE 等多维度评估
- **数据导出**: 支持 JSON、CSV 格式导出

### 🎨 用户界面
- **现代化设计**: Material-UI 组件库，支持亮/暗主题
- **响应式布局**: 适配桌面和移动设备
- **交互式图表**: Plotly.js 和 Recharts 驱动的动态可视化
- **实时更新**: WebSocket 连接，自动回退到轮询

## 🏗️ 项目结构

```
vo-benchmark/
├── 📁 backend/                    # Flask 后端服务
│   ├── 📁 src/
│   │   ├── 📁 api/               # REST API 路由和文档
│   │   ├── 📁 core/              # 核心算法模块
│   │   │   ├── 📁 features/      # 特征提取和匹配
│   │   │   └── 📁 ransac/        # 鲁棒估计算法
│   │   ├── 📁 datasets/          # 数据集处理
│   │   ├── 📁 storage/           # 存储系统
│   │   └── 📁 utils/             # 工具函数
│   ├── 📄 requirements.txt       # Python 依赖
│   └── 📄 start_server.py        # 服务器启动脚本
├── 📁 frontend/                   # React 前端应用
│   ├── 📁 src/
│   │   ├── 📁 api/               # API 客户端
│   │   ├── 📁 components/        # React 组件
│   │   ├── 📁 features/          # 功能模块
│   │   ├── 📁 hooks/             # 自定义 Hooks
│   │   └── 📁 utils/             # 工具函数
│   ├── 📄 package.json           # Node.js 依赖
│   └── 📄 vite.config.ts         # Vite 配置
├── 📁 docs/                      # 项目文档
├── 📄 setup.py                   # 自动化安装脚本
├── 📄 start.bat                  # Windows 启动脚本
├── 📄 start.sh                   # Linux/macOS 启动脚本
├── 📄 docker-compose.yml         # Docker 编排
└── 📄 README.md                  # 项目说明

## 🚀 快速开始

### 方式一：一键启动（推荐）
- Windows：双击根目录 start.bat（或在终端执行 start.bat）
- Linux/macOS：
  ```bash
  chmod +x start.sh
  ./start.sh
  ```
- 跨平台 Python 脚本：
  ```bash
  python setup.py
  ```
脚本会自动：检测 Python/Node 环境 → 安装依赖（如未安装）→ 启动后端(5000)与前端(3000)。

### 方式二：Docker Compose（生产/一键部署）
```bash
# 克隆仓库
git clone https://github.com/Eve6uumlyn4n0Reeves/vo_benchmark.git
cd vo_benchmark

# 一键启动
docker compose up --build -d
# 前端: http://127.0.0.1:3000  后端: http://127.0.0.1:5000  文档: http://127.0.0.1:5000/api/v1/docs/
```

### 方式三：手动安装（开发者）
1) 后端（Python 3.8+）
```bash
cd backend
python -m venv venv
# Windows
venv\\Scripts\\activate
# macOS/Linux
source venv/bin/activate
pip install -r requirements.txt
python start_server.py
```
2) 前端（Node.js 16+/18+）
```bash
cd frontend
npm install
npm run dev
```

### 🔧 必备环境
- Python 3.8+（推荐 3.10+）
- Node.js 16+（推荐 18+）
- Windows 10+/macOS 10.15+/Ubuntu 18.04+

### 🧩 常用环境变量
- 后端（运行前导出/设置）：
  - `SECRET_KEY`：生产环境必须设置
  - `CORS_ORIGINS`：允许的前端来源（逗号分隔）
  - `DATASET_PATHS`：数据集扫描路径（多个用 `;` 或 `:` 分隔）
  - `FLASK_PORT`：默认 5000
- 前端（开发时可用）：
  - `VITE_BACKEND_HOST`/`VITE_BACKEND_PORT`：后端地址（默认 127.0.0.1:5000）
  - `VITE_FRONTEND_PORT`：前端端口（默认 3000）

### 📁 数据集路径配置（可选）
可通过环境变量 `DATASET_PATHS` 指定多个扫描目录，支持“数据集根目录”和“单序列目录”混合：
```powershell
$env:DATASET_PATHS = "C:\\Datasets\\TUM_RGBD;D:\\Research\\TUM_RGBD;C:\\Datasets\\TUM_RGBD\\rgbd_dataset_freiburg1_xyz"
```

### ✅ 健康检查与文档
- 健康检查：http://127.0.0.1:5000/api/v1/health
- OpenAPI 文档：http://127.0.0.1:5000/api/v1/docs/

## 🧭 命令速查（Cheat Sheet）
- 启动后端：`cd backend && python start_server.py`
- 启动前端：`cd frontend && npm run dev`
- 运行后端测试：`cd backend && pytest -q`
- 构建前端生产包：`cd frontend && npm run build`
- 预览生产包：`cd frontend && npm run preview`
- 一键脚本（自动安装并启动）：`start.bat`（Windows）/ `./start.sh`（Linux/macOS） / `python setup.py`



## 后端文档入口
- 分模块架构说明（后端）：backend/docs/backend-modules.md
- 接口契约文档（后端 API）：backend/docs/api-contract.md
- Swagger 在线文档：/api/v1/docs/


## 技术架构

### 后端架构
- **存储系统**: 基于文件系统的存储，支持 JSON/Pickle 格式和压缩
- **任务管理**: 内存中的任务队列，无需 Redis/Celery
- **实时通信**: Server-Sent Events (SSE) 用于实时更新推送
- **API 文档**: Flask-RESTX 自动生成的 OpenAPI 文档
- **错误处理**: 统一的错误处理中间件和异常管理

### 前端架构
- **框架**: React 18 + TypeScript + Vite
- **状态管理**: Redux Toolkit
- **UI 组件**: Material-UI (MUI)
- **图表可视化**: Plotly.js + Recharts
- **实时更新**: SSE 客户端，自动回退到轮询
- **配置管理**: 分层配置系统（环境变量 + 服务器配置 + 默认值）

## 本地运行（Windows / PowerShell）

### 使用 Docker Compose（推荐一键）
```
# 根目录
docker compose up --build -d
# 前端 http://127.0.0.1:3000 ，后端 http://127.0.0.1:5000
```
- 自定义 CORS：运行前设置环境变量
```
$env:CORS_ORIGINS = "http://localhost:3000,https://your.domain"
```


### 1) 后端
要求：Python 3.12+
```
cd vo-benchmark/backend
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
```

可选：为数据集指定扫描路径（支持分号 ; 或冒号 : 分隔，多路径按顺序扫描）
示例（同时包含“数据集根目录”和“单个序列目录”）：
```powershell
$env:DATASET_PATHS="C:\\Datasets\\TUM_RGBD;D:\\Research\\TUM_RGBD;C:\\Datasets\\TUM_RGBD\\rgbd_dataset_freiburg1_xyz"
```

### 常用后端 API 路径（对齐当前实现）
- 健康检查：
  - 基础/详细/就绪（非文档版）：/api/v1/health/、/api/v1/health/detailed、/api/v1/health/ready
  - 带 OpenAPI 文档版本：/api/v1/health-doc/、/api/v1/health-doc/detailed、/api/v1/health-doc/ready
- 实验管理：
  - 非文档版：/api/v1/experiments/（GET/POST）、/api/v1/experiments/{id}（GET/DELETE）
  - 带 OpenAPI 文档版本：/api/v1/experiments-doc/（GET/POST）、/api/v1/experiments-doc/{id}（GET/DELETE）
- 结果查询：/api/v1/results/{experiment_id}/{algorithm_key}、/frames、/pr-curve、/trajectory（支持 include_reference）
- 任务：/api/v1/tasks/（列表）、/api/v1/tasks/{task_id}（详情）、/api/v1/tasks/{task_id}/cancel（取消）
- 配置：/api/v1/config/client、/api/v1/config/system、/api/v1/config/algorithms、/api/v1/config/diagnostics

### 启动与调试（后端）
- 本地开发：
```
cd backend
python start_server.py
```
- 健康检查与文档：
```
http://127.0.0.1:5000/api/v1/health/
http://127.0.0.1:5000/api/v1/docs/
```
- 运行测试：
```
cd backend
pytest -q
```


# 示例：同时包含“数据集根目录”和“单个序列目录”
$env:DATASET_PATHS="C:\\Datasets\\TUM_RGBD;D:\\Research\\TUM_RGBD;C:\\Datasets\\TUM_RGBD\\rgbd_dataset_freiburg1_xyz"
.\.venv\Scripts\python start_server.py
```
- 健康检查：http://127.0.0.1:5000/api/v1/health
- API 文档：http://127.0.0.1:5000/api/v1/docs/

注意：若看到 `ModuleNotFoundError: No module named 'sqlalchemy'`，请确认 `backend/requirements.txt` 已包含 `sqlalchemy>=2.0.0` 并重新安装依赖。

### 2) 前端
要求：Node.js 18+（或 20+）
### 任务与事件（接口化与实现）
- 默认实现：InMemory（单进程、离线可用），不需要任何外部依赖
- 接口：`IEventBus`、`ITaskBackend`（见 `backend/src/api/services/interfaces.py`）
- 默认实现：`InMemoryEventBus`、`InMemoryTaskBackend`（见 `backend/src/api/services/inmemory_impl.py`）
- 预留：Redis 实现（未来可通过环境变量选择实现，例如 `REDIS_URL` 和 `ENABLE_REDIS_*` 开关），无需改业务层代码

```
cd vo-benchmark/frontend
npm install
$env:VITE_BACKEND_HOST="127.0.0.1"
$env:VITE_BACKEND_PORT="5000"
$env:VITE_FRONTEND_PORT="3000"
npm run dev
```
- 访问前端：http://127.0.0.1:3000

若提示 `vite 不是内部或外部命令`，请先执行 `npm install` 再重试。

#### 构建与预览
```
cd vo-benchmark/frontend
npm run build
npm run preview
```
> 如遇 `EPERM`（esbuild.exe 占用）请关闭占用的进程/杀软后执行：
```
rmdir /s /q node_modules
del /f /q package-lock.json
npm install
npm run build
```

## 前端使用要点
- 顶部工具栏右侧可切换“亮/暗”主题（会持久化到本地）。
- 统一错误处理：接口错误会以右上角通知浮层提示，并尝试上报到 `/api/v1/errors`（失败降级为本地保存）。
- 结果分析页面（Results）包含：算法总览、性能对比、PR 曲线、帧级详情与轨迹可视化，可导出与对比。
  - 重型图表组件（PR 曲线、轨迹）按需懒加载。
  - 帧表格支持虚拟滚动，提升大数据量渲染性能。

### UI 主题规范（MUI）
- 主题入口：`src/config/theme.ts`，通过 `buildAppTheme(mode)` 统一设置主/辅色、字体层级、间距、圆角与断点。
- 全局启用：`src/main.tsx` 使用 `ThemeProvider` 注入，支持亮/暗主题切换（本地持久化 `STORAGE_KEYS.THEME`）。
- 组件规范：
  - `Card` 统一 `variant="outlined"`、圆角 12px、内容内边距 24px。
  - `Grid` 默认 `spacing=3`，页面卡片留白统一。
  - `Button/IconButton/Tooltip` 默认尺寸统一，禁用文本全大写。
  - 全局样式微调见 `src/styles/layout-fixes.css`（避免覆盖主题语义色）。

### 图表交互与导出
- PR 曲线（Plotly）：
  - 使用 `CHART_COLORS`，图例固定在右侧（纵向）。坐标轴固定 0-1，等比例网格；暗色模式自动调整文字/网格对比度。
  - 悬浮提示：Precision/Recall/Threshold/AUC；工具栏导出 PNG，文件名含算法与时间戳。
  - 最优点高对比样式（星形 + 描边），支持传入 `title/subtitle`（i18n）。
- 轨迹可视化（Recharts）：
  - 提供 XY/XZ/YZ/误差视图切换；Tooltip 数值单位统一（m/s）。
  - 空数据状态显示友好提示；暗色模式网格/文字对比度提升。

### 暗黑模式注意点
- 颜色与分隔线统一走主题 `palette` 与 `divider`；避免在 CSS 中硬编码黑/白背景色。
- 图表主题从 `CHART_THEME/DARK_CHART_THEME` 读取，Plotly `layout.font.color/gridcolor` 随主题切换。
- 表格头/体分隔线采用半透明黑色（暗色模式下由主题接管），避免白色分隔线在亮色下过强。

### 统一配置 Hook 约定（前端）
- 仅保留一个入口：`hooks/useConfig.ts` 中的 `useConfig` 和派生 Hook。
- 实验默认值请使用 `useExperimentConfigFromManager()`（基于 `/api/v1/config/client` 与默认配置合并），废弃 `hooks/useExperimentConfig.ts` 直连 API 的旧实现。
- 算法可选类型（特征/RANSAC）请使用 `useAlgorithms()`（内部走 `GET /config/algorithms`，失败回退默认）。

### WebSocket 与降级
- 前端使用 `services/websocket.ts + hooks/useWebSocket.ts`，`WS_BASE_URL` 来自配置（env 或 `config/defaults.ts`）。
- 重连策略：间隔 `reconnectInterval`，最多 `maxReconnectAttempts` 次；超过次数自动回退轮询（Tasks 页有轮询兜底）。
- 后端未启用 `/ws` 时，WebSocket 会连接失败并保持轮询；日志级别以 info 打印“达到最大重连次数，将回退轮询”。

### 可视化懒加载注意点
- PR 曲线与轨迹组件通过 React.lazy 加载，页面首次切换到相应 Tab 时再加载，避免首屏负担。
- 传入数据需满足严格类型：`PRCurvePlot` 接收 `PRCurveData[]`；轨迹可视化接收 `[{ algorithm_name, estimated_trajectory, ground_truth_trajectory, rmse, color }]`。

### 取消实验（约定说明）
- 当前版本未提供 /monitoring 路由；如需取消/控制实验，请在任务/队列接入后通过任务系统实现（未来版本将通过统一的任务接口暴露）。

## 开发端口与连通性

- 开发端口：前端默认 3000（VITE_FRONTEND_PORT 可覆盖）；后端默认 5000（FLASK_PORT 可覆盖）
- 代理：开发态通过 Vite 将 `/api` 代理到后端；生产态前端 Nginx 将 `/api` 反代到后端容器
- 主机：为避免某些环境 `localhost` 解析为 `::1` 导致连接异常，开发建议统一使用 `127.0.0.1`

### 实时通道（SSE 优先）与排障
- 实时端点：`/api/v1/events/`（Server‑Sent Events）
- Vite 代理已关闭 SSE 的 `content-length` 干扰；Nginx 配置已 `proxy_buffering off`
- 常见问题：
  - CORS 阻断：生产设置 `CORS_ORIGINS`（逗号分隔），开发自动放行 127.0.0.1:前端端口
  - 308 POST 重定向：对部分 POST 端点使用结尾斜杠（例如 `experiments/`）
  - `/errors` 404：错误上报为可选功能，404 可忽略（已静默）

### 连通性自检脚本
- 运行：
```
cd frontend
npm run check:connect
```
- 可选变量（默认已与 Vite 对齐）：
```
VITE_FRONTEND_HOST=127.0.0.1 VITE_FRONTEND_PORT=3000 \
VITE_BACKEND_HOST=127.0.0.1 VITE_BACKEND_PORT=5000 \
node ./test-connectivity.js
```

## 常用接口（节选）

### 自定义数据集格式与路径（后端 DatasetFactory）
- 后端通过 DatasetFactory 自动检测 TUM/KITTI；自定义类型建议对齐以下结构：
  - TUM 单序列目录可包含以下之一：`rgb/` 或 `images/`（可选 `depth/`）、或 `rgb.txt`（可选 `depth.txt`、`groundtruth.txt`）。
  - 支持两级嵌套：`path/seq1/seq2/rgb`。
  - KITTI 目录包含 `sequences/00,01,...`，每个序列含 `image_0/` 或 `image_2/`。
- Dataset 接口需实现：
  - `get_calibration(sequence) -> np.ndarray(3x3)`
  - `get_frame_count(sequence) -> int`
  - `get_image(sequence, frame_id) -> np.ndarray`
  - `get_ground_truth_pose(sequence, frame_id) -> Optional[Pose]`
  - `get_timestamp(sequence, frame_id) -> Optional[float]`
  - `sequences`（属性或方法）返回可用序列列表

### Windows 路径与数据集扫描指引
- 可通过环境变量 `DATASET_PATHS` 覆盖/追加扫描目录（支持 `;` 或 `:` 分隔）：
  ```powershell
  $env:DATASET_PATHS = "C:\\Datasets\\TUM_RGBD;D:\\TUM;C:\\Datasets\\TUM_RGBD\\rgbd_dataset_freiburg1_xyz"
  ```
  - 可同时填写“数据集根目录”（包含多个序列）与“单个序列目录”（例如 `rgbd_dataset_freiburg1_xyz`）。
  - 工厂容忍多种 TUM 变体结构：`rgb/`、`rgb_png/`、`images/`；`depth/`、`depth_png/`；仅 `rgb.txt`/`depth.txt`；二级嵌套 `path/seq/seq/rgb`；`groundtruth.txt` 在上层目录等。


- 实验：`GET/POST /api/v1/experiments/`、`GET /api/v1/experiments/<id>`
- 结果：`GET /api/v1/results/<experiment_id>/<algorithm_key>`
- PR 曲线：当无数据时，后端返回空数组（precisions/recalls/thresholds均为空）、`auc_score=0`、`has_data=false`，前端显示“暂无PR曲线数据”提示，不绘制示例折线。
- 轨迹：当无地面真值（GT）时，默认不返回参考直线；仅当请求参数 `include_reference=true` 时，返回基于时间的参考直线用于可视化对比，且在 `metadata` 中标注 `has_groundtruth=false`、`reference_groundtruth=true`。

- 健康：`GET /api/v1/health`、文档：`GET /api/v1/docs/`

## 部署要点（SSE/CORS/安全）

- 后端 CORS 与安全
  - 生产务必设置环境变量：
    - `SECRET_KEY`（必须）
    - `CORS_ORIGINS`（以逗号分隔的允许来源列表）
  - 建议 `LOG_TO_STDOUT=true` 以便容器日志聚合

- 反向代理（Nginx）开启 SSE 支持
  - 为 `/api/` 关闭缓冲并延长超时：

```
location /api/ {
  proxy_pass http://backend:5000;
  proxy_set_header Host $host;
  proxy_set_header X-Real-IP $remote_addr;
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_set_header X-Forwarded-Proto $scheme;
  proxy_buffering off;
  proxy_read_timeout 3600s;
  proxy_send_timeout 3600s;
}
```

- 前端 API Base URL
  - API 客户端使用运行时配置（`configManager`）的 `api.baseUrl`，默认回退为 `/api/v1`。
  - 开发环境下 Vite 代理 `/api` → 后端；可通过 `VITE_BACKEND_HOST/PORT` 定制。

## 已知事项与路线图
- **WebSocket 实现**: 暂未在后端实现，前端仅在 `isConnected===true` 且收到消息时处理更新，否则自动回退轮询。计划在下一版本实现。
- **数据集扩展**: 支持通过 DatasetFactory 自动检测 TUM/KITTI；扩展其他类型时请实现 Dataset 接口并在工厂中注册。
- **依赖管理**: 已清理重复依赖，统一端口配置，完善 Docker 构建流程。
- **健康检查**: 已增强依赖检查，包含 OpenCV、NumPy、SQLAlchemy 可用性验证。

## 许可证
MIT（详见根目录 LICENSE）

## 仓库
GitHub：`https://github.com/Eve6uumlyn4n0Reeves/vo_benchmark`