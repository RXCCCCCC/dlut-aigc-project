#!/usr/bin/env pwsh
# 本地快速启动脚本（Windows PowerShell）

Write-Host "========================================" -ForegroundColor Green
Write-Host "DLUT AIGC 本地启动脚本" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# 检查是否在项目根目录
if (-not (Test-Path "./backend") -or -not (Test-Path "./frontend")) {
    Write-Host "错误：请在项目根目录运行此脚本" -ForegroundColor Red
    exit 1
}

# 检查 .env 文件
if (-not (Test-Path "./.env")) {
    Write-Host "提示：未找到 .env 文件" -ForegroundColor Yellow
    Write-Host "正在复制 .env.example 为 .env..." -ForegroundColor Yellow
    Copy-Item ".env.example" -Destination ".env"
    Write-Host "请编辑 .env 文件填入 API 密钥" -ForegroundColor Yellow
}

# 后端启动
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "启动后端服务..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Push-Location backend

# 创建虚拟环境（如果不存在）
if (-not (Test-Path ".venv")) {
    Write-Host "创建 Python 虚拟环境..." -ForegroundColor Yellow
    python -m venv .venv
}

# 激活虚拟环境
Write-Host "激活虚拟环境..." -ForegroundColor Yellow
& ".\.venv\Scripts\Activate.ps1"

# 安装依赖
Write-Host "安装 Python 依赖..." -ForegroundColor Yellow
pip install -q -r requirements.txt

# 启动后端
Write-Host "启动 Flask 服务（http://localhost:5000）..." -ForegroundColor Green
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Gray

Start-Process pwsh -ArgumentList '-NoExit', '-Command', {
    . .\.venv\Scripts\Activate.ps1
    python app.py
} -WorkingDirectory $pwd

Pop-Location

# 等待后端启动
Start-Sleep -Seconds 3

# 前端启动
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "启动前端开发服务..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Push-Location frontend

# 安装依赖
Write-Host "安装 Node.js 依赖..." -ForegroundColor Yellow
npm install --quiet

# 启动前端
Write-Host "启动 Vite 开发服务（http://localhost:5173）..." -ForegroundColor Green
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Gray

npm run dev

Pop-Location
