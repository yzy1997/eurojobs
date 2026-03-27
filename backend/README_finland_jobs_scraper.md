# Finland jobs scraper — minimal first version

This is a conservative first version focused on compliance and maintainability.

Included:
- Kuntarekry public JSON source
- Tyomarkkinatori official API adapter placeholder
- Unified schema
- Deduplication
- CSV + JSONL export

## Run

```bash
python finland_jobs_scraper.py --query researcher --location Helsinki --out jobs.csv --jsonl jobs.jsonl
```

## Tyomarkkinatori official API

When you get official access credentials, set:

```bash
export TYO_API_BASE_URL='https://...'
export TYO_API_KEY='your_token_here'
```

Then update the placeholder path in `TyomarkkinatoriOfficialApiAdapter.fetch()` if your approved API package uses a different endpoint than `/jobs`.

## Output fields

- source
- source_job_id
- title
- company
- location
- published_at
- deadline
- url
- description_snippet
- language

## Next good steps

1. Add incremental persistence with SQLite.
2. Add Valtiolle adapter.
3. Add field-level normalization for dates and locations.
4. Add scheduled runs and alerting.
5. Add a small FastAPI backend and search UI.
