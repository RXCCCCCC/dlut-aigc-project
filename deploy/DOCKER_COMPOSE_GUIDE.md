# 本地 Docker Compose 部署与测试指南

本指南帮你在本地用 Docker Compose 完整部署项目，验证所有功能正常运行后，可直接部署到阿里云服务器，效果完全一致。

## 前置条件

1. **安装 Docker & Docker Compose**
   - 下载 [Docker Desktop](https://www.docker.com/products/docker-desktop)（包含 Docker & Docker Compose）
   - Windows/Mac：直接安装 Docker Desktop
   - Linux：安装 docker.io 与 docker-compose

2. **克隆或进入项目目录**
   ```bash
   cd d:/systemDir/Documents/GitHub/dlut-aigc-project
   ```

## 第一步：准备环境变量

### 1.1 复制并编辑 .env 文件

```bash
# 在 Windows PowerShell 中
Copy-Item .env.example -Destination .env
```

### 1.2 编辑 `.env` 文件，填入真实值

打开 `.env` 文件，按以下示例填充必须的 API 密钥：

```ini
# 必须配置（否则生成功能会失败）
TENCENT_SECRET_ID=your_tencent_secret_id
TENCENT_SECRET_KEY=your_tencent_secret_key

# 可选但推荐配置文本增强
SILICONFLOW_API_KEY=your_siliconflow_api_key

# 生产安全配置
JWT_SECRET_KEY=your-strong-random-secret-key-min-32-chars

# 存储方式（默认本地，已配置）
STORAGE_PROVIDER=local
```

## 第二步：启动容器

### 2.1 使用 docker-compose 启动所有服务

```bash
# 在项目根目录运行以下命令
docker-compose up --build
```

这条命令会：
- 构建后端镜像（Python + Flask + gunicorn）
- 构建前端镜像（Node + Vite + nginx）
- 启动两个容器并挂载 SQLite 数据目录

### 2.2 查看启动日志

启动后你应该看到类似的输出：

```
dlut-aigc-backend  | [2024-12-24 10:00:00 +0000] [7] [INFO] Listening at: http://0.0.0.0:5000 (7)
dlut-aigc-backend  | [2024-12-24 10:00:00 +0000] [7] [INFO] Using worker: sync
dlut-aigc-frontend | 192.168.1.10 - - [24/Dec/2024 10:00:00] "GET / HTTP/1.1" 200 5000
```

## 第三步：本地验证

### 3.1 访问前端

打开浏览器访问：
```
http://localhost:5173
```

你应该看到：
- **登录/注册页面**（如果未登录）
- 或**主页面**（如果已登录）

### 3.2 注册新用户

1. 点击"去注册"链接进入注册页
2. 输入用户名（3-32 字符）和密码（最少 6 字符）
3. 点击"注册"按钮

**预期结果：** 注册成功后自动跳转到登录页，显示"注册成功"提示

### 3.3 登录

1. 输入刚才注册的用户名和密码
2. 点击"登录"按钮

**预期结果：** 登录成功后跳转到主页面，显示用户昵称和"生成"、"历史"导航

### 3.4 测试生成功能（需要腾讯云 API 密钥）

1. 在"生成"页面输入文本描述，例如："一个蓝色的立方体"
2. 点击"开始生成！"按钮
3. 等待 3-5 分钟（取决于腾讯云处理速度）

**预期结果：**
- 显示"正在咏唱咒语..."加载提示
- 生成完成后显示 3D 模型预览和预览图
- 可旋转、缩放 3D 模型

### 3.5 验证历史记录

1. 点击"历史"导航
2. 应该看到刚才生成的记录

**预期结果：**
- 显示生成的记录列表（包含 prompt、时间）
- 支持"删除"和"下载模型"按钮

### 3.6 验证数据库持久化

停止容器并再次启动，数据应该仍然存在：

```bash
# 停止容器（Ctrl+C）
# 重新启动
docker-compose up
```

**预期结果：** 登录后应该仍能看到之前的历史记录

## 第四步：检查容器内数据库文件

### 4.1 查看本地挂载的数据目录

在项目根目录应该有一个 `./data` 文件夹（docker-compose 自动创建），其中包含 `data.db`：

```bash
# Windows PowerShell
dir .\data
ls -l .\data\data.db
```

**预期结果：** `data.db` 文件存在且大小 > 0

### 4.2 使用 sqlite3 客户端检查表结构（可选）

```bash
# 如果本地安装了 sqlite3
sqlite3 .\data\data.db
sqlite> .tables
# 应该看到 user 和 history 表
sqlite> SELECT COUNT(*) FROM user;
sqlite> SELECT COUNT(*) FROM history;
sqlite> .quit
```

## 第五步：测试日志与错误排查

### 5.1 查看后端日志

如果生成失败，查看后端日志以诊断问题：

```bash
# 另开一个终端查看后端日志
docker-compose logs -f backend
```

常见错误与解决方案：

| 错误信息 | 原因 | 解决方案 |
|---------|------|---------|
| `腾讯云凭证未配置或无效` | `TENCENT_SECRET_ID` 或 `TENCENT_SECRET_KEY` 缺失或错误 | 检查 `.env` 文件，确保值正确填写 |
| `SiliconFlow deepseek-r1 处理失败` | `SILICONFLOW_API_KEY` 错误或网络不通 | 检查 API Key；可选项，不影响基本生成 |
| `connection refused` | 前端无法连接后端 | 检查防火墙；docker-compose 中后端暴露 5000 端口 |
| `database is locked` | SQLite 并发写入冲突 | 这是 SQLite 的已知限制；若经常发生，考虑迁移到 MySQL/Postgres |

### 5.2 查看前端日志

```bash
docker-compose logs -f frontend
```

## 第六步：清理与停止

### 6.1 停止容器但保留数据

```bash
docker-compose stop
# 下次启动时数据仍在
```

### 6.2 停止并删除容器（数据保留）

```bash
docker-compose down
# data 目录中的 data.db 仍然存在
```

### 6.3 完全清理（包括容器、镜像、数据卷）

```bash
docker-compose down -v
# 注意：这会删除 data 卷中的数据
```

## 部署到阿里云的对应步骤

一旦在本地验证无误，部署到阿里云服务器的步骤完全相同：

1. 在服务器上克隆仓库
2. 创建并编辑 `.env` 文件（同本地）
3. 运行 `docker-compose up -d`（后台模式）
4. 通过 `http://your-aliyun-ip:5173` 访问前端

**唯一差异：**
- 本地：`http://localhost:5173`
- 阿里云：`http://your-aliyun-public-ip:5173`

## 性能与可靠性建议

在本地验证完成、部署到阿里云后：

1. **SQLite 的限制**：SQLite 对并发写入不友好；若预期并发用户多，建议迁移到 MySQL/RDS
2. **备份**：定期备份 `data.db` 文件或设置自动快照
3. **监控**：使用 `docker-compose logs` 或容器监控工具实时查看服务状态
4. **负载均衡**：若需要高可用，在 ALB/SLB 后添加多个后端实例（需要改用 MySQL/Postgres）

## 完整检查清单

在你认为项目已可部署到阿里云前，请完成以下检查：

- [ ] 本地 docker-compose 成功启动所有容器
- [ ] 能访问 http://localhost:5173 前端
- [ ] 能成功注册新用户（用户信息保存到 SQLite）
- [ ] 能成功登录（JWT token 生成并保存）
- [ ] 如果有腾讯云 API，能成功生成 3D 模型
- [ ] 能看到历史记录列表
- [ ] 能删除历史记录
- [ ] 能下载模型文件
- [ ] 停止并重启容器后，历史记录仍然存在（验证数据持久化）
- [ ] 本地 `./data/data.db` 文件存在且大小 > 0

完成以上全部检查，表示你的程序已可直接部署到阿里云服务器。
