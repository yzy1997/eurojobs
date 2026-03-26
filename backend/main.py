from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os

app = FastAPI(title="EuroJobs API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 示例职位数据 (不需要数据库)
SAMPLE_JOBS = [
    {"id": 1, "title": "Senior Python Developer", "company": "TechCorp Berlin", "location": "Berlin", "country": "德国", "category": "技术", "salary_range": "€70,000 - €100,000", "description": "Python后端开发，熟练掌握Django/FastAPI，有欧洲工作经历优先。", "url": "https://example.com/job1", "source": "Indeed", "likes": 42, "created_at": "2024-01-15"},
    {"id": 2, "title": "Frontend Engineer", "company": "WebSolutions Paris", "location": "Paris", "country": "法国", "category": "技术", "salary_range": "€55,000 - €75,000", "description": "React/Vue开发，热爱前端技术，有大型项目经验。", "url": "https://example.com/job2", "source": "LinkedIn", "likes": 28, "created_at": "2024-01-14"},
    {"id": 3, "title": "Data Scientist", "company": "DataCo London", "location": "London", "country": "英国", "category": "技术", "salary_range": "£50,000 - £70,000", "description": "数据分析，机器学习，Python/R，必须有相关经验。", "url": "https://example.com/job3", "source": "Indeed", "likes": 35, "created_at": "2024-01-13"},
    {"id": 4, "title": "Marketing Manager", "company": "BrandCo Amsterdam", "location": "Amsterdam", "country": "荷兰", "category": "市场", "salary_range": "€50,000 - €70,000", "description": "数字营销经验，熟悉欧洲市场，英文流利。", "url": "https://example.com/job4", "source": "LinkedIn", "likes": 19, "created_at": "2024-01-12"},
    {"id": 5, "title": "UX Designer", "company": "DesignHub Stockholm", "location": "Stockholm", "country": "瑞典", "category": "设计", "salary_range": "SEK 50,000 - 70,000", "description": "用户体验设计，熟练使用Figma，有作品集。", "url": "https://example.com/job5", "source": "Indeed", "likes": 31, "created_at": "2024-01-11"},
    {"id": 6, "title": "Product Manager", "company": "Innovate GmbH", "location": "Munich", "country": "德国", "category": "运营", "salary_range": "€65,000 - €90,000", "description": "产品管理，有技术背景优先，协调能力强。", "url": "https://example.com/job6", "source": "LinkedIn", "likes": 24, "created_at": "2024-01-10"},
    {"id": 7, "title": "DevOps Engineer", "company": "CloudTech Paris", "location": "Lyon", "country": "法国", "category": "技术", "salary_range": "€60,000 - €85,000", "description": "Kubernetes, AWS, CI/CD经验丰富。", "url": "https://example.com/job7", "source": "Indeed", "likes": 45, "created_at": "2024-01-09"},
    {"id": 8, "title": "Sales Representative", "company": "TradeCo London", "location": "Manchester", "country": "英国", "category": "销售", "salary_range": "£35,000 - £50,000", "description": "B2B销售经验，熟悉欧洲市场，英文流利。", "url": "https://example.com/job8", "source": "Indeed", "likes": 15, "created_at": "2024-01-08"},
]

# 内存存储评论和点赞
comments = [
    {"id": 1, "job_id": 1, "content": "很棒的职位！请问需要签证支持吗？", "author": "张三", "created_at": "2024-01-15"},
    {"id": 2, "job_id": 1, "content": "请问这个岗位接受远程吗？", "author": "李四", "created_at": "2024-01-15"},
    {"id": 3, "job_id": 2, "content": "公司氛围怎么样？", "author": "王五", "created_at": "2024-01-14"},
]

likes = {job["id"]: job["likes"] for job in SAMPLE_JOBS}

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

# ============== API 端点 ==============

@app.get("/")
async def root():
    return {"message": "EuroJobs API", "version": "1.0.0"}

@app.get("/api/jobs", response_model=List[JobResponse])
async def get_jobs(
    country: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """获取职位列表"""
    jobs = SAMPLE_JOBS.copy()

    if country and country != "全部":
        jobs = [j for j in jobs if j["country"] == country]

    if category and category != "全部":
        jobs = [j for j in jobs if j["category"] == category]

    if search:
        search_lower = search.lower()
        jobs = [j for j in jobs if search_lower in j["title"].lower() or search_lower in j["company"].lower()]

    return jobs[offset:offset+limit]

@app.get("/api/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: int):
    """获取单个职位详情"""
    for job in SAMPLE_JOBS:
        if job["id"] == job_id:
            return job
    raise HTTPException(status_code=404, detail="Job not found")

@app.post("/api/jobs/{job_id}/like")
async def like_job(job_id: int):
    """点赞职位"""
    if job_id not in likes:
        raise HTTPException(status_code=404, detail="Job not found")
    likes[job_id] = likes.get(job_id, 0) + 1
    return {"likes": likes[job_id]}

@app.get("/api/comments", response_model=List[CommentResponse])
async def get_comments(job_id: Optional[int] = None):
    """获取评论"""
    if job_id:
        return [c for c in comments if c["job_id"] == job_id]
    return comments

@app.post("/api/comments", response_model=CommentResponse)
async def create_comment(comment: CommentCreate):
    """创建评论"""
    new_id = len(comments) + 1
    new_comment = {
        "id": new_id,
        "job_id": comment.job_id,
        "content": comment.content,
        "author": comment.author,
        "created_at": "2024-01-15"
    }
    comments.append(new_comment)
    return new_comment

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)