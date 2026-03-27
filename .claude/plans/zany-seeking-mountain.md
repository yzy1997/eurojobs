# 登录系统实现计划

## 背景
用户已有后端部署，需要：
1. 重构后端代码 - 把登录逻辑和爬虫逻辑拆分到独立文件
2. 添加登录功能 - 用户信息存数据库

## 重构方案

### 后端重构
- `backend/main.py` - 主文件，只做路由导入
- `backend/auth.py` - 登录/注册逻辑
- `backend/scraper.py` - 爬虫逻辑
- `backend/database.py` - 数据库连接和初始化

### 数据库
新建 `users` 表:
```sql
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  username VARCHAR(50) UNIQUE NOT NULL,
  email VARCHAR(100) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### API 端点
- `POST /api/auth/register` - 注册
- `POST /api/auth/login` - 登录 (返回JWT)
- `GET /api/auth/me` - 获取当前用户

### 前端
- `app/login/page.tsx` - 登录页
- `app/register/page.tsx` - 注册页
- 修改 `layout.tsx` - 添加登录/登出按钮

## 关键文件
- `backend/main.py`
- `backend/auth.py` (新建)
- `backend/scraper.py` (新建)
- `backend/database.py` (新建)
- `app/login/page.tsx` (新建)
- `app/register/page.tsx` (新建)

## 验证
1. 注册用户 → 数据库有记录
2. 登录成功 → 返回token
3. 前端登录/注册页面可用