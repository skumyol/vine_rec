FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Base system deps for OpenCV + curl/wget
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    wget \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install -r requirements.txt

# Playwright WebKit + its system dependencies (the code uses webkit, not chromium)
RUN python -m playwright install --with-deps webkit

# Pre-warm EasyOCR models so cold start in prod is fast
RUN python -c "import easyocr; easyocr.Reader(['en','fr','de','it'], gpu=False)"

# App
COPY app/ ./app/

RUN mkdir -p /app/data/cache /app/data/images/original /app/data/images/processed /app/data/images/crops /app/data/results

EXPOSE 8000

# Single worker keeps the shared Playwright browser + EasyOCR reader as one process.
# Use --workers 2 only if you have plenty of RAM (each worker = own browser + OCR model).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
