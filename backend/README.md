# VO-Benchmark Backend

视觉里程计基准测试系统的后端服务，基于 Flask + RestX 构建。

## 快速开始（Windows）

### 环境要求
- Python 3.8+
- Windows 10/11 或 WSL

### 安装与启动

1. **创建虚拟环境**（推荐）
   ```powershell
   cd backend
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

2. **安装依赖**
   ```powershell
   pip install -r requirements.txt
   ```

3. **启动开发服务器**
   ```powershell
   python start_server.py
   ```

4. **验证服务**
   - 健康检查：http://127.0.0.1:5000/api/v1/health-doc/
   - API 文档：http://127.0.0.1:5000/api/v1/docs/

## 生产环境配置

### 环境变量
```bash
# 必需配置
FLASK_ENV=production
CORS_ORIGINS=https://yourdomain.com,https://api.yourdomain.com

# 可选配置
LOG_LEVEL=INFO
LOG_TO_STDOUT=true
BACKEND_PORT=5000
```

### CORS 安全
⚠️ **重要**：默认配置允许所有来源（`*`），生产环境必须设置具体域名：
```bash
export CORS_ORIGINS="https://yourdomain.com,https://api.yourdomain.com"
```

### 日志配置
- 开发环境：控制台输出，DEBUG 级别
- 生产环境：建议 INFO 级别，可配置文件输出

## 文档参考

- 分模块架构说明：docs/backend-modules.md
- 接口契约文档：docs/api-contract.md
- 在线 API 文档：/api/v1/docs/

## 常见问题

### OpenCV 安装缓慢
如果 `opencv-contrib-python` 安装缓慢，可以：
1. 使用国内镜像：`pip install -i https://pypi.tuna.tsinghua.edu.cn/simple opencv-contrib-python`
2. 或暂时跳过，系统会自动降级到基础功能

### 端口冲突
默认端口 5000，如需修改：
```bash
export BACKEND_PORT=8000
python start_server.py
```

