# EuroJobs Backend

This is the Python backend for the EuroJobs platform.

## Setup

```bash
cd backend
pip install -r requirements.txt
```

## Database Setup

```bash
# Create PostgreSQL database
createdb eurojobs

# Initialize tables (run SQL from init.sql)
psql -d eurojobs -f init.sql
```

## Run

```bash
uvicorn main:app --reload --port 8000
```

## API Endpoints

- `GET /api/jobs` - List jobs
- `GET /api/jobs/{id}` - Get job details
- `POST /api/jobs` - Create job
- `POST /api/jobs/{id}/like` - Like a job
- `GET /api/comments?job_id={id}` - Get comments
- `POST /api/comments` - Add comment