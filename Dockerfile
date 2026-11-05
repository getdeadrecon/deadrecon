FROM python:3.12-slim

LABEL maintainer="DeadRecon Community"
LABEL description="DeadRecon OSINT Framework"

# nmap gets only the raw-socket capability it needs for SYN scans and OS detection,
# so the app itself can run without root.
RUN apt-get update && apt-get install -y --no-install-recommends \
    nmap dnsutils whois curl libcap2-bin tor \
    && setcap cap_net_raw+eip "$(command -v nmap)" \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Hash-pinned dependencies. Regenerate requirements.lock as described in CONTRIBUTING.md.
COPY requirements.lock .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --require-hashes -r requirements.lock

COPY . .
RUN pip install --no-cache-dir --no-deps .

# Optional Go recon tools (nuclei, katana, subfinder, naabu, tlsx). Adds about 500 MB.
# docker build --build-arg RECON_TOOLS=true .
ARG RECON_TOOLS=false
RUN if [ "$RECON_TOOLS" = "true" ]; then sh /app/scripts/install_recon_tools.sh; fi

RUN useradd --create-home --uid 10001 app \
    && mkdir -p /app/exports /app/data /home/app/.deadrecon \
    && chown -R app:app /app/exports /app/data /home/app/.deadrecon

EXPOSE 5000

ENV DEADRECON_DB_URL=sqlite:////app/data/deadrecon.db
ENV NMAP_PRIVILEGED=1

VOLUME ["/app/data", "/app/exports"]

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s \
    CMD curl -f http://localhost:5000/api/v1/health || exit 1

USER app

# Baked in so a scan never has to fetch templates, which would bypass a proxy.
RUN if command -v nuclei >/dev/null; then nuclei -update-templates -silent; fi

# One worker: scans and Socket.IO rooms live in this process.
CMD ["gunicorn", "--worker-class", "gthread", "--workers", "1", "--threads", "100", \
     "--bind", "0.0.0.0:5000", "--access-logfile", "-", \
     "deadrecon.web.app:create_app()"]
