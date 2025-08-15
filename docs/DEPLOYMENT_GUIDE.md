# VO-Benchmark 部署指南

本文档提供 VO-Benchmark 系统的完整部署指南，包括开发环境、生产环境和 Docker 容器化部署。

## 快速开始

### Docker Compose 部署（推荐）

最简单的部署方式，适用于开发和生产环境：

```bash
# 克隆仓库
git clone https://github.com/Eve6uumlyn4n0Reeves/vo_benchmark.git
cd vo_benchmark

# 启动服务
docker compose up --build -d

# 访问服务
# 前端: http://127.0.0.1:3000
# 后端: http://127.0.0.1:5000
# API 文档: http://127.0.0.1:5000/api/v1/docs/
```

### 环境变量配置

生产环境建议设置以下环境变量：

```bash
# 安全配置
export SECRET_KEY="your-secure-secret-key-here"
export CORS_ORIGINS="http://localhost:3000,https://your-domain.com"

# 存储路径
export RESULTS_ROOT="/data/results"
export DATASETS_ROOT="/data/datasets"

# 日志配置
export LOG_LEVEL="INFO"
export LOG_TO_STDOUT="true"

# 启动服务
docker compose up --build -d
```

## 本地开发环境

### 系统要求

- **后端**: Python 3.12+
- **前端**: Node.js 18+ 或 20+
- **操作系统**: Windows 10+, macOS 10.15+, Ubuntu 18.04+

### 后端开发环境

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境 (Windows)
.\.venv\Scripts\activate
# 激活虚拟环境 (Linux/macOS)
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 设置数据集路径（可选）
# Windows
$env:DATASET_PATHS="C:\Datasets\TUM_RGBD;D:\Research\TUM_RGBD"
# Linux/macOS
export DATASET_PATHS="/path/to/datasets:/another/path"

# 启动开发服务器
python start_server.py
```

### 前端开发环境

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 设置环境变量（可选）
# Windows
$env:VITE_BACKEND_HOST="127.0.0.1"
$env:VITE_BACKEND_PORT="5000"
$env:VITE_FRONTEND_PORT="3000"

# Linux/macOS
export VITE_BACKEND_HOST="127.0.0.1"
export VITE_BACKEND_PORT="5000"
export VITE_FRONTEND_PORT="3000"

# 启动开发服务器
npm run dev
```

## 生产环境部署

### 使用 Docker Compose

1. **准备环境文件**

创建 `.env` 文件：

```bash
# .env
SECRET_KEY=your-very-secure-secret-key-here
CORS_ORIGINS=https://your-domain.com,https://api.your-domain.com
RESULTS_ROOT=/data/results
DATASETS_ROOT=/data/datasets
LOG_LEVEL=INFO
LOG_TO_STDOUT=true
FLASK_ENV=production
FLASK_DEBUG=false
```

2. **启动服务**

```bash
docker compose --env-file .env up --build -d
```

3. **验证部署**

```bash
# 检查服务状态
docker compose ps

# 查看日志
docker compose logs -f

# 健康检查
curl http://localhost:5000/api/v1/health
```

### 使用 Nginx 反向代理

如果需要自定义域名和 SSL，可以在前面添加 Nginx：

```nginx
# /etc/nginx/sites-available/vo-benchmark
server {
    listen 80;
    server_name your-domain.com;
    
    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL 配置
    ssl_certificate /path/to/your/cert.pem;
    ssl_certificate_key /path/to/your/key.pem;
    
    # 前端静态文件
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # API 代理
    location /api/ {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # SSE 支持
        proxy_buffering off;
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }
}
```

## 配置管理

### 配置文件层次

配置加载顺序（后者覆盖前者）：

1. `backend/config/default.yaml` - 默认配置
2. `backend/config/{environment}.yaml` - 环境特定配置
3. 环境变量 - 运行时覆盖

### 关键配置项

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|----------|--------|------|
| 服务端口 | `FLASK_PORT` | 5000 | 后端服务端口 |
| 前端端口 | `VITE_FRONTEND_PORT` | 3000 | 前端开发端口 |
| 数据集路径 | `DATASETS_ROOT` | `./data/datasets` | 数据集存储路径 |
| 结果路径 | `RESULTS_ROOT` | `./data/results` | 实验结果路径 |
| 跨域设置 | `CORS_ORIGINS` | `http://localhost:3000` | 允许的跨域来源 |
| 日志级别 | `LOG_LEVEL` | INFO | 日志输出级别 |

## 数据管理

### 数据目录结构

```
data/
├── datasets/           # 数据集存储
│   ├── TUM_RGBD/
│   └── KITTI/
├── results/           # 实验结果
│   └── experiments/
└── tmp/              # 临时文件
```

### 数据集配置

支持多种数据集格式：

```bash
# 设置数据集搜索路径
export DATASET_PATHS="/data/datasets/TUM:/data/datasets/KITTI:/data/custom"
```

## 监控和维护

### 健康检查

系统提供多层次健康检查：

```bash
# 基础健康检查
curl http://localhost:5000/api/v1/health

# 详细健康检查
curl http://localhost:5000/api/v1/health/detailed

# 就绪检查
curl http://localhost:5000/api/v1/health/ready
```

### 日志管理

```bash
# 查看容器日志
docker compose logs -f backend
docker compose logs -f frontend

# 查看特定时间段日志
docker compose logs --since="2024-01-01T00:00:00" backend
```

### 备份和恢复

```bash
# 备份实验数据
tar -czf vo-benchmark-backup-$(date +%Y%m%d).tar.gz data/ results/

# 恢复数据
tar -xzf vo-benchmark-backup-20240101.tar.gz
```

## 故障排除

### 常见问题

1. **端口冲突**
   ```bash
   # 检查端口占用
   netstat -tulpn | grep :5000
   # 或使用不同端口
   export FLASK_PORT=5001
   ```

2. **依赖缺失**
   ```bash
   # 重新安装后端依赖
   cd backend && pip install -r requirements.txt
   # 重新安装前端依赖
   cd frontend && npm install
   ```

3. **权限问题**
   ```bash
   # 确保数据目录权限
   sudo chown -R $USER:$USER data/ results/
   ```

4. **Docker 构建失败**
   ```bash
   # 清理 Docker 缓存
   docker system prune -a
   # 重新构建
   docker compose build --no-cache
   ```

### 性能优化

1. **后端优化**
   - 调整并行作业数：`DEFAULT_PARALLEL_JOBS=8`
   - 优化特征数量：`DEFAULT_MAX_FEATURES=3000`

2. **前端优化**
   - 启用生产构建：`npm run build`
   - 使用 CDN 加速静态资源

3. **系统优化**
   - 增加内存限制：在 docker-compose.yml 中设置 `mem_limit`
   - 使用 SSD 存储提升 I/O 性能

## 安全考虑

### 生产环境安全

1. **密钥管理**
   ```bash
   # 生成安全密钥
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **网络安全**
   - 使用 HTTPS
   - 配置防火墙规则
   - 限制 CORS 来源

3. **容器安全**
   - 定期更新基础镜像
   - 使用非 root 用户运行容器
   - 扫描镜像漏洞

### 访问控制

当前版本不包含用户认证，生产环境建议：

1. 在 Nginx 层添加基础认证
2. 使用 VPN 限制访问
3. 配置 IP 白名单

## 扩展和定制

### 添加新的数据集类型

1. 实现 `Dataset` 接口
2. 在 `DatasetFactory` 中注册
3. 更新配置文件

### 添加新的算法

1. 实现特征提取器或 RANSAC 方法
2. 更新配置中的支持列表
3. 添加相应测试

### API 扩展

1. 在 `routes/` 下添加新路由
2. 定义相应的 schema
3. 更新 API 文档

## 支持和社区

- **GitHub**: https://github.com/Eve6uumlyn4n0Reeves/vo_benchmark
- **文档**: 查看 `docs/` 目录下的详细文档
- **问题报告**: 使用 GitHub Issues
- **贡献指南**: 参考 `CONTRIBUTING.md`（如果存在）

---

*最后更新: 2025-08-14*
