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
# CORS configuration - expanded and flexible
# -------------------------
base_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://resumesub.xyz",
    "https://www.resumesub.xyz",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=base_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# Middleware: Lock /api (API key + smart origin protection)
# -------------------------
@app.middleware("http")
async def lock_api(request: Request, call_next):
    if request.url.path.startswith("/api"):
        # API key check - keep this for security
        key = request.headers.get("x-api-key")
        if key != SECRET_KEY:
            raise HTTPException(status_code=403, detail="Forbidden: Invalid API Key")

        # Origin check - fixed indentation and logic
        origin = request.headers.get("origin")
        if origin:
            # Allow exact production domains
            if origin in base_origins:
                return await call_next(request)

            # Allow ANY Vercel origin (preview or production)
            if "vercel.app" in origin:
                return await call_next(request)

            # Allow localhost variants
            if origin.startswith("http://localhost") or origin.startswith("http://127.0.0.1"):
                return await call_next(request)

            # In production, block anything else
            if ENV == "production":
                raise HTTPException(status_code=403, detail="Forbidden: Invalid Origin")
            # In development, optionally allow all (for testing)
            # remove the line below if you want strict in dev too
            # return await call_next(request)

            raise HTTPException(status_code=403, detail="Forbidden: Invalid Origin")

    # Proceed if not /api path
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