"""爬虫模块 - 职位数据爬取"""
import asyncio
import aiohttp
import asyncpg
import os

# Adzuna API 配置
ADZUNA_APP_ID = "2ef8c956"
ADZUNA_APP_KEY = "00569c16b823ed37c3f4253495ae0fbf"

# 国家代码映射
COUNTRY_CODES = {
    "德国": "de", "法国": "fr", "英国": "gb", "荷兰": "nl",
    "西班牙": "es", "意大利": "it", "瑞典": "se", "芬兰": "fi",
    "波兰": "pl", "丹麦": "dk", "挪威": "no", "瑞士": "ch",
    "比利时": "be", "爱尔兰": "ie", "奥地利": "at", "捷克": "cz",
    "匈牙利": "hu", "葡萄牙": "pt", "希腊": "gr"
}

# 欧洲国家列表
COUNTRIES = [
    "德国", "法国", "英国", "荷兰", "西班牙", "意大利", "瑞典", "芬兰", "波兰",
    "丹麦", "挪威", "瑞士", "比利时", "爱尔兰", "奥地利", "捷克", "匈牙利", "葡萄牙", "希腊"
]

# 热门关键词
KEYWORDS = [
    "python", "java", "javascript", "software", "developer", "engineer", "data scientist",
    "frontend", "backend", "full stack", "web", "cloud", "devops", "machine learning",
    "product manager", "project manager", "designer", "UX",
    "accountant", "finance", "financial", "banking",
    "marketing", "sales", "digital",
    "HR", "human resources", "recruiter",
    "operations", "customer service",
    "nurse", "medical", "healthcare",
    "teacher", "education", "trainer"
]

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/eurojobs")


def categorize_job(title: str) -> str:
    """分类函数"""
    text = title.lower()
    if any(w in text for w in ["python", "java", "javascript", "software", "developer", "engineer", "frontend", "backend", "full stack", "web", "cloud", "devops", "machine learning", "data"]):
        return "技术"
    elif any(w in text for w in ["product", "project", "designer", "UX"]):
        return "产品设计"
    elif any(w in text for w in ["finance", "accountant", "banking", "financial"]):
        return "金融"
    elif any(w in text for w in ["marketing", "digital", "sales", "brand"]):
        return "市场"
    elif any(w in text for w in ["HR", "human resources", "recruiter"]):
        return "人力资源"
    elif any(w in text for w in ["nurse", "doctor", "medical", "healthcare"]):
        return "医疗"
    elif any(w in text for w in ["teacher", "education", "trainer"]):
        return "教育"
    elif any(w in text for w in ["manufacturing", "production", "mechanical"]):
        return "制造工程"
    elif any(w in text for w in ["legal", "lawyer", "compliance"]):
        return "法律"
    return "其他"


def format_salary(min_sal, max_sal):
    if min_sal and max_sal:
        return f"€{int(min_sal)} - €{int(max_sal)}"
    return ""


async def scrape_single(session, country: str, keyword: str, limit: int = 5):
    """单个查询爬取"""
    country_code = COUNTRY_CODES.get(country, "de")
    url = f"https://api.adzuna.com/v1/api/jobs/{country_code}/search?app_id={ADZUNA_APP_ID}&app_key={ADZUNA_APP_KEY}&what={keyword}&results_per_page={limit}"

    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            if resp.status == 200:
                data = await resp.json()
                jobs = []
                for item in data.get("results", []):
                    jobs.append({
                        "title": item.get("title", ""),
                        "company": item.get("company", {}).get("display_name", "未知公司"),
                        "location": item.get("location", {}).get("display_name", ""),
                        "country": country,
                        "category": categorize_job(item.get("title", "")),
                        "salary_range": format_salary(item.get("salary_min"), item.get("salary_max")),
                        "description": item.get("description", "")[:500] if item.get("description") else "",
                        "url": item.get("redirect_url", ""),
                        "source": "Adzuna",
                    })
                return jobs
    except Exception as e:
        pass
    return []


async def run_scraper():
    """运行爬虫 - 从 Adzuna 获取职位数据"""
    print("🚀 开始自动爬取职位信息...")

    all_jobs = []

    print(f"🔍 开始爬取 {len(COUNTRIES)} 个国家 x {len(KEYWORDS)} 个关键词...")

    # 创建 session
    async with aiohttp.ClientSession() as session:
        total = len(COUNTRIES) * len(KEYWORDS)
        count = 0

        for country in COUNTRIES:
            for keyword in KEYWORDS:
                count += 1
                try:
                    jobs = await scrape_single(session, country, keyword, limit=5)
                    if jobs:
                        all_jobs.extend(jobs)
                    # 每10次请求等待1秒，避免被限制
                    if count % 10 == 0:
                        await asyncio.sleep(1)
                        print(f"  📊 进度: {count}/{total} - 已获取 {len(all_jobs)} 个职位")
                except Exception as e:
                    pass

    print(f"📊 共获取 {len(all_jobs)} 个职位")

    # 去重
    seen = {}
    unique_jobs = []
    for job in all_jobs:
        if job["url"] not in seen:
            seen[job["url"]] = True
            unique_jobs.append(job)

    print(f"📊 去重后: {len(unique_jobs)} 个职位")

    # 如果没数据，使用示例数据
    if len(unique_jobs) < 5:
        print("⚠️ 使用扩展示例数据...")
        unique_jobs = get_extended_sample_data()

    # 保存到数据库
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
    async with pool.acquire() as conn:
        # 删除旧数据
        await conn.execute("DELETE FROM jobs")
        # 插入新数据
        for job in unique_jobs:
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

    print(f"✅ 共保存 {len(unique_jobs)} 个职位")
    await pool.close()


def get_extended_sample_data():
    """扩展的示例数据"""
    return [
        {"title": "Senior Python Developer", "company": "Siemens AG", "location": "Berlin", "country": "德国", "category": "技术", "salary_range": "€70,000 - €100,000", "description": "后端开发，Python/Django，远程可选", "url": "https://example.com/de/python-1", "source": "Adzuna", "likes": 0},
        {"title": "Frontend Developer", "company": "SAP", "location": "Munich", "country": "德国", "category": "技术", "salary_range": "€65,000 - €90,000", "description": "React/Angular，Vue.js经验", "url": "https://example.com/de/frontend-2", "source": "Adzuna", "likes": 0},
        {"title": "Data Engineer", "company": "Bosch", "location": "Stuttgart", "country": "德国", "category": "技术", "salary_range": "€60,000 - €85,000", "description": "大数据工程，Spark, Kafka", "url": "https://example.com/de/data-3", "source": "Adzuna", "likes": 0},
        {"title": "Full Stack Developer", "company": "LVMH", "location": "Paris", "country": "法国", "category": "技术", "salary_range": "€55,000 - €80,000", "description": "Java/Python全栈，电商项目", "url": "https://example.com/fr/fullstack-1", "source": "Adzuna", "likes": 0},
        {"title": "Data Scientist", "company": "BNP Paribas", "location": "Paris", "country": "法国", "category": "技术", "salary_range": "€50,000 - €75,000", "description": "金融数据分析，Python,R", "url": "https://example.com/fr/data-2", "source": "Adzuna", "likes": 0},
        {"title": "Senior Software Engineer", "company": "Barclays", "location": "London", "country": "英国", "category": "技术", "salary_range": "£60,000 - £90,000", "description": "Java/Python，微服务", "url": "https://example.com/uk/swe-1", "source": "Adzuna", "likes": 0},
        {"title": "Backend Developer", "company": "HSBC", "location": "London", "country": "英国", "category": "技术", "salary_range": "£55,000 - £80,000", "description": "Python/Go，API开发", "url": "https://example.com/uk/backend-2", "source": "Adzuna", "likes": 0},
        {"title": "Python Developer", "company": "ASML", "location": "Amsterdam", "country": "荷兰", "category": "技术", "salary_range": "€55,000 - €75,000", "description": "Python后端，自动化", "url": "https://example.com/nl/python-1", "source": "Adzuna", "likes": 0},
        {"title": "UX Designer", "company": "Booking.com", "location": "Amsterdam", "country": "荷兰", "category": "产品设计", "salary_range": "€45,000 - €65,000", "description": "用户体验设计，Figma", "url": "https://example.com/nl/ux-2", "source": "Adzuna", "likes": 0},
        {"title": "Remote Python Engineer", "company": "GitLab", "location": "Remote", "country": "远程", "category": "技术", "salary_range": "$80,000 - $120,000", "description": "远程工作，全栈Python", "url": "https://example.com/remote/python-1", "source": "RemoteOK", "likes": 0},
    ]