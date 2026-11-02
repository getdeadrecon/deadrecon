FROM python:3.12-slim

LABEL maintainer="PhantomSignal Community"
LABEL description="PhantomSignal OSINT Framework — See everything. Leave no trace."

# Core system deps (required)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libffi-dev libssl-dev \
    nmap dnsutils whois curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .
RUN pip install --no-cache-dir -e .

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
