# 本地验证快速开始（不使用 Docker）

如果你的本地开发环境中安装了 Python、Node.js 和 SQLite，可以按以下步骤快速验证项目在本地正常运行。这套步骤验证成功后，直接部署到阿里云效果完全一致。

## 前置环境检查

```powershell
# 检查 Python 版本（需要 3.9+）
python --version

# 检查 Node.js 版本（需要 20+）
node --version
npm --version
```

## 第一步：后端本地验证

### 1.1 进入后端目录并创建虚拟环境

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 1.2 安装依赖

```powershell
pip install -r requirements.txt
```

### 1.3 创建 `.env` 文件（复制根目录的 `.env.example`）

```powershell
# 在 backend 目录同级（项目根目录）复制
cd ..
Copy-Item .env.example -Destination .env
```

### 1.4 编辑 `.env` 文件，填入必要的 API 密钥

打开 `.env` 文件，设置：
```ini
TENCENT_SECRET_ID=your_secret_id
TENCENT_SECRET_KEY=your_secret_key
JWT_SECRET_KEY=your-strong-random-secret
```

### 1.5 启动后端服务

```powershell
cd backend
.venv\Scripts\Activate.ps1
python app.py
```

**预期输出：**
```
 * Running on http://0.0.0.0:5000
Using database URI: sqlite:///D:\systemDir\Documents\GitHub\dlut-aigc-project\backend\data.db
```

验证项：
- [ ] 后端成功启动在 http://localhost:5000
- [ ] SQLite 数据库文件 `backend/data.db` 已创建
- [ ] 没有导入错误或连接异常

## 第二步：前端本地验证（新建终端）

### 2.1 安装前端依赖

```powershell
cd frontend
npm install
```

### 2.2 启动前端开发服务器

```powershell
npm run dev
```

**预期输出：**
```
  VITE v7.0.0  ready in 1234 ms

  ➜  Local:   http://localhost:5173/
```

验证项：
- [ ] 前端成功启动在 http://localhost:5173
- [ ] 没有构建错误

## 第三步：功能验证（浏览器中）

打开浏览器访问 `http://localhost:5173`

### 3.1 注册测试

1. 如果看到登录页，点击"去注册"
2. 输入用户名（如 `testuser`）和密码（如 `password123`）
3. 点击"注册"

**预期结果：**
- 注册成功后显示"注册成功"或自动跳转到登录页
- 查看后端日志，应该看到 `User registered` 相关信息

### 3.2 登录测试

1. 输入刚才注册的用户名和密码
2. 点击"登录"

**预期结果：**
- 登录成功后跳转到主页面（生成页）
- 看到用户名显示在顶部导航
- 检查浏览器 DevTools > Application > LocalStorage，应该看到 `access_token` 和 `username`

### 3.3 历史记录页面测试

1. 点击顶部导航的"历史"
2. 应该看到空列表或之前的记录（如果有的话）

**预期结果：**
- 历史页面正常加载
- 显示"暂无历史记录"或历史列表

### 3.4 生成功能测试（需要腾讯云 API）

如果你配置了 `TENCENT_SECRET_ID` 和 `TENCENT_SECRET_KEY`：

1. 在主页输入文本描述，例如："一个蓝色立方体"
2. 点击"开始生成！"

**预期结果：**
- 显示"正在咏唱咒语..."加载动画
- 3-5 分钟后显示生成的 3D 模型和预览图
- 生成记录应该出现在"历史"页面

如果没有配置 API 密钥，会看到错误提示（这是正常的）。

### 3.5 数据持久化测试

1. 停止后端（Ctrl+C）
2. 停止前端（Ctrl+C）
3. 重新启动后端和前端
4. 重新登录，检查历史记录是否仍然存在

**预期结果：**
- SQLite 数据库保持数据，登录后能看到之前的记录

## 第四步：数据库检查（可选）

如果你本地安装了 `sqlite3`：

```powershell
cd backend
sqlite3 data.db
sqlite> .tables
# 应该看到 user 和 history 表
sqlite> SELECT COUNT(*) FROM user;
# 应该显示注册的用户数
sqlite> SELECT * FROM user;
# 应该看到用户信息
sqlite> .quit
```

如果没有 sqlite3，可以用 DB Browser 或 VS Code SQLite 扩展打开 `backend/data.db`。

## 完整验证检查清单

在认为项目已可部署到阿里云前，请完成以下全部检查：

- [ ] 后端 Python 依赖安装无误，`python app.py` 启动成功
- [ ] 前端 Node.js 依赖安装无误，`npm run dev` 启动成功
- [ ] 浏览器可访问 http://localhost:5173
- [ ] 可成功注册新用户（用户数据保存到 SQLite）
- [ ] 可成功登录（JWT token 生成并保存到 LocalStorage）
- [ ] 登录后能看到"生成"和"历史"导航
- [ ] 如有 API 密钥，能成功生成 3D 模型
- [ ] 能查看历史记录列表
- [ ] 停止并重启后端/前端后，用户和历史数据仍存在
- [ ] `backend/data.db` 文件大小 > 0

## 常见问题与排查

### 问题 1：后端启动失败 - ModuleNotFoundError

**症状：** `ModuleNotFoundError: No module named 'flask'`

**解决：**
```powershell
# 确保已激活虚拟环境
.venv\Scripts\Activate.ps1
# 重新安装依赖
pip install -r requirements.txt
```

### 问题 2：前端无法连接后端 - 404 或 CORS 错误

**症状：** 浏览器控制台显示 `/api/...` 404 或 CORS 错误

**原因：** 后端未运行或代理配置错误

**解决：**
- 确保后端运行在 http://localhost:5000
- 检查前端 `vite.config.js` 中的代理配置是否指向 http://127.0.0.1:5000
- 刷新浏览器

### 问题 3：数据库错误 - database is locked

**症状：** 操作时显示 `database is locked`

**原因：** SQLite 不支持并发写入

**解决：** 这是 SQLite 的已知限制；若在生产有并发写入，建议迁移到 MySQL/Postgres

### 问题 4：生成失败 - 腾讯云 API 错误

**症状：** 生成时显示"模型生成失败"

**原因：** API 密钥错误或网络问题

**解决：**
- 检查 `.env` 中的 `TENCENT_SECRET_ID` 和 `TENCENT_SECRET_KEY` 是否正确
- 查看后端日志获取详细错误信息

## 部署到阿里云的对应步骤

一旦本地验证全部通过，部署到阿里云的步骤：

```bash
# 在阿里云服务器上

# 克隆仓库
git clone https://github.com/RXCCCCCC/dlut-aigc-project.git
cd dlut-aigc-project

# 使用 docker-compose（推荐）
cp .env.example .env
# 编辑 .env 填入 API 密钥
nano .env  # 或用其他编辑器
docker-compose up -d

# 或使用 systemd（适合手动部署）
# 按照 deploy/systemd/dlut-aigc.service 配置

# 验证服务运行
curl http://localhost:5000/api/auth/login  # 应该返回 400（缺少参数）
curl http://localhost:5173                  # 应该返回 HTML
```

## 总结

1. **本地验证（无 Docker）** — 按上述步骤在本地运行，验证所有功能
2. **Docker Compose 验证（可选）** — 如果本地有 Docker，按 `deploy/DOCKER_COMPOSE_GUIDE.md` 运行
3. **部署到阿里云** — 步骤完全相同，使用 docker-compose 或 systemd

成功完成本地验证后，你的代码已可安心部署到任何环境，包括阿里云服务器。
