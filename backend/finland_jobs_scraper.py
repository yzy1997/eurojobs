#!/usr/bin/env python3
"""
Minimal Finland jobs collector

Version 1:
- Kuntarekry public JSON source
- Tyomarkkinatori official API placeholder
- Unified schema
- Deduplication
- CSV + JSONL export

Usage:
    python finland_jobs_scraper.py --out jobs.csv --jsonl jobs.jsonl
    python finland_jobs_scraper.py --query researcher --location Helsinki

Environment variables:
    TYO_API_BASE_URL     Base URL for Tyomarkkinatori official API
    TYO_API_KEY          API key / bearer token for Tyomarkkinatori
    TYO_API_TIMEOUT      Request timeout in seconds (default 20)

Notes:
- This script intentionally avoids login, browser automation, and any bypass logic.
- Tyomarkkinatori access is left as an official-API adapter only.
- Kuntarekry response formats may evolve, so the parser is defensive.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import requests


USER_AGENT = "finland-jobs-collector/0.1 (+contact: replace-with-your-email)"
DEFAULT_TIMEOUT = 20


@dataclass
class JobRecord:
    source: str
    source_job_id: str
    title: str
    company: str
    location: str
    published_at: str
    deadline: str
    url: str
    description_snippet: str
    language: str
    raw: Dict[str, Any]

    @property
    def dedup_key(self) -> str:
        if self.source and self.source_job_id:
            return f"{self.source}:{self.source_job_id}"
        base = "|".join([
            self.source or "",
            self.title or "",
            self.company or "",
            self.location or "",
            self.url or "",
        ])
        return hashlib.sha256(base.encode("utf-8")).hexdigest()


class BaseAdapter:
    source_name: str = "base"

    def fetch(self, *, query: Optional[str] = None, location: Optional[str] = None) -> List[JobRecord]:
        raise NotImplementedError


class HttpClient:
    def __init__(self, timeout: int = DEFAULT_TIMEOUT) -> None:
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def get_json(self, url: str, *, params: Optional[Dict[str, Any]] = None,
                 headers: Optional[Dict[str, str]] = None, retries: int = 3,
                 backoff_seconds: float = 2.0) -> Any:
        merged_headers = dict(headers or {})
        last_err: Optional[Exception] = None
        for attempt in range(1, retries + 1):
            try:
                resp = self.session.get(url, params=params, headers=merged_headers, timeout=self.timeout)
                resp.raise_for_status()
                return resp.json()
            except Exception as exc:  # noqa: BLE001
                last_err = exc
                if attempt == retries:
                    break
                time.sleep(backoff_seconds * attempt)
        assert last_err is not None
        raise last_err


def clean_text(text: Any) -> str:
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


class KuntarekryAdapter(BaseAdapter):
    source_name = "kuntarekry"

    def __init__(self, client: HttpClient, endpoint: str = "https://www.kuntarekry.fi/fi/api/json-jobs/") -> None:
        self.client = client
        self.endpoint = endpoint

    def fetch(self, *, query: Optional[str] = None, location: Optional[str] = None) -> List[JobRecord]:
        # The public endpoint has changed formats before, so this parser accepts several shapes.
        data = self.client.get_json(self.endpoint)
        items = self._extract_items(data)
        jobs: List[JobRecord] = []

        for item in items:
            title = self._pick(item, ["title", "name", "job_title", "heading"])
            company = self._pick(item, ["organisation", "organization", "employer", "company"])
            url = self._pick(item, ["url", "job_url", "link", "href"])
            location_value = self._pick(item, ["organisation", "location", "city", "municipality", "address_city"])
            published_at = self._pick(item, ["publication_start", "published_at", "created_at", "publicationDate"])
            deadline = self._pick(item, ["publication_end", "deadline", "expires_at", "endDate"])
            source_job_id = str(self._pick(item, ["id", "job_id", "uuid", "slug"]))
            description = self._pick(item, ["description", "teaser", "lead", "summary", "body"])
            language = self._pick(item, ["language", "lang"]) or self._guess_language(title, description)

            if not title and not url:
                continue

            normalized = JobRecord(
                source=self.source_name,
                source_job_id=source_job_id,
                title=clean_text(title),
                company=clean_text(company),
                location=clean_text(location_value),
                published_at=clean_text(published_at),
                deadline=clean_text(deadline),
                url=clean_text(url),
                description_snippet=clean_text(description)[:500],
                language=clean_text(language),
                raw=item,
            )

            if query and not self._matches_query(normalized, query):
                continue
            if location and location.lower() not in (normalized.location or "").lower():
                continue
            jobs.append(normalized)

        return jobs

    @staticmethod
    def _pick(item: Dict[str, Any], keys: Iterable[str]) -> Any:
        for key in keys:
            if key in item and item[key] not in (None, ""):
                return item[key]
        return ""

    @staticmethod
    def _extract_items(data: Any) -> List[Dict[str, Any]]:
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
        if isinstance(data, dict):
            for key in ("jobs", "results", "items", "data"):
                if isinstance(data.get(key), list):
                    return [x for x in data[key] if isinstance(x, dict)]
        return []

    @staticmethod
    def _matches_query(job: JobRecord, query: str) -> bool:
        q = query.lower().strip()
        hay = " ".join([
            job.title,
            job.company,
            job.location,
            job.description_snippet,
        ]).lower()
        return all(token in hay for token in q.split())

    @staticmethod
    def _guess_language(title: str, description: str) -> str:
        text = f"{title} {description}".lower()
        if any(word in text for word in ["työ", "tehtävä", "hakija", "kunta", "sijainti"]):
            return "fi"
        if any(word in text for word in ["jobb", "ansökan", "kommun"]):
            return "sv"
        return "en"


class TyomarkkinatoriOfficialApiAdapter(BaseAdapter):
    source_name = "tyomarkkinatori"

    def __init__(self, client: HttpClient, base_url: Optional[str], api_key: Optional[str]) -> None:
        self.client = client
        self.base_url = (base_url or "").rstrip("/")
        self.api_key = api_key

    def is_configured(self) -> bool:
        return bool(self.base_url and self.api_key)

    def fetch(self, *, query: Optional[str] = None, location: Optional[str] = None) -> List[JobRecord]:
        if not self.is_configured():
            print(
                "[info] Tyomarkkinatori adapter skipped: missing TYO_API_BASE_URL or TYO_API_KEY",
                file=sys.stderr,
            )
            return []

        # This path is a placeholder because official access details vary by granted credentials.
        # Update it to match the endpoint documented in your approved API access package.
        url = f"{self.base_url}/jobs"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params: Dict[str, Any] = {}
        if query:
            params["q"] = query
        if location:
            params["location"] = location

        data = self.client.get_json(url, params=params, headers=headers)
        items = self._extract_items(data)
        jobs: List[JobRecord] = []
        for item in items:
            title = self._pick(item, ["title", "heading", "name"])
            company = self._pick(item, ["employer", "company", "organization"])
            url = self._pick(item, ["url", "link", "jobUrl"])
            location_value = self._pick(item, ["location", "city", "municipality"])
            published_at = self._pick(item, ["publishedAt", "published_at", "created_at"])
            deadline = self._pick(item, ["deadline", "expiresAt", "application_deadline"])
            source_job_id = str(self._pick(item, ["id", "uuid", "job_id", "slug"]))
            description = self._pick(item, ["description", "summary", "teaser", "body"])
            language = self._pick(item, ["language", "lang"]) or ""

            if not title and not url:
                continue

            jobs.append(JobRecord(
                source=self.source_name,
                source_job_id=source_job_id,
                title=clean_text(title),
                company=clean_text(company),
                location=clean_text(location_value),
                published_at=clean_text(published_at),
                deadline=clean_text(deadline),
                url=clean_text(url),
                description_snippet=clean_text(description)[:500],
                language=clean_text(language),
                raw=item,
            ))
        return jobs

    @staticmethod
    def _pick(item: Dict[str, Any], keys: Iterable[str]) -> Any:
        for key in keys:
            if key in item and item[key] not in (None, ""):
                return item[key]
        return ""

    @staticmethod
    def _extract_items(data: Any) -> List[Dict[str, Any]]:
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
        if isinstance(data, dict):
            for key in ("jobs", "results", "items", "data"):
                if isinstance(data.get(key), list):
                    return [x for x in data[key] if isinstance(x, dict)]
        return []


class Aggregator:
    def __init__(self, adapters: List[BaseAdapter]) -> None:
        self.adapters = adapters

    def collect(self, *, query: Optional[str] = None, location: Optional[str] = None) -> List[JobRecord]:
        collected: List[JobRecord] = []
        for adapter in self.adapters:
            try:
                records = adapter.fetch(query=query, location=location)
                print(f"[info] {adapter.source_name}: fetched {len(records)} jobs", file=sys.stderr)
                collected.extend(records)
            except Exception as exc:  # noqa: BLE001
                print(f"[warn] {adapter.source_name}: {exc}", file=sys.stderr)
        return deduplicate_jobs(collected)


def deduplicate_jobs(records: List[JobRecord]) -> List[JobRecord]:
    seen: Dict[str, JobRecord] = {}
    for record in records:
        seen.setdefault(record.dedup_key, record)
    jobs = list(seen.values())
    jobs.sort(key=lambda x: (
        normalize_sort_value(x.published_at),
        x.source,
        x.title.lower(),
    ), reverse=True)
    return jobs


def normalize_sort_value(value: str) -> str:
    value = (value or "").strip()
    return value or "0000-00-00T00:00:00"


def export_csv(records: List[JobRecord], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "source",
        "source_job_id",
        "title",
        "company",
        "location",
        "published_at",
        "deadline",
        "url",
        "description_snippet",
        "language",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rec in records:
            row = asdict(rec)
            row.pop("raw", None)
            writer.writerow(row)


def export_jsonl(records: List[JobRecord], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(asdict(rec), ensure_ascii=False) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect public Finland job postings from selected sources.")
    parser.add_argument("--query", type=str, default=None, help="Keyword query, e.g. 'researcher' or 'software engineer'")
    parser.add_argument("--location", type=str, default=None, help="Location filter, e.g. 'Helsinki'")
    parser.add_argument("--out", type=Path, default=Path("jobs.csv"), help="CSV output path")
    parser.add_argument("--jsonl", type=Path, default=Path("jobs.jsonl"), help="JSONL output path")
    parser.add_argument("--disable-tyo", action="store_true", help="Disable Tyomarkkinatori adapter")
    parser.add_argument("--disable-kunta", action="store_true", help="Disable Kuntarekry adapter")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    timeout = int(os.getenv("TYO_API_TIMEOUT", str(DEFAULT_TIMEOUT)))
    client = HttpClient(timeout=timeout)

    adapters: List[BaseAdapter] = []
    if not args.disable_kunta:
        adapters.append(KuntarekryAdapter(client=client))
    if not args.disable_tyo:
        adapters.append(
            TyomarkkinatoriOfficialApiAdapter(
                client=client,
                base_url=os.getenv("TYO_API_BASE_URL"),
                api_key=os.getenv("TYO_API_KEY"),
            )
        )

    aggregator = Aggregator(adapters)
    records = aggregator.collect(query=args.query, location=args.location)

    export_csv(records, args.out)
    export_jsonl(records, args.jsonl)

    summary = {
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        "query": args.query,
        "location": args.location,
        "count": len(records),
        "csv": str(args.out),
        "jsonl": str(args.jsonl),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
