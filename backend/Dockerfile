FROM python:3.11-slim

# System deps for OCR + Playwright
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browser for Crawl4AI stealth mode
RUN playwright install chromium --with-deps

# Copy backend source
COPY . .

# Copy agents (mounted via volume in dev, copied in prod)
COPY ../agents ./agents

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
