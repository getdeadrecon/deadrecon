FROM python:3.12-slim

LABEL maintainer="PhantomSignal Community"
LABEL description="PhantomSignal OSINT Framework — See everything. Leave no trace."
LABEL version="1.3.1"

# Core system deps (required)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libffi-dev libssl-dev \
    nmap dnsutils whois curl \
    && rm -rf /var/lib/apt/lists/*

# Optional crawler deps — allowed to fail on minimal base images
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium chromium-driver tesseract-ocr \
    && rm -rf /var/lib/apt/lists/* || \
    (rm -rf /var/lib/apt/lists/* && echo "Optional crawler deps not available — crawling disabled")

WORKDIR /app

# Install Python dependencies (from pre-downloaded wheels for offline build)
COPY requirements.txt .
COPY wheels/ /tmp/wheels/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --no-index --find-links /tmp/wheels/ -r requirements.txt && \
    rm -rf /tmp/wheels/

# Install playwright browsers
RUN playwright install chromium --with-deps 2>/dev/null || true

# Copy application code
COPY . .
RUN pip install --no-cache-dir -e .

# Initialize database
RUN python -c "from phantomsignal.core.database import init_db; init_db()"

# Create exports directory
RUN mkdir -p /app/exports /app/data

EXPOSE 5000

ENV PHANTOMSIGNAL_HOST=0.0.0.0
ENV PHANTOMSIGNAL_PORT=5000
ENV PHANTOMSIGNAL_DB_URL=sqlite:////app/data/phantomsignal.db

VOLUME ["/app/data", "/app/exports"]

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s \
    CMD curl -f http://localhost:5000/api/v1/health || exit 1

CMD ["python", "run.py"]
