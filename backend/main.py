from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import asyncpg
import os
import asyncio
import sys

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from datetime import datetime

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

class JobResponse(JobCreate):
    id: int
    created_at: str

    class Config:
        from_attributes = True

class CommentCreate(BaseModel):
    job_id: int
    content: str
    author: str

class CommentResponse(CommentCreate):
    id: int
    created_at: str

    class Config:
        from_attributes = True

async def init_db():
    """初始化数据库表"""
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
        # 添加 url 唯一约束用于去重
        await conn.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'jobs_url_key') THEN
                    ALTER TABLE jobs ADD CONSTRAINT jobs_url_key UNIQUE (url);
                END IF;
            END
            $$
        """)
        print("✅ 数据库表初始化完成")

# ============== 自动爬虫功能 ==============
async def scrape_and_save():
    """爬取职位并保存到数据库"""
    try:
        # 动态导入爬虫模块
        import sys
        sys.path.append('backend')
        from scrapers.indeed import IndeedScraper
        scraper = IndeedScraper()

        print("🔄 开始自动爬取职位信息...")

        # 爬取德国和法国的Python职位
        countries = ["德国", "法国", "英国"]
        keywords = ["python", "software developer", "data scientist"]

        all_jobs = []
        for country in countries:
            for keyword in keywords:
                try:
                    scraper = IndeedScraper()
                    jobs = await scraper.scrape(country=country, keywords=keyword, limit=10)
                    all_jobs.extend(jobs)
                    print(f"  ✅ {country} - {keyword}: 获取 {len(jobs)} 个职位")
                except Exception as e:
                    print(f"  ❌ {country} - {keyword} 失败: {e}")

        # 去重并保存到数据库
        if all_jobs:
            pool = await get_pool()
            seen = set()
            async with pool.acquire() as conn:
                for job in all_jobs:
                    # 根据 url 去重
                    if job['url'] in seen:
                        continue
                    seen.add(job['url'])

                    await conn.execute(
                        """INSERT INTO jobs (title, company, location, country, category, salary_range, description, url, source, likes)
                           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                           ON CONFLICT (url) DO NOTHING""",
                        job['title'], job['company'], job['location'], job['country'],
                        job['category'], job['salary_range'], job['description'],
                        job['url'], job['source'], job['likes']
                    )

            print(f"🎉 爬取完成！共保存 {len(seen)} 个新职位")
        else:
            print("⚠️ 未获取到任何职位")

    except Exception as e:
        print(f"❌ 爬虫运行失败: {e}")

async def start_scheduler():
    """定时任务：每6小时爬取一次"""
    import time
    while True:
        await scrape_and_save()
        # 等待6小时 (6 * 60 * 60 秒)
        await asyncio.sleep(6 * 60 * 60)

@app.on_event("startup")
async def startup_event():
    """服务启动时自动运行"""
    await init_db()  # 先初始化数据库表
    # 启动后台爬虫任务
    asyncio.create_task(start_scheduler())
    # 立即执行一次爬虫
    asyncio.create_task(scrape_and_save())

# ============== API 端点 ==============

@app.get("/")
async def root():
    return {"message": "EuroJobs API", "version": "1.0.0"}

@app.get("/api/scrape")
async def manual_scrape():
    """手动触发爬虫"""
    await scrape_and_save()
    return {"message": "爬虫已启动"}

@app.get("/api/jobs", response_model=List[JobResponse])
async def get_jobs(
    country: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
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

@app.get("/api/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM jobs WHERE id = $1", job_id)
        if not row:
            raise HTTPException(status_code=404, detail="Job not found")
        return dict(row)

@app.post("/api/jobs", response_model=JobResponse)
async def create_job(job: JobCreate):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO jobs (title, company, location, country, category, salary_range, description, url, source, likes)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
               RETURNING *""",
            job.title, job.company, job.location, job.country, job.category,
            job.salary_range, job.description, job.url, job.source, job.likes
        )
        return dict(row)

@app.post("/api/jobs/{job_id}/like")
async def like_job(job_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "UPDATE jobs SET likes = likes + 1 WHERE id = $1 RETURNING likes",
            job_id
        )
        if not row:
            raise HTTPException(status_code=404, detail="Job not found")
        return {"likes": row["likes"]}

@app.get("/api/comments", response_model=List[CommentResponse])
async def get_comments(job_id: Optional[int] = None):
    pool = await get_pool()
    async with pool.acquire() as conn:
        if job_id:
            rows = await conn.fetch(
                "SELECT * FROM comments WHERE job_id = $1 ORDER BY created_at DESC",
                job_id
            )
        else:
            rows = await conn.fetch("SELECT * FROM comments ORDER BY created_at DESC")
        return [dict(row) for row in rows]

@app.post("/api/comments", response_model=CommentResponse)
async def create_comment(comment: CommentCreate):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO comments (job_id, content, author)
               VALUES ($1, $2, $3)
               RETURNING *""",
            comment.job_id, comment.content, comment.author
        )
        return dict(row)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)