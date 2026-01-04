FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    wget ca-certificates bzip2 xz-utils fontconfig fonts-dejavu-core \
    fonts-noto-core unzip perl build-essential && rm -rf /var/lib/apt/lists/*

RUN wget -qO- "https://yihui.org/tinytex/install-bin-unix.sh" | sh -s --
ENV PATH="/root/.TinyTeX/bin/x86_64-linux:${PATH}"

RUN tlmgr update --self && \
    tlmgr install xetex collection-xetex collection-latexrecommended \
      collection-latexextra collection-fontsrecommended fontspec latexmk

WORKDIR /app

# COPY FROM backend FOLDER
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
