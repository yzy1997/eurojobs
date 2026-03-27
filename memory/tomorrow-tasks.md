---
name: tomorrow-tasks
description: Tasks to do tomorrow for the EuroJobs project
type: project
---

# 明天任务

## 1. 重新部署 Railway 后端
- 部署最新代码（包含芬兰等 19 个国家）
- 目的：让爬虫能爬取更多国家的职位

## 2. 添加 GitHub Actions 定时爬虫
- 每天凌晨 3 点自动运行
- 需要用户准备：
  - GitHub Token（含 workflow 权限）
  - 在仓库添加 secret: RAILWAY_API_URL