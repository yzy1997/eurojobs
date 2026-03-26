import asyncio
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime

class BaseScraper:
    """Base class for job scrapers"""
    source_name = "base"

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    async def fetch(self, url: str) -> Optional[str]:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            try:
                resp = await client.get(url, headers=self.headers)
                return resp.text
            except Exception as e:
                print(f"Error fetching {url}: {e}")
                return None

    async def scrape(self, country: str = "germany", keywords: str = "python") -> List[Dict]:
        raise NotImplementedError

class IndeedScraper(BaseScraper):
    source_name = "Indeed"

    COUNTRY_URLS = {
        "德国": "https://de.indeed.com",
        "法国": "https://fr.indeed.com",
        "英国": "https://www.indeed.co.uk",
        "荷兰": "https://www.indeed.nl",
        "西班牙": "https://www.indeed.es",
        "意大利": "https://www.indeed.it",
    }

    async def scrape(self, country: str = "德国", keywords: str = "python", limit: int = 20) -> List[Dict]:
        base_url = self.COUNTRY_URLS.get(country, "https://de.indeed.com")
        search_url = f"{base_url}/jobs?q={keywords}&l=&sort=date"

        html = await self.fetch(search_url)
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        jobs = []

        job_cards = soup.select(".jobsearch-ResultsList > li")[:limit]

        for card in job_cards:
            try:
                title_elem = card.select_one(".jobTitle")
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                link = title_elem.find("a")
                url = f"{base_url}{link.get('href')}" if link else ""

                company = card.select_one(".companyName") or card.select_one(".company")
                company = company.get_text(strip=True) if company else "未知公司"

                location = card.select_one(".companyLocation")
                location = location.get_text(strip=True) if location else ""

                salary = card.select_one(".salaryText")
                salary_range = salary.get_text(strip=True) if salary else ""

                summary = card.select_one(".job-snippet")
                description = summary.get_text(strip=True) if summary else ""

                jobs.append({
                    "title": title,
                    "company": company,
                    "location": location,
                    "country": country,
                    "category": self.categorize(title, description),
                    "salary_range": salary_range,
                    "description": description[:500],
                    "url": url,
                    "source": self.source_name,
                    "likes": 0,
                })
            except Exception as e:
                print(f"Error parsing job card: {e}")
                continue

        return jobs

    def categorize(self, title: str, description: str) -> str:
        text = (title + " " + description).lower()
        if any(w in text for w in ["software", "developer", "engineer", "python", "java", "frontend", "backend"]):
            return "技术"
        elif any(w in text for w in ["finance", "financial", "accounting", "accountant"]):
            return "金融"
        elif any(w in text for w in ["marketing", "digital", "seo", "content"]):
            return "市场"
        elif any(w in text for w in ["sales", "account", "business"]):
            return "销售"
        elif any(w in text for w in ["design", "designer", "ui", "ux"]):
            return "设计"
        elif any(w in text for w in ["hr", "human resources", "recruiter", "talent"]):
            return "人力"
        else:
            return "运营"

class LinkedInScraper(BaseScraper):
    source_name = "LinkedIn"

    async def scrape(self, country: str = "德国", keywords: str = "python", limit: int = 20) -> List[Dict]:
        # LinkedIn has strict anti-scraping, using a simplified mock for demo
        # In production, use official LinkedIn API or browser automation
        base_url = f"https://www.linkedin.com/jobs/search/?keywords={keywords}&location={country}"

        html = await self.fetch(base_url)
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        jobs = []

        job_cards = soup.select(".job-card-container")[:limit]

        for card in job_cards:
            try:
                title_elem = card.select_one(".job-card-list__title")
                title = title_elem.get_text(strip=True) if title_elem else "未知职位"

                link = card.select_one("a.job-card-list__title")
                url = link.get("href", "") if link else ""

                company = card.select_one(".job-card-container__company-name")
                company = company.get_text(strip=True) if company else "未知公司"

                location = card.select_one(".job-card-container__metadata-item")
                location = location.get_text(strip=True) if location else ""

                jobs.append({
                    "title": title,
                    "company": company,
                    "location": location,
                    "country": country,
                    "category": "技术",
                    "salary_range": "",
                    "description": "来自 LinkedIn",
                    "url": f"https://www.linkedin.com{url}",
                    "source": self.source_name,
                    "likes": 0,
                })
            except Exception as e:
                print(f"Error parsing LinkedIn card: {e}")
                continue

        return jobs

async def scrape_all(keywords: str = "python", country: str = "德国") -> List[Dict]:
    """Scrape jobs from all sources"""
    scrapers = [IndeedScraper(), LinkedInScraper()]
    all_jobs = []

    for scraper in scrapers:
        try:
            jobs = await scraper.scrape(country=country, keywords=keywords)
            all_jobs.extend(jobs)
            print(f"[{scraper.source_name}] Scraped {len(jobs)} jobs")
        except Exception as e:
            print(f"[{scraper.source_name}] Error: {e}")

    return all_jobs

if __name__ == "__main__":
    async def main():
        jobs = await scrape_all("python developer", "德国")
        for job in jobs[:5]:
            print(f"- {job['title']} @ {job['company']}")

    asyncio.run(main())