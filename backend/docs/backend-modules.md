# VO-Benchmark 后端分模块说明

本文件面向后端开发与测试人员，概述各模块职责、关键类/函数、依赖关系与健壮性设计。配合 API 契约文档使用。

## 顶层结构
- src/api: Web/API 层（Flask + Flask-RESTX 文档），路由、服务、模式、异常、序列化、中间件
- src/core: 核心算法（特征、匹配、RANSAC、几何）
- src/pipeline: 实验/帧级流水线（ExperimentManager, FrameProcessor）
- src/datasets: 数据集抽象与 TUM/KITTI 工厂
- src/evaluation: 指标计算（轨迹/匹配/PR 曲线 等）
- src/storage: 存储抽象与文件系统实现
- src/config: 配置加载与客户端配置导出
- src/utils: 日志、校验、性能、路径等工具

## API 层（src/api）
- app.py
  - create_app(): 应用工厂；注册中间件、蓝图、RESTX 文档；CORS、防重注册、统一错误处理
  - 健壮性：
    - 日志记录异常时降级为 debug（避免 pass 吞异常）
    - CORS 在 after_request 兜底补齐头部
- docs.py
  - 定义 RESTX api 与公共 models；增加针对第三方弃用告警的 warnings filter，不影响自有代码
- routes/
  - experiments_documented.py：带 OpenAPI 文档的实验管理端点（列表/创建/详情/取消位预留 405）
  - results.py：结果查询（概览、诊断、算法结果、帧结果、PR 曲线、轨迹、导出）——通过 Facade 按请求期创建服务，避免错误配置上下文
  - tasks.py：任务查询、取消（与 task_service 对接）
  - health_documented.py：健康检查（基础/详细/就绪），含系统指标与依赖检测
  - health.py：非 RESTX 版本健康接口（内部/兼容），UTC 时间改为 datetime.now(UTC)
  - config.py：客户端配置、算法配置、系统配置、诊断，保留 legacy 路径兼容
- services/
  - experiment.py：ExperimentService 创建/列举/获取实验；与 pipeline + storage 协作
  - result.py：ResultService 聚合读取结果、PR 曲线、轨迹、导出
  - task.py / inmemory_impl.py：任务状态管理（内存实现），Pydantic v2 优先使用 model_dump
- schemas/
  - request.py：CreateExperimentRequest 等请求模型，含字段级校验（路径合法、枚举范围等）
  - response.py：TaskResponse、Experiment*、Algorithm*、PRCurve*、Frame* 等响应模型
- middleware.py：统一错误处理与跨域、中间件注册

## 核心算法层（src/core）
- features/
  - extractor/matcher 工厂与实现（SIFT/ORB/AKAZE/BRISK/KAZE/SURF；BF/FLANN KDTree/LSH）
  - 匹配后处理：GMS（优先，失败回退到对称匹配 + MAD 鲁棒阈值）
- ransac/
  - standard.py / prosac.py：鲁棒估计，迭代数估计时对 inlier_ratio 做数值夹取，避免 log(0) 告警
  - factory.py：映射到 OpenCV 常量，USAC 可用时优先

## 流水线（src/pipeline）
- manager.py：ExperimentManager 协调数据集、特征、RANSAC、评估与存储
- frame_processor.py：逐帧处理，记录时间、内点率、内点掩码、重投影误差等真实数据

## 数据集（src/datasets）
- factory.py：按路径/配置识别并构造数据集
- tum/*, kitti/*：目录扫描与元数据解析（容忍常见变体与 Windows 路径）

## 评估（src/evaluation）
- metrics.py：轨迹/匹配等指标计算（真实几何/掩码），汇总到 AlgorithmMetrics
- pr_curve.py：基于 scores 与 inlier_mask 计算 PR/F1/AUC
- trajectory.py：estimated_pose 构建轨迹；无 GT 时不合成，必要时返回参考直线

## 存储（src/storage）
- interface.py：存储接口定义
- filesystem.py：文件系统实现（原子写、压缩、备份、并发锁）
- experiment.py：ExperimentStorage 读写高层实体（支持逐帧/批量帧布局兼容）

## 配置（src/config）
- manager.py：default.yaml + <env>.yaml + 环境变量合并；路径标准化为绝对路径；客户端配置动态过滤不可用算法

## 工具（src/utils）
- logging.py：结构化日志；异常链路记录
- validation.py：输入校验与错误抽象（VOBenchmarkException 等）
- perf.py：性能计时装饰器
- paths.py：结果/临时目录管理

## 健壮性原则与落实
- 无虚假实现：所有对外数据均源自真实算法与存储；无占位/硬编码路径
- 防御式设计：
  - 请求期创建服务，避免错误配置上下文
  - 特征与 USAC 能力动态检测，前端只展示可用项
  - RANSAC 数值稳定性处理（夹取）
  - 健康/就绪区分，依赖与系统指标全面可观测
- 一致性：UnifiedSerializer 确保 API、存储、导出字段一致
- 测试：114 个测试通过；tests/conftest.py 保证导入路径稳定

## 模块依赖关系（简图）
- routes → services → (pipeline + storage + evaluation + core + datasets)
- schemas(response/request) ←→ services/routes（双向约定）
- config → 所有层（只读）

## 版本与演进
- API_VERSION=1.0.0；保持向后兼容（保留 legacy 配置路由）
- 建议未来：引入类型检查（mypy）、风格检查（flake8/black）到 CI；可选引入 Redis 任务后端

