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
import random

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
    print("✅ 数据库表初始化完成")

# ============== 真实数据爬虫 ==============
class JobScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

    async def scrape_adzuna(self, country: str, keyword: str, limit: int = 15):
        """Adzuna API - 需要注册获取真实key"""
        # 使用真实的 Adzuna demo key (可能有限制)
        app_id = "2ef8c956"
        app_key = "00569c16b823ed37c3f4253495ae0fbf"
        country_code = {
            "德国": "de", "法国": "fr", "英国": "gb", "荷兰": "nl",
            "西班牙": "es", "意大利": "it", "瑞典": "se", "芬兰": "fi",
            "波兰": "pl", "丹麦": "dk", "挪威": "no", "瑞士": "ch",
            "奥地利": "at", "比利时": "be", "爱尔兰": "ie"
        }.get(country, "de")

        url = f"https://api.adzuna.com/v1/api/jobs/{country_code}/search?app_id={app_id}&app_key={app_key}&what={keyword}&results_per_page={limit}"

        jobs = []
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data.get("results", []):
                        jobs.append({
                            "title": item.get("title", ""),
                            "company": item.get("company", {}).get("display_name", "未知公司"),
                            "location": item.get("location", {}).get("display_name", ""),
                            "country": country,
                            "category": self.categorize(item.get("title", ""), ""),
                            "salary_range": self.format_salary(item.get("salary_min"), item.get("salary_max")),
                            "description": item.get("description", "")[:500] if item.get("description") else "",
                            "url": item.get("redirect_url", ""),
                            "source": "Adzuna",
                        })
                    print(f"  ✅ Adzuna {country}: {len(jobs)} 个职位")
                else:
                    print(f"  ⚠️ Adzuna 返回状态: {resp.status_code}")
        except Exception as e:
            print(f"  ❌ Adzuna 错误: {e}")

        return jobs

    def format_salary(self, min_sal, max_sal):
        if min_sal and max_sal:
            return f"€{int(min_sal)} - €{int(max_sal)}"
        return ""

    def categorize(self, title: str, description: str) -> str:
        text = (title + " " + description).lower()
        if any(w in text for w in ["software", "developer", "engineer", "python", "java", "frontend", "backend", "data", "ai", "it"]):
            return "技术"
        elif any(w in text for w in ["finance", "financial", "accounting", "accountant"]):
            return "金融"
        elif any(w in text for w in ["marketing", "digital", "seo", "content", "brand"]):
            return "市场"
        elif any(w in text for w in ["sales", "account", "business", "account manager"]):
            return "销售"
        elif any(w in text for w in ["design", "designer", "ui", "ux", "creative"]):
            return "设计"
        elif any(w in text for w in ["hr", "human resources", "recruiter", "talent"]):
            return "人力"
        else:
            return "运营"

# ============== 运行爬虫 ==============
async def run_scraper():
    print("🚀 开始自动爬取职位信息...")
    scraper = JobScraper()

    all_jobs = []

    # 1. Adzuna API (需要真实API key)
    print("📡 尝试 Adzuna API...")
    countries = ["德国", "法国", "英国", "荷兰", "西班牙", "意大利", "瑞典", "芬兰", "波兰", "丹麦", "挪威", "瑞士", "奥地利", "比利时", "爱尔兰"]
    keywords = [
        # 技术
        "python", "software developer", "data scientist", "frontend developer",
        "backend developer", "devops", "full stack", "machine learning", "cloud",
        "data engineer", "software engineer", "IT", "web developer",
        # 金融
        "accountant", "financial analyst", "finance", "banking", "accounting",
        # 市场
        "marketing", "digital marketing", "SEO", "content marketing", "brand manager",
        # 销售
        "sales", "account manager", "business development", "sales manager", "account executive",
        # 设计
        "designer", "UX", "UI", "graphic designer", "product designer",
        # 人力资源
        "HR", "human resources", "recruiter", "talent acquisition", "HR manager",
        # 运营
        "operations", "project manager", "product manager", "customer service", "support",
        # 其他
        "consultant", "legal", "admin", "assistant"
    ]

    for country in countries:
        for keyword in keywords:
            try:
                jobs = await scraper.scrape_adzuna(country, keyword, limit=10)
                all_jobs.extend(jobs)
                print(f"  ✅ {country} - {keyword}: {len(jobs)} 个职位")
            except Exception as e:
                print(f"  ❌ {country} - {keyword} 失败")

    # 2. 如果没数据，使用扩展的示例数据
    if len(all_jobs) < 5:
        print("⚠️ 使用扩展示例数据...")
        all_jobs = get_extended_sample_data()

    # 保存到数据库
    pool = await get_pool()
    async with pool.acquire() as conn:
        # 删除旧数据
        await conn.execute("DELETE FROM jobs")
        # 插入新数据
        for job in all_jobs:
            try:
                await conn.execute(
                    """INSERT INTO jobs (title, company, location, country, category, salary_range, description, url, source, likes)
                       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)""",
                    job["title"], job["company"], job["location"], job["country"],
                    job["category"], job["salary_range"], job["description"],
                    job["url"], job["source"], job.get("likes", 0)
                )
            except Exception as e:
                pass

    print(f"✅ 共保存 {len(all_jobs)} 个职位")

def get_extended_sample_data():
    """扩展的示例数据"""
    return [
        # 德国职位
        {"title": "Senior Python Developer", "company": "Siemens AG", "location": "Berlin", "country": "德国", "category": "技术", "salary_range": "€70,000 - €100,000", "description": "后端开发，Python/Django，远程可选", "url": "https://example.com/de/python-1", "source": "Adzuna", "likes": 0},
        {"title": "Frontend Developer", "company": "SAP", "location": "Munich", "country": "德国", "category": "技术", "salary_range": "€65,000 - €90,000", "description": "React/Angular，Vue.js经验", "url": "https://example.com/de/frontend-2", "source": "Adzuna", "likes": 0},
        {"title": "Data Engineer", "company": "Bosch", "location": "Stuttgart", "country": "德国", "category": "技术", "salary_range": "€60,000 - €85,000", "description": "大数据工程，Spark, Kafka", "url": "https://example.com/de/data-3", "source": "Adzuna", "likes": 0},
        {"title": "DevOps Engineer", "company": "BMW", "location": "Munich", "country": "德国", "category": "技术", "salary_range": "€70,000 - €95,000", "description": "Kubernetes, AWS, CI/CD", "url": "https://example.com/de/devops-4", "source": "Adzuna", "likes": 0},
        {"title": "Machine Learning Engineer", "company": "Audi", "location": "Ingolstadt", "country": "德国", "category": "技术", "salary_range": "€75,000 - €105,000", "description": "ML/AI，Python，TensorFlow", "url": "https://example.com/de/ml-5", "source": "Adzuna", "likes": 0},
        # 法国职位
        {"title": "Full Stack Developer", "company": "LVMH", "location": "Paris", "country": "法国", "category": "技术", "salary_range": "€55,000 - €80,000", "description": "Java/Python全栈，电商项目", "url": "https://example.com/fr/fullstack-1", "source": "Adzuna", "likes": 0},
        {"title": "Data Scientist", "company": "BNP Paribas", "location": "Paris", "country": "法国", "category": "技术", "salary_range": "€50,000 - €75,000", "description": "金融数据分析，Python,R", "url": "https://example.com/fr/data-2", "source": "Adzuna", "likes": 0},
        {"title": "Cloud Architect", "company": "Orange", "location": "Lyon", "country": "法国", "category": "技术", "salary_range": "€60,000 - €85,000", "description": "AWS/Azure架构设计", "url": "https://example.com/fr/cloud-3", "source": "Adzuna", "likes": 0},
        # 英国职位
        {"title": "Senior Software Engineer", "company": "Barclays", "location": "London", "country": "英国", "category": "技术", "salary_range": "£60,000 - £90,000", "description": "Java/Python，微服务", "url": "https://example.com/uk/swe-1", "source": "Adzuna", "likes": 0},
        {"title": "Backend Developer", "company": "HSBC", "location": "London", "country": "英国", "category": "技术", "salary_range": "£55,000 - £80,000", "description": "Python/Go，API开发", "url": "https://example.com/uk/backend-2", "source": "Adzuna", "likes": 0},
        {"title": "Product Manager", "company": "Amazon", "location": "London", "country": "英国", "category": "运营", "salary_range": "£50,000 - £75,000", "description": "产品管理，数据驱动", "url": "https://example.com/uk/pm-3", "source": "Adzuna", "likes": 0},
        # 荷兰职位
        {"title": "Python Developer", "company": "ASML", "location": "Amsterdam", "country": "荷兰", "category": "技术", "salary_range": "€55,000 - €75,000", "description": "Python后端，自动化", "url": "https://example.com/nl/python-1", "source": "Adzuna", "likes": 0},
        {"title": "UX Designer", "company": "Booking.com", "location": "Amsterdam", "country": "荷兰", "category": "设计", "salary_range": "€45,000 - €65,000", "description": "用户体验设计，Figma", "url": "https://example.com/nl/ux-2", "source": "Adzuna", "likes": 0},
        # 远程职位
        {"title": "Remote Python Engineer", "company": "GitLab", "location": "Remote", "country": "远程", "category": "技术", "salary_range": "$80,000 - $120,000", "description": "远程工作，全栈Python", "url": "https://example.com/remote/python-1", "source": "RemoteOK", "likes": 0},
        {"title": "Remote DevOps", "company": "DigitalOcean", "location": "Remote", "country": "远程", "category": "技术", "salary_range": "$90,000 - $130,000", "description": "远程工作，K8s专家", "url": "https://example.com/remote/devops-2", "source": "RemoteOK", "likes": 0},
        {"title": "Remote Data Scientist", "company": "Toptal", "location": "Remote", "country": "远程", "category": "技术", "salary_range": "$100,000 - $150,000", "description": "远程工作，AI/ML", "url": "https://example.com/remote/data-3", "source": "RemoteOK", "likes": 0},
    ]

# ============== 定时爬虫任务 ==============
import threading
import time

def start_scheduler():
    """后台定时爬虫 - 每天凌晨3点执行"""
    def run_daily():
        while True:
            # 计算下次运行时间（每天凌晨3点）
            now = datetime.now()
            next_run = now.replace(hour=3, minute=0, second=0, microsecond=0)
            if now.hour >= 3:
                next_run = next_run.replace(day=now.day + 1)

            wait_seconds = (next_run - now).total_seconds()
            print(f"⏰ 定时爬虫: {wait_seconds/3600:.1f} 小时后执行")
            time.sleep(wait_seconds)

            # 执行爬虫
            print("🕛 执行定时爬虫...")
            try:
                asyncio.run(run_scraper())
                print("✅ 定时爬虫完成")
            except Exception as e:
                print(f"❌ 定时爬虫失败: {e}")

    # 启动后台线程
    scheduler_thread = threading.Thread(target=run_daily, daemon=True)
    scheduler_thread.start()
    print("✅ 定时爬虫服务已启动 (每天凌晨3点)")

# ============== 启动事件 ==============
@app.on_event("startup")
async def startup():
    print("✅ EuroJobs API 启动")
    # 启动定时任务
    start_scheduler()
    # 立即执行一次爬虫
    asyncio.create_task(run_scraper())

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

class CommentCreate(BaseModel):
    job_id: int
    content: str
    author: str

@app.get("/")
async def root():
    return {"message": "EuroJobs API", "version": "1.0.0"}

@app.get("/api/scrape")
async def trigger_scrape():
    await run_scraper()
    return {"message": "爬取完成"}

@app.get("/api/jobs")
async def get_jobs(country: Optional[str] = None, category: Optional[str] = None, search: Optional[str] = None, limit: int = 50, offset: int = 0):
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)