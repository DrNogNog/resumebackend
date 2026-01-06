# =========================
# Runtime Stage (Minimal PDF + Python runtime)
# =========================
FROM python:3.11-slim

# Install runtime deps + minimal LaTeX dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libffi-dev libssl-dev wget ca-certificates fontconfig \
    fonts-dejavu-core perl bzip2 xz-utils unzip curl \
    && rm -rf /var/lib/apt/lists/*

# -------------------------
# Install TinyTeX (minimal PDF engine)
# -------------------------
RUN wget -qO- "https://yihui.org/tinytex/install-bin-unix.sh" | sh -s -- --no-path --admin --no-doc && \
    mv /root/.TinyTeX /opt/TinyTeX

ENV PATH="/opt/TinyTeX/bin/x86_64-linux:${PATH}"

# Minimal essential packages
RUN tlmgr update --self && tlmgr install \
    xetex latexmk fontspec && \
    tlmgr clean --all

# Enable on-demand package installation
RUN echo "export PATH=/opt/TinyTeX/bin/x86_64-linux:\$PATH" >> /etc/profile.d/tinytex.sh && \
    echo "export TEXMFHOME=/app/texmf" >> /etc/profile.d/tinytex.sh && \
    echo "export TEXLIVE_INSTALLER_EXTRA_OPTIONS='--no-interaction'" >> /etc/profile.d/tinytex.sh

# Helper script to automatically install missing packages
RUN mkdir -p /usr/local/bin && \
    echo '#!/bin/sh\n\
tlmgr install --reinstall "$1"\n\
exec "$@"' > /usr/local/bin/tlmgr-wrapper && \
    chmod +x /usr/local/bin/tlmgr-wrapper

# -------------------------
# Cleanup unnecessary packages
# -------------------------
RUN apt-get purge -y --auto-remove wget curl bzip2 xz-utils unzip perl && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /app

# Copy prebuilt wheels from builder
COPY --from=builder /wheels /wheels

# Install all wheels offline
RUN pip install --no-index --find-links=/wheels /wheels/*.whl && rm -rf /wheels

# Copy application
COPY app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
