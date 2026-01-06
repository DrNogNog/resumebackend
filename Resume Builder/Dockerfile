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

RUN apt-get update && apt-get install -y --no-install-recommends \
    libffi-dev libssl-dev wget ca-certificates fontconfig fonts-dejavu-core perl \
    && rm -rf /var/lib/apt/lists/*

# Install TinyTeX (PDF engine)
RUN wget -qO- "https://yihui.org/tinytex/install-bin-unix.sh" | sh -s -- --no-path && \
    mv /root/.TinyTeX /opt/TinyTeX && \
    ln -s /opt/TinyTeX/bin/x86_64-linux/tlmgr /usr/local/bin/tlmgr

ENV PATH="/opt/TinyTeX/bin/x86_64-linux:${PATH}"

RUN tlmgr update --self && tlmgr install \
    xetex collection-xetex collection-latexrecommended \
    collection-latexextra collection-fontsrecommended fontspec latexmk

WORKDIR /app

# Copy prebuilt wheels from the builder stage (note the stage name `builder`)
COPY --from=builder /build/*.whl /wheels/

# Install all wheels offline
RUN pip install --no-index --find-links=/wheels /wheels/*.whl

# Copy app code
COPY app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
