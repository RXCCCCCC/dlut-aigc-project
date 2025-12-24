# 本地验证完整步骤（一步一步）

本指南提供最清晰的逐步验证流程，确保你能快速在本地验证项目的所有功能都正常运行。

---

## 📋 前置环境检查

在开始前，请确保已安装：

```powershell
# 检查 Python（需要 3.9+）
python --version

# 检查 Node.js（需要 20+）
node --version
npm --version
```

如果任何一个命令返回"不认识"，请先安装对应工具再继续。

---

## 🚀 方式一：使用快速启动脚本（推荐）

### 步骤 1：打开 PowerShell

在项目根目录打开 Windows PowerShell，或使用 VS Code 的终端。

### 步骤 2：运行启动脚本

```powershell
.\start.ps1
```

脚本会自动执行以下动作：
- 创建 Python 虚拟环境
- 安装后端依赖
- 启动后端服务（端口 5000）
- 安装前端依赖
- 启动前端开发服务（端口 5173）

### 步骤 3：等待启动完成

你应该看到两个终端窗口分别显示：

**后端终端输出：**
```
Using database URI: sqlite:///D:\...\backend\data.db
 * Running on http://0.0.0.0:5000
 * WARNING: This is a development server. Do not use it in production.
```

**前端终端输出：**
```
VITE v7.0.0  ready in 1234 ms

➜  Local:   http://localhost:5173/
➜  press h to show help
```

### 步骤 4：打开浏览器

访问 `http://localhost:5173`，你应该看到登录/注册页面。

---

## 🔧 方式二：手动逐步启动（如脚本有问题）

### 第一部分：启动后端

#### 步骤 1：打开第一个 PowerShell 终端

```powershell
cd d:/systemDir/Documents/GitHub/dlut-aigc-project
```

#### 步骤 2：创建 Python 虚拟环境

```powershell
python -m venv venv
```

这会在当前目录创建一个 `venv` 文件夹。

#### 步骤 3：激活虚拟环境

```powershell
venv\Scripts\Activate.ps1
```

成功后，终端左侧应该显示 `(venv)`。

#### 步骤 4：安装后端依赖

```powershell
cd backend
pip install -r requirements.txt
```

这会安装 Flask、SQLAlchemy、JWT 等所有依赖（需要 1-2 分钟）。

#### 步骤 5：创建 .env 文件

```powershell
cd ..
Copy-Item .env.example -Destination .env
```

#### 步骤 6：编辑 .env 文件

用任何文本编辑器打开 `.env`，修改以下内容：

```ini
# 必须配置（否则生成功能会失败）
TENCENT_SECRET_ID=your_tencent_secret_id
TENCENT_SECRET_KEY=your_tencent_secret_key

# 可选但推荐
SILICONFLOW_API_KEY=your_siliconflow_api_key

# 生产安全
JWT_SECRET_KEY=my-strong-random-secret-key-12345678
```

如果你没有腾讯云 API 密钥，可以暂时留空（后端会启动，但生成功能会失败，这是正常的）。

#### 步骤 7：启动后端服务

```powershell
cd backend
python app.py
```

**预期输出：**
```
Using database URI: sqlite:///D:\systemDir\Documents\GitHub\dlut-aigc-project\backend\data.db
 * Running on http://0.0.0.0:5000
 * WARNING: This is a development server. Do not use it in production.
```

**验证点：**
- ✅ 后端服务在 http://localhost:5000 运行
- ✅ 数据库文件已创建在 `backend/data.db`
- ✅ 没有导入错误或异常

---

### 第二部分：启动前端（新建终端）

#### 步骤 8：打开第二个 PowerShell 终端

在 VS Code 或新 PowerShell 窗口中，进入项目根目录：

```powershell
cd d:/systemDir/Documents/GitHub/dlut-aigc-project
cd frontend
```

#### 步骤 9：安装前端依赖

```powershell
npm install
```

这会安装 Vue、Vite、axios、vue-router 等依赖（需要 1-2 分钟）。

#### 步骤 10：启动前端开发服务器

```powershell
npm run dev
```

**预期输出：**
```
VITE v7.0.0  ready in 1234 ms

➜  Local:   http://localhost:5173/
➜  press h to show help
```

**验证点：**
- ✅ 前端服务在 http://localhost:5173 运行
- ✅ 没有构建错误

---

## ✅ 第三部分：功能验证（浏览器）

现在打开浏览器访问 `http://localhost:5173`。

### 验证 1：看到登录/注册页面

**预期：** 页面显示"登录"和"去注册"链接

如果看不到，检查：
- [ ] 后端终端是否显示正在运行
- [ ] 前端终端是否显示正在运行
- [ ] 浏览器是否访问了正确的 URL（http://localhost:5173，不是 http://localhost:5000）

### 验证 2：注册新用户

1. 点击"去注册"链接
2. 输入用户名，例如：`testuser`
3. 输入密码，例如：`password123`
4. 点击"注册"按钮

**预期结果：** 
- 弹出成功提示或自动跳转到登录页
- 后端终端显示注册日志

**检查后端日志：** 在后端终端应该看到类似：
```
接收到新的生成请求！
```

### 验证 3：登录

1. 输入刚才注册的用户名 `testuser` 和密码 `password123`
2. 点击"登录"按钮

**预期结果：**
- 登录成功后跳转到主页面（生成页）
- 顶部导航显示用户名
- 可看到"生成"和"历史"导航

**检查浏览器存储：**
- 打开浏览器 DevTools（F12）
- 选择 Application → LocalStorage → http://localhost:5173
- 应该看到 `access_token` 和 `username` 两个字段

### 验证 4：查看历史记录页面

1. 点击顶部导航的"历史"
2. 应该看到空列表或"暂无历史记录"

**预期结果：** 页面正常加载，没有错误

### 验证 5：生成 3D 模型（需要 API 密钥）

如果你在 `.env` 中配置了腾讯云 API 密钥：

1. 回到"生成"页面
2. 在文本框输入描述，例如：`一个蓝色的立方体`
3. 点击"开始生成！"按钮

**预期结果（3-5 分钟后）：**
- 显示 3D 模型预览
- 显示 2D 预览图
- 生成记录出现在"历史"页面中

**如果没有 API 密钥：**
- 会看到错误提示"腾讯云凭证未配置"
- 这是正常的，表示后端正在尝试调用 API

### 验证 6：删除历史记录

1. 进入"历史"页面
2. 点击某条记录右侧的"删除"按钮

**预期结果：** 记录被删除，列表更新

### 验证 7：数据持久化

1. 回到登录页：点击"登出"或关闭浏览器
2. 停止后端：在后端终端按 Ctrl+C
3. 停止前端：在前端终端按 Ctrl+C
4. 重新启动后端和前端（按第一部分步骤 7 和 10）
5. 再次打开浏览器访问 http://localhost:5173
6. 用相同的用户名和密码登录

**预期结果：** 
- 用户信息仍然存在（可以用同一用户名密码登录）
- 历史记录仍然存在
- `backend/data.db` 文件仍在

这证明 SQLite 数据库正确保存了数据。

---

## 📊 完整验证检查清单

在认为项目已可部署到阿里云前，请完成以下全部检查：

```
后端启动与依赖
- [ ] Python 依赖安装无误
- [ ] 虚拟环境激活成功
- [ ] 后端启动无错误信息
- [ ] 可访问 http://localhost:5000

前端启动与依赖
- [ ] Node.js 依赖安装无误
- [ ] 前端启动无编译错误
- [ ] 可访问 http://localhost:5173

功能验证
- [ ] 能访问登录/注册页面
- [ ] 能成功注册新用户
- [ ] 用户数据保存到 SQLite
- [ ] 能成功登录
- [ ] JWT token 保存到 LocalStorage
- [ ] 登录后显示用户名和导航
- [ ] 能访问"历史"页面
- [ ] 历史页面正常加载（空或有记录）

生成功能（如有 API 密钥）
- [ ] 能成功生成 3D 模型
- [ ] 生成记录出现在历史
- [ ] 能看到 3D 模型预览
- [ ] 能看到 2D 预览图

历史管理功能
- [ ] 历史列表显示正确
- [ ] 能删除历史记录
- [ ] 能下载模型文件

数据持久化
- [ ] 停止并重启后，用户仍能登录
- [ ] 历史记录在重启后仍存在
- [ ] backend/data.db 文件大小 > 0
```

---

## 🐛 常见问题快速排查

### 问题 1：后端无法启动 - "ModuleNotFoundError: No module named 'flask'"

**解决：**
```powershell
# 确保虚拟环境已激活（看到 (venv) 前缀）
venv\Scripts\Activate.ps1
# 重新安装依赖
cd backend
pip install -r requirements.txt
```

### 问题 2：前端无法访问后端 - "/api/... 404" 或 "CORS 错误"

**解决：**
- 确保后端运行在 http://localhost:5000
- 检查后端是否有错误日志
- 清除浏览器缓存（Ctrl+Shift+Delete）
- 刷新页面（Ctrl+F5）

### 问题 3：注册失败 - "username already exists"

**原因：** 用户名已存在

**解决：** 用不同的用户名注册，例如 `testuser2`

### 问题 4：生成失败 - "腾讯云凭证未配置或无效"

**原因：** API 密钥缺失或错误

**解决：**
- 检查 `.env` 中的 `TENCENT_SECRET_ID` 和 `TENCENT_SECRET_KEY` 是否正确
- 若没有 API 密钥，可跳过此功能测试

### 问题 5：后端或前端已在占用端口

**症状：** "Address already in use" 或 "port 5000 already in use"

**解决：**
```powershell
# 杀死占用端口的进程
netstat -ano | findstr :5000  # 查看占用 5000 端口的进程
taskkill /PID <PID> /F        # 杀死该进程
```

---

## 📈 下一步

验证成功后，你已可部署到阿里云。选择以下方式之一：

### 方式 A：使用 Docker Compose（推荐）
```bash
# 在阿里云服务器上
git clone https://github.com/RXCCCCCC/dlut-aigc-project.git
cd dlut-aigc-project
cp .env.example .env
# 编辑 .env
docker-compose up -d
```

### 方式 B：使用 systemd（手动部署）
按 `deploy/systemd/dlut-aigc.service` 示例配置。

### 方式 C：手动启动（简单但不推荐生产）
按本指南步骤在阿里云服务器上执行。

---

## 💡 总结

| 步骤 | 命令/动作 | 预期结果 |
|------|---------|--------|
| 1 | `.\start.ps1` | 后端 + 前端自动启动 |
| 2 | 访问 http://localhost:5173 | 看到登录页 |
| 3 | 注册用户 | 用户保存到数据库 |
| 4 | 登录 | token 保存到 LocalStorage |
| 5 | 生成模型（可选） | 模型与记录保存 |
| 6 | 停止并重启 | 数据持久化 |

**完成以上全部验证后，你的代码已可安心部署到阿里云或任何生产环境！**
