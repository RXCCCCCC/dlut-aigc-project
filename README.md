# 3D模型创造器! - 智享生活赛题项目

## 赛题选择

本项目选择参赛赛题为：**智享生活**

## 项目创意

### 解决的实际问题
在当前数字化时代，3D模型在各个领域都有广泛应用，包括电商展示、游戏开发、室内设计、教育演示等。然而，传统3D建模需要专业技能和大量时间，普通用户难以快速创建所需的3D模型。本项目旨在解决这一问题，让普通用户也能轻松生成高质量的3D模型。

### 创意来源
项目灵感来源于AI生成技术的快速发展，特别是多模态AI在文本到图像、图像到3D等任务上的突破。我们希望利用这些先进技术，打造一个简单易用的3D模型生成平台，让用户通过简单的文字描述或图片上传就能获得精美的3D模型。

### 目标用户
- 电商平台商家：快速生成商品3D展示模型
- 教育工作者：创建教学用的3D模型
- 内容创作者：为视频、文章配图制作3D素材
- 游戏开发者：快速原型设计
- 普通用户：制作个性化3D模型

## 已实现功能

### 核心功能
1. **文本生成3D模型**：用户输入文字描述，系统自动生成相应的3D模型
2. **图片生成3D模型**：用户上传图片，系统根据图片内容生成3D模型
3. **3D模型预览**：在浏览器中实时交互式预览生成的3D模型
4. **模型下载**：支持下载生成的GLB格式3D模型文件

### 技术特色
1. **AI文本增强**：使用DeepSeek-R1模型对用户输入的简单描述进行增强，生成更适合3D建模的详细描述
2. **多模态AI支持**：集成腾讯云混元AI的文生3D和图生3D能力
3. **实时3D渲染**：基于Three.js实现浏览器端的3D模型实时渲染和交互
4. **语音输入支持**：提供语音识别功能，方便用户通过语音输入文本描述

### 用户体验优化
1. **直观的UI界面**：简洁美观的用户界面，操作流程清晰
2. **拖拽上传**：支持文件拖拽上传，提升操作便捷性
3. **实时反馈**：提供加载状态提示和错误信息反馈
4. **响应式设计**：适配不同屏幕尺寸的设备

## 运行与部署指南

### 项目结构

```
dut-aigc-project/
├── backend/           # 后端代码
│   ├── app.py         # Flask应用主文件
│   ├── .env           # 环境变量配置文件
│   ├── .gitignore     # Git忽略文件配置
│   └── venv/          # Python虚拟环境
└── frontend/          # 前端代码
    ├── src/           # 源代码目录
    │   ├── components/
    │   │   └── GeneratorInput.vue  # 主要组件
    │   ├── App.vue    # 应用根组件
    │   └── main.js    # 应用入口文件
    ├── vite.config.js # Vite配置文件
    ├── package.json   # 项目依赖配置
    └── .gitignore     # Git忽略文件配置
```

## 功能特性

1. 文字描述生成3D模型
2. 图片参考生成3D模型
3. 3D模型在线预览（支持旋转、缩放）
4. 3D模型下载（GLB格式）

## 环境要求

### 后端环境
- Python 3.12.3
- 腾讯云账号及API密钥

### 前端环境
- Node.js 22.13.0
- npm 11.5.2

## 安装与配置

### 后端配置

1. 创建并激活 Python 虚拟环境：
   ```bash
   cd backend
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux
   source venv/bin/activate
   ```

2. 安装依赖：
   ```bash
   cd backend
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. 配置 API 密钥：
   创建并在 backend/.env 文件中填写：
   ```
   # 腾讯云混元AI密钥
   TENCENT_SECRET_ID=your_secret_id
   TENCENT_SECRET_KEY=your_secret_key

   # 硅基流动 deepseek-r1 API 密钥
   SILICONFLOW_API_KEY=your_siliconflow_api_key
   ```

   **如何获得腾讯云 API 密钥（SecretId 和 SecretKey）：**
   1. 登录 [腾讯云控制台](https://console.cloud.tencent.com/)。
   2. 点击右上角头像，选择“访问管理” > “访问密钥”。
   3. 在“API密钥管理”页面，点击“新建密钥”或查看已有密钥。
   4. 复制 SecretId 和 SecretKey，分别填入 .env 文件。

   其中 SILICONFLOW_API_KEY 为你在硅基流动平台注册获得的 API Key，用于调用 deepseek-r1 文本增强服务。

### 前端配置
安装依赖：
   ```bash
   cd frontend
   npm install
   ```

## 运行项目

### 启动后端服务

1. 进入后端目录并激活虚拟环境:
   ```bash
   cd backend
   # Windows
   venv\Scripts\activate
   # Linux
   # source venv/bin/activate
   ```

2. 启动Flask服务:
   ```bash
   python app.py
   ```
   后端服务将运行在 `http://localhost:5000`

### 启动前端开发服务器(重新打开一个终端窗口，注意请勿关闭此前已经启动的后端服务)

1. 进入前端目录:
   ```bash
   cd frontend
   ```

2. 启动开发服务器:
   ```bash
   npm run dev
   ```
   前端服务将运行在 `http://localhost:5173`

## 使用说明

1. 打开浏览器访问 `http://localhost:5173`
2. 在输入框中输入您想要生成的3D模型描述，例如："一个漂浮在云端的魔法图书馆"
3. （可选）上传参考图片
4. 点击"开始生成！"按钮
5. 等待AI生成3D模型（可能需要几分钟时间）
6. 生成完成后可在线预览3D模型，支持旋转、缩放操作
7. 点击"下载3D模型"按钮可下载GLB格式的3D模型文件

## API接口

### 生成3D模型
- URL: `/api/generate`
- 方法: POST
- 参数:
  - text: 文字描述（可选）
  - image: 参考图片（可选）
- 返回:
  - status: 状态（success/error）
  - message: 消息描述
  - modelUrl: 3D模型文件URL
  - previewImageUrl: 预览图URL

### 3D模型代理
- URL: `/api/model-proxy`
- 方法: GET
- 参数:
  - url: 真实模型文件URL
- 说明: 用于代理腾讯云模型文件，解决跨域问题

## 安全注意事项

- 请妥善保管您的腾讯云API密钥，不要将其提交到代码仓库中
- [.env](file:///e:/practice/dut-aigc-project/backend/.env)文件已被添加到[.gitignore](file:///e:/practice/dut-aigc-project/frontend/.gitignore)中，避免意外提交

## 项目规范

- 前后端分离架构
- RESTful API设计
- 环境变量配置管理
- Git版本控制

## 可能的问题及解决方案

1. 如果遇到跨域问题，请检查前端[vite.config.js](file:///e:/practice/dut-aigc-project/frontend/vite.config.js)中的代理配置
2. 如果3D模型无法加载，请检查后端代理服务是否正常运行
3. 如果生成失败，请检查腾讯云API密钥配置是否正确