FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Expose port
EXPOSE 8000

# Run the app from backend directory
CMD ["python", "-c", "
import sys
sys.path.insert(0, '.')
import uvicorn
uvicorn.run('main:app', host='0.0.0.0', port=8000)
"]