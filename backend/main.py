from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import asyncpg
import os

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