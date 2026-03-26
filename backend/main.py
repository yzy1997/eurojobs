from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import asyncpg
import os
import asyncio
import httpx
from bs4 import BeautifulSoup
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

# ============== 数据库初始化 ==============
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
                url TEXT NOT NULL UNIQUE,
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
        print("✅ 数据库表初始化完成")

# ============== 爬虫模块 ==============
class JobScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    async def scrape_indeed(self, country: str, keyword: str, limit: int = 10):
        country_urls = {
            "德国": "https://de.indeed.com",
            "法国": "https://fr.indeed.com",
            "英国": "https://www.indeed.co.uk",
        }
        base_url = country_urls.get(country, "https://de.indeed.com")
        url = f"{base_url}/jobs?q={keyword}&l="

        jobs = []
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                resp = await client.get(url, headers=self.headers)
                soup = BeautifulSoup(resp.text, "html.parser")
                job_cards = soup.select(".jobsearch-ResultsList > li")[:limit]

                for card in job_cards:
                    try:
                        title_elem = card.select_one(".jobTitle")
                        if not title_elem:
                            continue
                        title = title_elem.get_text(strip=True)
                        link = title_elem.find("a")
                        job_url = f"{base_url}{link.get('href')}" if link else ""

                        company = card.select_one(".companyName")
                        company = company.get_text(strip=True) if company else "未知公司"

                        location = card.select_one(".companyLocation")
                        location = location.get_text(strip=True) if location else ""

                        salary = card.select_one(".salaryText")
                        salary_range = salary.get_text(strip=True) if salary else ""

                        summary = card.select_one(".job-snippet")
                        description = summary.get_text(strip=True)[:500] if summary else ""

                        if title and job_url:
                            jobs.append({
                                "title": title,
                                "company": company,
                                "location": location,
                                "country": country,
                                "category": self.categorize(title, description),
                                "salary_range": salary_range,
                                "description": description,
                                "url": job_url,
                                "source": "Indeed",
                            })
                    except:
                        continue
        except Exception as e:
            print(f"Scraping error: {e}")
        return jobs

    def categorize(self, title: str, description: str) -> str:
        text = (title + " " + description).lower()
        if any(w in text for w in ["software", "developer", "engineer", "python", "java", "frontend", "backend", "data", "ai"]):
            return "技术"
        elif any(w in text for w in ["finance", "financial", "accounting"]):
            return "金融"
        elif any(w in text for w in ["marketing", "digital", "seo", "content"]):
            return "市场"
        elif any(w in text for w in ["sales", "account", "business"]):
            return "销售"
        elif any(w in text for w in ["design", "designer", "ui", "ux"]):
            return "设计"
        else:
            return "运营"

# ============== 运行爬虫并保存到数据库 ==============
async def run_scraper():
    print("🚀 开始自动爬取职位信息...")
    scraper = JobScraper()

    countries = ["德国", "法国", "英国"]
    keywords = ["python", "software developer"]

    all_jobs = []
    for country in countries:
        for keyword in keywords:
            try:
                jobs = await scraper.scrape_indeed(country, keyword, limit=10)
                all_jobs.extend(jobs)
                print(f"  ✅ {country} - {keyword}: {len(jobs)} 个职位")
            except Exception as e:
                print(f"  ❌ {country} - {keyword} 失败")

    # 保存到数据库
    if all_jobs:
        pool = await get_pool()
        async with pool.acquire() as conn:
            for job in all_jobs:
                try:
                    await conn.execute(
                        """INSERT INTO jobs (title, company, location, country, category, salary_range, description, url, source, likes)
                           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                           ON CONFLICT (url) DO NOTHING""",
                        job["title"], job["company"], job["location"], job["country"],
                        job["category"], job["salary_range"], job["description"],
                        job["url"], job["source"], 0
                    )
                except Exception as e:
                    pass
        print(f"🎉 共保存 {len(all_jobs)} 个职位到数据库")

# ============== 启动事件 ==============
@app.on_event("startup")
async def startup():
    try:
        await init_db()  # 先建表
        await run_scraper()  # 然后爬取数据
    except Exception as e:
        print(f"启动错误: {e}")

# ============== API 端点 ==============

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

class CommentCreate(BaseModel):
    job_id: int
    content: str
    author: str

class CommentResponse(CommentCreate):
    id: int
    created_at: str

@app.get("/")
async def root():
    return {"message": "EuroJobs API", "version": "1.0.0"}

@app.get("/api/scrape")
async def trigger_scrape():
    await run_scraper()
    return {"message": "爬取完成"}

@app.get("/api/jobs", response_model=List[dict])
async def get_jobs(country: Optional[str] = None, category: Optional[str] = None, search: Optional[str] = None, limit: int = 50, offset: int = 0):
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

@app.get("/api/jobs/{job_id}", response_model=dict)
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

@app.get("/api/comments", response_model=List[dict])
async def get_comments(job_id: Optional[int] = None):
    pool = await get_pool()
    async with pool.acquire() as conn:
        if job_id:
            rows = await conn.fetch("SELECT * FROM comments WHERE job_id = $1 ORDER BY created_at DESC", job_id)
        else:
            rows = await conn.fetch("SELECT * FROM comments ORDER BY created_at DESC")
        return [dict(row) for row in rows]

@app.post("/api/comments", response_model=dict)
async def create_comment(comment: CommentCreate):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO comments (job_id, content, author) VALUES ($1, $2, $3) RETURNING *",
            comment.job_id, comment.content, comment.author
        )
        return dict(row)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)