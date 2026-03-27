"""认证模块 - 登录、注册、JWT Token"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional
import asyncpg
import bcrypt
import jwt
import os
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()

SECRET_KEY = os.getenv("SECRET_KEY", "eurojobs-secret-key-change-in-production")
ALGORITHM = "HS256"

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/eurojobs")

# 数据库连接池
pool: Optional[asyncpg.Pool] = None

async def get_pool():
    global pool
    if pool is None:
        pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
    return pool

# ============== 数据模型 ==============
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# ============== 工具函数 ==============
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_token(user_id: int, username: str) -> str:
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        username = payload.get("username")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"user_id": user_id, "username": username}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ============== 初始化用户表 ==============
async def init_users_table():
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

# ============== API 端点 ==============
@router.post("/register", response_model=TokenResponse)
async def register(user: UserCreate):
    pool = await get_pool()
    async with pool.acquire() as conn:
        # 检查用户名是否存在
        existing = await conn.fetchrow(
            "SELECT id FROM users WHERE username = $1 OR email = $2",
            user.username, user.email
        )
        if existing:
            raise HTTPException(status_code=400, detail="用户名或邮箱已存在")

        # 加密密码
        password_hash = hash_password(user.password)

        # 插入用户
        result = await conn.fetchrow(
            """INSERT INTO users (username, email, password_hash)
               VALUES ($1, $2, $3) RETURNING id, username, email, created_at""",
            user.username, user.email, password_hash
        )

        # 生成 token
        token = create_token(result["id"], result["username"])

        return TokenResponse(
            access_token=token,
            user=UserResponse(**result)
        )

@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    pool = await get_pool()
    async with pool.acquire() as conn:
        # 查找用户
        user = await conn.fetchrow(
            "SELECT id, username, email, password_hash, created_at FROM users WHERE username = $1",
            credentials.username
        )

        if not user:
            raise HTTPException(status_code=401, detail="用户名或密码错误")

        # 验证密码
        if not verify_password(credentials.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="用户名或密码错误")

        # 生成 token
        token = create_token(user["id"], user["username"])

        return TokenResponse(
            access_token=token,
            user=UserResponse(
                id=user["id"],
                username=user["username"],
                email=user["email"],
                created_at=user["created_at"]
            )
        )

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    pool = await get_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT id, username, email, created_at FROM users WHERE id = $1",
            current_user["user_id"]
        )
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        return UserResponse(**user)