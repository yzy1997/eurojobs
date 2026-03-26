from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
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

# 内存存储
jobs_db = []
comments_db = []
likes_db = {}

# ============== 爬虫模块 ==============
class JobScraper:
    """职位爬虫"""

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    async def scrape_indeed(self, country: str, keyword: str, limit: int = 10):
        """爬取 Indeed 网站"""
        country_urls = {
            "德国": "https://de.indeed.com",
            "法国": "https://fr.indeed.com",
            "英国": "https://www.indeed.co.uk",
            "荷兰": "https://www.indeed.nl",
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
                    except Exception as e:
                        continue
        except Exception as e:
            print(f"Scraping Indeed {country} error: {e}")

        return jobs

    def categorize(self, title: str, description: str) -> str:
        """自动分类"""
        text = (title + " " + description).lower()
        if any(w in text for w in ["software", "developer", "engineer", "python", "java", "frontend", "backend", "data", "ai"]):
            return "技术"
        elif any(w in text for w in ["finance", "financial", "accounting", "bank"]):
            return "金融"
        elif any(w in text for w in ["marketing", "digital", "seo", "content", "brand"]):
            return "市场"
        elif any(w in text for w in ["sales", "account", "business"]):
            return "销售"
        elif any(w in text for w in ["design", "designer", "ui", "ux"]):
            return "设计"
        elif any(w in text for w in ["hr", "human resources", "recruiter"]):
            return "人力"
        else:
            return "运营"

# 初始化爬虫并执行
scraper = JobScraper()

async def run_scraper():
    """运行爬虫并更新数据"""
    print("🚀 开始自动爬取职位信息...")

    countries = ["德国", "法国", "英国"]
    keywords = ["python", "software developer", "data scientist"]

    all_jobs = []
    for country in countries:
        for keyword in keywords:
            try:
                jobs = await scraper.scrape_indeed(country, keyword, limit=15)
                all_jobs.extend(jobs)
                print(f"  ✅ {country} - {keyword}: 获取 {len(jobs)} 个职位")
            except Exception as e:
                print(f"  ❌ {country} - {keyword} 失败")

    # 去重
    seen = set()
    unique_jobs = []
    for job in all_jobs:
        if job["url"] not in seen:
            seen.add(job["url"])
            job["id"] = len(unique_jobs) + 1
            job["likes"] = 0
            job["created_at"] = datetime.now().strftime("%Y-%m-%d")
            unique_jobs.append(job)

    global jobs_db
    jobs_db = unique_jobs
    print(f"🎉 共获取 {len(jobs_db)} 个职位")

# 启动时自动爬取
@app.on_event("startup")
async def startup():
    asyncio.create_task(run_scraper())

# ============== API 端点 ==============

@app.get("/")
async def root():
    return {"message": "EuroJobs API", "version": "1.0.0"}

@app.get("/api/scrape")
async def trigger_scrape():
    """手动触发爬虫"""
    await run_scraper()
    return {"message": f"爬取完成，共 {len(jobs_db)} 个职位"}

@app.get("/api/jobs", response_model=List[dict])
async def get_jobs(
    country: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """获取职位列表"""
    jobs = jobs_db.copy()

    if country and country != "全部":
        jobs = [j for j in jobs if j.get("country") == country]

    if category and category != "全部":
        jobs = [j for j in jobs if j.get("category") == category]

    if search:
        search_lower = search.lower()
        jobs = [j for j in jobs if search_lower in j.get("title", "").lower() or search_lower in j.get("company", "").lower()]

    return jobs[offset:offset+limit]

@app.get("/api/jobs/{job_id}", response_model=dict)
async def get_job(job_id: int):
    """获取职位详情"""
    for job in jobs_db:
        if job.get("id") == job_id:
            return job
    raise HTTPException(status_code=404, detail="Job not found")

@app.post("/api/jobs/{job_id}/like")
async def like_job(job_id: int):
    """点赞职位"""
    for job in jobs_db:
        if job.get("id") == job_id:
            job["likes"] = job.get("likes", 0) + 1
            return {"likes": job["likes"]}
    raise HTTPException(status_code=404, detail="Job not found")

@app.get("/api/comments", response_model=List[dict])
async def get_comments(job_id: Optional[int] = None):
    if job_id:
        return [c for c in comments_db if c.get("job_id") == job_id]
    return comments_db

@app.post("/api/comments", response_model=dict)
async def create_comment(comment: dict):
    new_id = len(comments_db) + 1
    new_comment = {
        "id": new_id,
        "job_id": comment.get("job_id"),
        "content": comment.get("content"),
        "author": comment.get("author"),
        "created_at": datetime.now().strftime("%Y-%m-%d")
    }
    comments_db.append(new_comment)
    return new_comment

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)