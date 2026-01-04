FROM python:3.11-slim

# system deps + fonts + tools for TinyTeX
RUN apt-get update && apt-get install -y \
    wget ca-certificates bzip2 xz-utils fontconfig fonts-dejavu-core \
    fonts-noto-core unzip perl build-essential && rm -rf /var/lib/apt/lists/*

# Install TinyTeX
RUN wget -qO- "https://yihui.org/tinytex/install-bin-unix.sh" | sh -s --
ENV PATH="/root/.TinyTeX/bin/x86_64-linux:${PATH}"

# tlmgr installs for xelatex support
RUN tlmgr update --self && \
    tlmgr install xetex collection-xetex collection-latexrecommended \
      collection-latexextra collection-fontsrecommended fontspec latexmk

WORKDIR /app

# Copy requirements FIRST (better layer caching)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application code
COPY ./app /app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
