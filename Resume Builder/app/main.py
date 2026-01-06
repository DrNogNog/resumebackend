from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os

# Import routers
from app.api.routes import (
    users,
    resume_routes,
    generation,
    auth,
    usage,
    subscriptions,
    webhooks,
    suggestions,
)

# Environment
ENV = os.getenv("ENV", "development")
SECRET_KEY = os.getenv("SECRET_KEY")

# Disable docs in production
if ENV == "production":
    app = FastAPI(
        title="Resume Builder API",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
else:
    app = FastAPI(title="Resume Builder API")

# -------------------------
# CORS configuration - let FastAPI handle it properly
# -------------------------
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://resumesub.xyz",
    "https://www.resumesub.xyz",
]

# In development, allow Vercel preview URLs (all end with .vercel.app)
if ENV != "production":
    origins.append("https://resumefrontend-65glk9ccl-gordonng26-gmailcoms-projects.vercel.app")  # optional: specific preview
    # Or allow all Vercel previews dynamically in middleware below

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# Middleware: Lock /api (API key + origin protection)
# -------------------------
@app.middleware("http")
async def lock_api(request: Request, call_next):
    if request.url.path.startswith("/api"):
        # API key check (keep this for security)
        key = request.headers.get("x-api-key")
        if key != SECRET_KEY:
            raise HTTPException(status_code=403, detail="Forbidden: Invalid API Key")

        # Origin check - strict in production, flexible in development
        origin = request.headers.get("origin")
        if origin:
            allowed = {
                "https://resumesub.xyz",
                "https://www.resumesub.xyz",
                "http://localhost:3000",
                "http://127.0.0.1:3000",
            }
            # Allow all Vercel preview domains in non-production
            if ENV != "production" and (origin.endswith(".vercel.app") or origin in allowed):
                pass
            elif origin not in allowed:
                raise HTTPException(status_code=403, detail="Forbidden: Invalid Origin")

    # Let CORSMiddleware handle OPTIONS preflight - no manual response needed
    return await call_next(request)

# -------------------------
# Routers
# -------------------------
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(resume_routes.router, prefix="/api/resume", tags=["Resume"])
app.include_router(generation.router, prefix="/api/gen", tags=["Generator"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(subscriptions.router, prefix="/api/sub", tags=["Subscribe"])
app.include_router(usage.router, prefix="/api/protected", tags=["Protected"])
app.include_router(webhooks.router, prefix="/api/stripe", tags=["Stripe"])
app.include_router(suggestions.router, prefix="/api/sug", tags=["Suggestions"])