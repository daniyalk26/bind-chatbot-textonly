# backend/Dockerfile
FROM python:3.9-slim

WORKDIR /app

# ---- system deps ----
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
 && rm -rf /var/lib/apt/lists/*

# ---- Python deps ----
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# ---- project code ----
COPY . .

# ---- serve ----
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
