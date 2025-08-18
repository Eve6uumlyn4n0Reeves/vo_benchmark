# 🚀 VO-Benchmark 傻瓜式配置指南

> **一行一行复制粘贴即可完成配置**
> 适用于：Windows 10+, 无梯子环境, 零基础用户

## 📋 配置清单

- [ ] 安装 Python 3.8+
- [ ] 安装 Node.js 16+
- [ ] 配置国内镜像源
- [ ] 下载项目代码
- [ ] 配置后端环境
- [ ] 配置前端环境
- [ ] 启动服务

---

## 第一步：安装基础软件

### 1.1 下载并安装 Python
```
访问：https://www.python.org/downloads/
下载：Python 3.10+ (推荐 3.10.11)
安装时：✅ 勾选 "Add Python to PATH"
```

### 1.2 下载并安装 Node.js
```
访问：https://nodejs.org/
下载：LTS 版本 (推荐 18.17.0)
默认安装即可（会自动安装 npm）
```

### 1.3 验证安装
打开命令提示符（Win+R 输入 cmd），逐行执行：
```cmd
python --version
```
```cmd
node --version
```
```cmd
npm --version
```

---

## 第二步：配置国内镜像源

### 2.1 配置 Python pip 镜像
逐行执行：
```cmd
mkdir %APPDATA%\pip
```
```cmd
echo [global] > %APPDATA%\pip\pip.ini
```
```cmd
echo index-url = https://pypi.tuna.tsinghua.edu.cn/simple >> %APPDATA%\pip\pip.ini
```
```cmd
echo trusted-host = pypi.tuna.tsinghua.edu.cn >> %APPDATA%\pip\pip.ini
```

### 2.2 配置 npm 镜像
```cmd
npm config set registry https://registry.npmmirror.com
```

### 2.3 验证镜像配置
```cmd
pip config list
```
```cmd
npm config get registry
```

---

## 第三步：下载项目

### 3.1 下载方式一：Git（推荐）
```cmd
git clone https://github.com/Eve6uumlyn4n0Reeves/vo_benchmark.git
```
```cmd
cd <PROJECT_ROOT>  # 请替换为你本地仓库的实际路径
```

### 3.2 下载方式二：ZIP包（备用）
```
1. 访问：https://github.com/Eve6uumlyn4n0Reeves/vo_benchmark
2. 点击绿色 "Code" 按钮
3. 选择 "Download ZIP"
4. 解压到任意目录
5. 在解压目录打开命令提示符
```

---

## 第四步：配置后端环境

### 4.1 进入后端目录
```cmd
cd <PROJECT_ROOT>\backend
```

### 4.2（可选）创建虚拟环境
```cmd
python -m venv venv
```

### 4.3（可选）激活虚拟环境
```cmd
venv\Scripts\activate
```
> 成功后命令行前面会显示 `(venv)`

### 4.4 升级 pip
```cmd
python -m pip install --upgrade pip
```

### 4.5 安装后端依赖
```cmd
pip install -r requirements.txt
```

### 4.6 验证后端安装
```cmd
python -c "import flask; print('Flask 安装成功')"
```
```cmd
python -c "import cv2; print('OpenCV 安装成功')"
```

---

## 第五步：配置前端环境

### 5.1 进入前端目录（新开命令提示符）
```cmd
cd <PROJECT_ROOT>\frontend
```

### 5.2 清理缓存（可选）
```cmd
npm cache clean --force
```

### 5.3 安装前端依赖
```cmd
npm install
```

### 5.4 验证前端安装
```cmd
npm list react
```

---

## 第六步：启动服务

### 6.1 启动后端（第一个命令提示符窗口）
确保在 `vo_benchmark\backend` 目录下：
```cmd
（可选）venv\Scripts\activate  # 你也可以直接使用全局 Python 环境
```
```cmd
python start_server.py
```
> 看到 "Running on http://127.0.0.1:5000" 表示成功

### 6.2 启动前端（第二个命令提示符窗口）
确保在 `vo_benchmark\frontend` 目录下：
```cmd
npm run dev
```
> 看到 "Local: http://127.0.0.1:3000" 表示成功


### 6.3 一键连通性与端到端验证（可选强烈建议）
在前端目录运行下列命令进行自动化健康检查与端到端连通性验证：

```cmd
cd <PROJECT_ROOT>\frontend
npm run check:connect
npx playwright install --with-deps
npm run e2e
```

- check:connect 会检查：/api/v1/health-doc/、/api/v1/health-doc/detailed、/api/v1/config/client、/api/v1/events/（3s内是否有数据）
- e2e 会自动拉起 dev server，验证健康页、SSE 心跳（20s 内）以及 Arrow 解析（不依赖外部 CDN）

---

## 第七步：访问应用

### 7.1 打开浏览器访问
```
前端界面：http://127.0.0.1:3000
后端API：http://127.0.0.1:5000
健康检查：http://127.0.0.1:5000/api/v1/health-doc/
API文档：http://127.0.0.1:5000/api/v1/docs/
```

### 7.2 验证实时通信（SSE）
系统使用 Server-Sent Events 进行实时通信：
- 任务进度更新会自动推送到前端
- 如果网络断开，前端会自动重连
- 可在浏览器开发者工具的 Network 面板查看 `/api/v1/events/` 连接

---

## 🔧 常见问题解决

### 问题1：pip 安装很慢
```cmd
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题2：npm 安装失败
```cmd
npm install --registry=https://registry.npmmirror.com
```

### 问题3（可选）：Python 虚拟环境激活失败
```cmd
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
然后重新执行：
```cmd
venv\Scripts\activate
```

### 问题4：端口被占用
后端换端口：
```cmd
set FLASK_PORT=5001
python start_server.py
```

前端换端口：
```cmd
npm run dev -- --port 3001
```

### 问题5：OpenCV 安装失败
```cmd
pip install opencv-python-headless -i https://pypi.tuna.tsinghua.edu.cn/simple
```


### 问题6：GMS 日志刷屏（xfeatures2d.matchGMS 缺失）
如果后端日志不断出现：
```
GMS not available or failed: module 'cv2.xfeatures2d' has no attribute 'matchGMS'. Falling back to symmetric+MAD filter.
```
说明当前 OpenCV 不支持 GMS（需要 contrib 版）。解决有两种方式：

A) 最安静的方式（不需要安装任何东西）
- 关闭匹配后处理（不再尝试 GMS，也不会有相关日志）
  1. 打开 backend/config/default.yaml
  2. 修改：
     ```yaml
     experiment:
       post_filter:
         enabled: false
     ```
  3. 重启后端

B) 安装支持 GMS 的 OpenCV-Contrib（可选）
- 在后端虚拟环境中执行：
  ```cmd
  pip uninstall -y opencv-python opencv-contrib-python
  pip install opencv-contrib-python==4.8.0.76 -i https://pypi.tuna.tsinghua.edu.cn/simple
  ```
- 验证：
  ```cmd
  python -c "import cv2; print(hasattr(cv2,'xfeatures2d') and hasattr(cv2.xfeatures2d,'matchGMS'))"
  ```
  输出 True 表示可用。

注意：我们已在代码中优化，缺少 GMS 时只会提示一次并自动回退到更稳健的对称+MAD 过滤，不会再刷屏。


### 问题8：PR 曲线返回 500 或空白
- 现算需要 scikit-learn，执行：
```cmd
cd backend
pip install -r requirements.txt
```
- 仍失败：查看响应体 error 字段是否包含 "requires scikit-learn"；或前端暂时隐藏现算入口

### 问题9：多进程 SSE 不工作
- 启用 Redis 模式：
```cmd
set EVENT_BUS=redis
set REDIS_URL=redis://localhost:6379/0
cd backend && pip install -r requirements.txt
```
- 确认前端 SSE 指向 /api/v1/events/，Nginx 对该路由关闭缓冲与压缩

### 问题7：生产环境部署
如需部署到生产环境，需要额外配置：


D) 生产 Nginx 配置（SSE 专用配置，确保实时）

在前端 Nginx 配置中为 SSE 端点增加专用 location（已在仓库的 frontend/nginx.conf 中示例化）：

```
location /api/v1/events/ {
  proxy_pass http://backend:5000;
  proxy_buffering off;
  gzip off;
  proxy_set_header X-Accel-Buffering no;
  proxy_read_timeout 3600s;
  proxy_send_timeout 3600s;
}
```

说明：仅针对 SSE 路由关闭缓冲与压缩，避免影响其他 API 的性能与缓存策略。

A) 后端生产配置
```cmd
set FLASK_ENV=production
set CORS_ORIGINS=https://yourdomain.com,https://api.yourdomain.com
set LOG_LEVEL=INFO
python start_server.py
```

B) 前端构建
```cmd
cd <PROJECT_ROOT>\frontend
npm run build
```
构建产物在 `frontend/dist/` 目录，可部署到 Nginx 等 Web 服务器。

C) 安全注意事项
- ⚠️ 默认 CORS 配置允许所有来源，生产环境必须设置具体域名
- 建议使用反向代理（Nginx）处理 HTTPS 和静态文件
- 配置防火墙只开放必要端口

---

### 附：任务数据结构对齐说明（前端已适配）
- 任务进度 progress：后端返回 0.0~1.0 浮点数；前端以百分比显示（乘以 100），例如 0.42 -> 42%
- 步骤 current_step：后端可能返回整数或字符串；前端已兼容 number | string 两种类型
- 位置说明：
  - 任务列表与详情的进度条组件已统一进行百分比展示
  - 不需要修改后端返回格式；前端负责显示换算


## 📝 快速验证脚本

创建 `check.py` 文件，内容如下：
```python
import sys
import subprocess

def check(cmd, name):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✅ {name}: {result.stdout.strip()}")
    except:
        print(f"❌ {name}: 未安装")

check([sys.executable, "--version"], "Python")
check(["node", "--version"], "Node.js")
check(["npm", "--version"], "npm")
```

运行验证：
```cmd
python check.py
```

---

## 🎯 一键重启命令

### 重启后端
```cmd
cd vo_benchmark\backend
venv\Scripts\activate
python start_server.py
```

### 重启前端
```cmd
cd vo_benchmark\frontend
npm run dev
```

---

## 📞 技术支持

如果遇到问题，请提供以下信息：
1. 操作系统版本
2. Python 版本 (`python --version`)
3. Node.js 版本 (`node --version`)
4. 错误信息截图

**配置完成后，您就可以开始使用 VO-Benchmark 进行视觉里程计算法评测了！** 🎉
