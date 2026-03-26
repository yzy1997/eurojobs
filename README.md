# EuroJobs - 欧洲招聘平台

高端简洁的欧洲招聘信息整合网站。

## 项目结构

```
eurojobs/
├── frontend/          # Next.js 前端
│   ├── app/          # App Router 页面
│   ├── components/   # React 组件
│   └── lib/          # 工具函数
│
└── backend/           # Python FastAPI 后端
    ├── scrapers/     # 爬虫模块
    ├── main.py       # API 服务
    └── init.sql      # 数据库初始化
```

## 快速开始

### 前端

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:3000

### 后端

```bash
cd backend
pip install -r requirements.txt

# 初始化数据库
psql -U postgres -d eurojobs -f init.sql

# 启动服务
uvicorn main:app --reload --port 8000
```

## 一键部署

### Railway (推荐)

1. 注册 [Railway.app](https://railway.app)
2. 创建新项目，连接 GitHub
3. 添加 PostgreSQL 数据库
4. 部署 Python 服务

### Vercel (前端)

1. 注册 [Vercel](https://vercel.com)
2. 导入 GitHub 项目
3. 部署完成！

## 功能

- [x] 多平台爬虫聚合 (Indeed, LinkedIn)
- [x] 按国家/类别筛选
- [x] 搜索功能
- [x] 点赞功能
- [x] 留言评论
- [x] 广告位

## 技术栈

- 前端: Next.js 14 + TypeScript + Tailwind CSS
- 后端: Python FastAPI + asyncpg
- 数据库: PostgreSQL
- 部署: Vercel + Railway

## License

MIT