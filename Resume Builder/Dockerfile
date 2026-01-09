# =========================
# Builder Stage
# =========================
FROM python:3.11-slim AS builder

# Install build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc python3-dev libffi-dev libssl-dev wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy requirements and build wheels
COPY requirements.prod.txt .

RUN pip install --upgrade pip wheel && \
    pip wheel --no-cache-dir -r requirements.prod.txt -w /build

# =========================
# Runtime Stage
# =========================
FROM python:3.11-slim

# --- OS deps + Postgres client + fonts ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    libffi-dev libssl-dev wget ca-certificates fontconfig fonts-dejavu-core \
    cabextract xfonts-utils perl unzip \
    && rm -rf /var/lib/apt/lists/*

# --- Microsoft Core Fonts (Calibri fix) ---
RUN wget -q https://downloads.sourceforge.net/project/corefonts/the%20fonts/final/mscorefonts2.deb && \
    dpkg -i mscorefonts2.deb || apt-get -f install -y && \
    rm -f mscorefonts2.deb && fc-cache -f -v

# --- Install full TeX Live (all needed for your resume template) ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-xetex \
    texlive-latex-recommended \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    latexmk \
    lmodern \
    enumitem \
    xcolor \
    hyperref \
    && rm -rf /var/lib/apt/lists/*

# --- Ensure pg_isready exists ---
RUN which pg_isready && pg_isready --version

# --- App workspace ---
WORKDIR /app

# --- Install Python wheels ---
COPY --from=builder /build/*.whl /wheels/
RUN pip install --no-index --find-links=/wheels /wheels/*.whl

# --- Copy full project ---
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini
COPY app ./app
COPY start.sh ./start.sh

RUN chmod +x ./start.sh

EXPOSE 8000
CMD ["./start.sh"]
