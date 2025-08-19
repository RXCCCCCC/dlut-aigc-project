# 3D模型生成应用

这是一个基于AI的3D模型生成应用，用户可以通过输入文字描述或上传图片来生成对应的3D模型。

## 项目概述

本项目采用前后端分离架构，前端使用Vue 3 + Vite + three.js构建，后端使用Python Flask框架，并集成腾讯云AI3D(hunyuan-to-3d)服务来生成3D模型。

### 技术栈

- 前端: Vue 3 + Vite + three.js
- 后端: Python Flask
- 云服务: 腾讯云AI3D(hunyuan-to-3d)服务

## 项目结构

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
- Python 3.7+
- 腾讯云账号及API密钥

### 前端环境
- Node.js 16+
- npm 或 yarn

## 安装与配置

### 后端配置

1. 创建Python虚拟环境:
   ```bash
   cd backend
   python -m venv venv
   ```

2. 激活虚拟环境:
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

3. 安装依赖:
   ```bash
   pip install flask flask-cors requests python-dotenv tencentcloud-sdk-python
   ```

4. 配置腾讯云API密钥:
   在[backend/.env](file:///e:/practice/dut-aigc-project/backend/.env)文件中配置您的腾讯云密钥:
   ```
   TENCENT_SECRET_ID=your_secret_id
   TENCENT_SECRET_KEY=your_secret_key
   ```

### 前端配置

1. 安装依赖:
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
   # macOS/Linux
   # source venv/bin/activate
   ```

2. 启动Flask服务:
   ```bash
   python app.py
   ```
   后端服务将运行在 `http://localhost:5000`

### 启动前端开发服务器

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