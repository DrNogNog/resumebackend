# =========================
# Builder Stage
# =========================
FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc python3-dev libffi-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY requirements.prod.txt .

RUN pip install --upgrade pip wheel && \
    pip wheel --no-cache-dir -r requirements.prod.txt -w /build


# =========================
# Runtime Stage
# =========================
FROM python:3.11-slim

# --- OS + postgres client ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    libffi-dev libssl-dev wget ca-certificates fontconfig fonts-dejavu-core perl \
    && rm -rf /var/lib/apt/lists/*

# --- Ensure pg_isready exists ---
RUN which pg_isready && pg_isready --version

# --- Install TinyTeX ---
RUN wget -qO- "https://yihui.org/tinytex/install-bin-unix.sh" | sh -s -- --no-path && \
    mv /root/.TinyTeX /opt/TinyTeX && \
    ln -s /opt/TinyTeX/bin/x86_64-linux/tlmgr /usr/local/bin/tlmgr

ENV PATH="/opt/TinyTeX/bin/x86_64-linux:${PATH}"

RUN tlmgr update --self && tlmgr install \
    xetex collection-xetex collection-latexrecommended \
    collection-latexextra collection-fontsrecommended fontspec latexmk

# --- App workspace ---
WORKDIR /app

# --- Install Python wheels ---
COPY --from=builder /build/*.whl /wheels/
RUN pip install --no-index --find-links=/wheels /wheels/*.whl

# --- Copy full project (FIXES alembic.ini missing) ---
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini
COPY app ./app
COPY start.sh ./start.sh

RUN chmod +x ./start.sh

EXPOSE 8000
CMD ["./start.sh"]
