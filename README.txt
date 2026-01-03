uvicorn app.main:app --reload

4) TinyTeX / xelatex hosting notes (important) 🧾
For Linux containers use TinyTeX (install in Dockerfile) or install texlive-xetex system package.
For Windows servers (if not containerized) install TinyTeX (via R) or MiKTeX and add xelatex to PATH.
If LaTeX is heavy or security-sensitive, consider offloading PDF generation to:
A separate worker container (Celery/RQ) with its own TeX tooling,
Or a dedicated microservice that runs xelatex, with resource/time limits.
Ensure TEX_BIN is configurable (env var) so you can point to system xelatex or TinyTeX path.
5) Database & file persistence 🗄️
Use Postgres for production and set DB credentials via ENV (not in code).
Store PDFs on a named Docker volume (in Compose) or use S3 and save only the S3 URL in DB (recommended for scale).
6) Windows-specific hosting tips 🪟
Use Docker Desktop (WSL2 backend recommended). Build and run the same Docker images from Windows.
Alternatively use WSL2 to run a Linux environment and docker-compose there.
For a Windows-only host, install Python, Node, and MiKTeX/TinyTeX and run services with PM2/Windows services, but containers are simpler and more reproducible.
7) CI/CD & deployment workflow suggestions
Build images in CI, run tests, push images to container registry (GitHub Packages, Docker Hub, ECR).
Deploy via:
DigitalOcean App Platform, Fly, or Render (simple),
Kubernetes/ECS for large scale, with Helm/manifest,
Or Vercel for frontend + Render for backend is a fast low-maintenance combo.
Add a health check that calls your backend /health and a tiny GET /health/tex that runs xelatex --version with a timeout to validate TeX availability.
8) Security & production hardening 🔐
Use HTTPS (Let’s Encrypt / managed TLS)
Harden CORS and CSRF if needed.
Enforce safe LaTeX options: -no-shell-escape, compile in isolated directory, set a compile timeout and disk/quota limits.
Rotate secrets and store them in a secrets manager (AWS Secrets Manager, GitHub Actions secrets).

---

Windows TinyTeX quick install (recommended):
1. Install R (https://cran.r-project.org/) if you don't have it.
2. In R or RStudio run:
   install.packages("tinytex")
   tinytex::install_tinytex()
3. Ensure TinyTeX is on PATH. Typical install path: %APPDATA%\TinyTeX\bin\win32
   Temporary PowerShell add:
     $env:PATH += ";$env:USERPROFILE\AppData\Roaming\TinyTeX\bin\win32"
   Permanent (cmd):
     setx PATH "%PATH%;C:\Users\<you>\AppData\Roaming\TinyTeX\bin\win32"
4. Install additional packages (in R):
   tinytex::tlmgr_install(c("xetex","collection-xetex","collection-latexrecommended",
                            "collection-latexextra","collection-fontsrecommended",
                            "fontspec","latexmk"))
5. Test:
   xelatex --version
   echo "\\documentclass{article}\\usepackage{fontspec}\\begin{document}Hi\\end{document}" > test.tex
   xelatex -interaction=nonstopmode -halt-on-error -output-directory=out test.tex

Docker Compose (local testing / small production):
- Build & run (using the included docker-compose.yml):
  docker compose build
  docker compose up -d

- The compose setup expects:
  - `frontend/Dockerfile` (exists) and `backend/Dockerfile` (created)
  - nginx config in `nginx/conf/default.conf` (created)
  - a named volume `uploads` is used to persist generated PDFs

Health check:
- App: GET /health returns basic app status
- TeX: GET /gen/health/tex returns the configured TeX binary and version if available. Use this to verify `xelatex` is installed and on PATH.

Notes:
- In production set ENV=production and make sure cookie `secure=True` is used for auth.
- Consider offloading compilation to a separate worker container for scaling and security.
