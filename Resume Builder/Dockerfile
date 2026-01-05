FROM python:3.11-slim

# Install system dependencies:
# - TinyTeX prerequisites
# - Build tools for compiling Python wheels (many packages in your requirements need this)
# - Git for potential package installs
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        wget \
        ca-certificates \
        bzip2 \
        xz-utils \
        fontconfig \
        fonts-dejavu-core \
        fonts-noto-core \
        unzip \
        perl \
        build-essential \
        gcc \
        g++ \
        python3-dev \
        libffi-dev \
        libssl-dev \
        libcurl4-openssl-dev \
        rustc \
        cargo \
        git && \
    rm -rf /var/lib/apt/lists/*

# Install TinyTeX (user-friendly way, non-root path)
RUN wget -qO- "https://yihui.org/tinytex/install-bin-unix.sh" | sh -s -- --no-path && \
    mv /root/.TinyTeX /opt/TinyTeX && \
    ln -s /opt/TinyTeX/bin/x86_64-linux/tlmgr /usr/local/bin/tlmgr

# Add TinyTeX to PATH and update TeX packages
ENV PATH="/opt/TinyTeX/bin/x86_64-linux:${PATH}"
RUN tlmgr update --self && \
    tlmgr install \
        xetex \
        collection-xetex \
        collection-latexrecommended \
        collection-latexextra \
        collection-fontsrecommended \
        fontspec \
        latexmk

# Set up app directory
WORKDIR /app

# Copy and install Python dependencies with reliability fixes
COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt \
        -i https://pypi.tuna.tsinghua.edu.cn/simple \
        --trusted-host pypi.tuna.tsinghua.edu.cn \
        --default-timeout=1000 \
        --retries=20 \
        --use-deprecated=legacy-resolver

# Optional: Prevent backports.zoneinfo issues on Python 3.11+
# If it's pulled in transitively, this skips it safely
RUN echo "backports.zoneinfo; python_version < '3.9'" >> requirements.txt || true

# Copy application code
COPY app ./app

# Expose port
EXPOSE 8000

# Run the FastAPI app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]