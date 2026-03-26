#!/bin/bash

# EuroJobs 一键部署脚本

echo "=== EuroJobs Railway 部署 ==="

# 1. 初始化 git
git init
git add .
git commit -m "Initial commit: EuroJobs MVP"

echo ""
echo "=== 下一步操作 ==="
echo ""
echo "1. 在 GitHub 创建仓库: https://github.com/new"
echo "2. 推送代码:"
echo "   git remote add origin https://github.com/YOUR_USERNAME/eurojobs.git"
echo "   git push -u origin main"
echo ""
echo "3. 访问 https://railway.app 注册"
echo "4. 创建新项目，选择 GitHub 仓库"
echo "5. 添加 PostgreSQL 数据库"
echo "6. 部署后修改环境变量 DATABASE_URL"
echo ""
echo "=== 或使用以下 Railway 按钮 ==="
echo ""
echo "Deploy to Railway:"
echo "https://railway.app/new?template=https://github.com/your-repo"