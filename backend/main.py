"""EuroJobs API - 主入口文件"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import asyncpg
import os
import asyncio
import threading
import time
from datetime import datetime

# 导入认证模块
from auth import router as auth_router, init_users_table

# 导入爬虫模块
from scraper import run_scraper

app = FastAPI(title="EuroJobs API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/eurojobs")

pool: Optional[asyncpg.Pool] = None

async def get_pool():
    global pool
    if pool is None:
        pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
    return pool

# ============== 数据库初始化 ==============
async def init_db():
    print("🔄 正在初始化数据库...")
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                company VARCHAR(255) NOT NULL,
                location VARCHAR(100),
                country VARCHAR(50) NOT NULL,
                category VARCHAR(50),
                salary_range VARCHAR(100),
                description TEXT,
                url TEXT NOT NULL,
                source VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                likes INTEGER DEFAULT 0
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                id SERIAL PRIMARY KEY,
                job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
                content TEXT NOT NULL,
                author VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    # 初始化 users 表
    await init_users_table()
    print("✅ 数据库表初始化完成")

# ============== 定时爬虫任务 ==============
def start_scheduler():
    """后台定时爬虫 - 每天凌晨3点执行"""
    def run_daily():
        while True:
            now = datetime.now()
            next_run = now.replace(hour=3, minute=0, second=0, microsecond=0)
            if now.hour >= 3:
                next_run = next_run.replace(day=now.day + 1)

            wait_seconds = (next_run - now).total_seconds()
            print(f"⏰ 定时爬虫: {wait_seconds/3600:.1f} 小时后执行")
            time.sleep(wait_seconds)

            print("🕛 执行定时爬虫...")
            try:
                asyncio.run(run_scraper())
                print("✅ 定时爬虫完成")
            except Exception as e:
                print(f"❌ 定时爬虫失败: {e}")

    scheduler_thread = threading.Thread(target=run_daily, daemon=True)
    scheduler_thread.start()
    print("✅ 定时爬虫服务已启动 (每天凌晨3点)")

# ============== 启动事件 ==============
@app.on_event("startup")
async def startup():
    print("✅ EuroJobs API 启动")
    await init_db()
    start_scheduler()
    asyncio.create_task(run_scraper())

# ============== 数据模型 ==============
class JobCreate(BaseModel):
    title: str
    company: str
    location: str
    country: str
    category: str
    salary_range: Optional[str] = None
    description: str
    url: str
    source: str
    likes: int = 0

class CommentCreate(BaseModel):
    job_id: int
    content: str
    author: str

# ============== API 端点 ==============
@app.get("/")
async def root():
    return {"message": "EuroJobs API", "version": "1.0.0"}

@app.get("/api/scrape")
async def trigger_scrape():
    await run_scraper()
    return {"message": "爬取完成"}

@app.get("/api/jobs")
async def get_jobs(country: Optional[str] = None, category: Optional[str] = None, search: Optional[str] = None, limit: int = 10000, offset: int = 0):
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            query = "SELECT * FROM jobs WHERE 1=1"
            params = []
            param_count = 1

            if country and country != "全部":
                query += f" AND country = ${param_count}"
                params.append(country)
                param_count += 1

            if category and category != "全部":
                query += f" AND category = ${param_count}"
                params.append(category)
                param_count += 1

            if search:
                query += f" AND (title ILIKE ${param_count} OR company ILIKE ${param_count})"
                params.append(f"%{search}%")
                param_count += 1

            query += f" ORDER BY created_at DESC LIMIT ${param_count} OFFSET ${param_count + 1}"
            params.extend([limit, offset])

            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
    except Exception as e:
        print(f"Error: {e}")
        return []

@app.get("/api/jobs/{job_id}")
async def get_job(job_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM jobs WHERE id = $1", job_id)
        if not row:
            raise HTTPException(status_code=404, detail="Job not found")
        return dict(row)

@app.post("/api/jobs/{job_id}/like")
async def like_job(job_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("UPDATE jobs SET likes = likes + 1 WHERE id = $1 RETURNING likes", job_id)
        if not row:
            raise HTTPException(status_code=404, detail="Job not found")
        return {"likes": row["likes"]}

@app.get("/api/comments")
async def get_comments(job_id: Optional[int] = None):
    pool = await get_pool()
    async with pool.acquire() as conn:
        if job_id:
            rows = await conn.fetch("SELECT * FROM comments WHERE job_id = $1 ORDER BY created_at DESC", job_id)
        else:
            rows = await conn.fetch("SELECT * FROM comments ORDER BY created_at DESC")
        return [dict(row) for row in rows]

@app.post("/api/comments")
async def create_comment(comment: CommentCreate):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO comments (job_id, content, author) VALUES ($1, $2, $3) RETURNING *",
            comment.job_id, comment.content, comment.author
        )
        return dict(row)

# ============== 注册认证路由 ==============
app.include_router(auth_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)