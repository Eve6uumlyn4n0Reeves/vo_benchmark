# ⚡ VO-Benchmark 快速启动

> **已配置环境用户专用 - 直接复制粘贴启动**

## 🚀 一键启动（Windows 一键脚本）

### 方式一：一键脚本（推荐）
```powershell
# 在项目根目录执行
powershell -ExecutionPolicy Bypass -File .\scripts\start_win.ps1
```

### 方式二：手动两个窗口
```cmd
:: 后端
cd <PROJECT_ROOT>\backend
python start_server.py

:: 前端
cd <PROJECT_ROOT>\frontend
npm run dev
```

### 访问应用
```
http://127.0.0.1:3000
```

---

## 🔄 重新配置环境

### 重装后端依赖
```cmd
cd <PROJECT_ROOT>\backend
venv\Scripts\activate
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 重装前端依赖
```cmd
cd <PROJECT_ROOT>\frontend
npm cache clean --force
npm install --registry=https://registry.npmmirror.com
```

---

## 🛠️ 开发命令

### 后端测试
```cmd
cd vo_benchmark\backend
venv\Scripts\activate
pytest
```

### 前端构建
```cmd
cd vo_benchmark\frontend
npm run build
```

### 前端预览
```cmd
cd vo_benchmark\frontend
npm run preview
```

---

## 📋 状态检查

### 检查服务状态
```cmd
curl http://127.0.0.1:5000/api/v1/health
curl http://127.0.0.1:3000
```

### 检查端口占用
```cmd
netstat -ano | findstr :5000
netstat -ano | findstr :3000
```

---

## 🔧 故障排除

### 清理并重启
```cmd
# 停止所有服务 (Ctrl+C)
# 清理端口
taskkill /f /im python.exe
taskkill /f /im node.exe
# 重新启动
```

### 更换端口
```cmd
# 后端使用 5001 端口
set FLASK_PORT=5001
python start_server.py

# 前端使用 3001 端口
npm run dev -- --port 3001
```
