from fastapi import FastAPI, Request, HTTPException, Response
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
# CORS configuration
# -------------------------
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://www.resumesub.xyz",  # frontend origin
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# Middleware: Lock /api
# -------------------------
@app.middleware("http")
async def lock_api(request: Request, call_next):
    # ✅ Handle preflight OPTIONS immediately
    if request.method == "OPTIONS":
        # Return proper CORS headers for preflight
        response = Response(status_code=204)
        response.headers["Access-Control-Allow-Origin"] = "https://www.resumesub.xyz"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-API-Key"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response

    if request.url.path.startswith("/api"):
        # API key check
        key = request.headers.get("x-api-key")
        if key != SECRET_KEY:
            raise HTTPException(status_code=403, detail="Forbidden: Invalid API Key")

        # Origin check
        allowed_origins = {"https://www.resumesub.xyz"}
        origin = request.headers.get("origin")
        if origin not in allowed_origins:
            raise HTTPException(status_code=403, detail="Forbidden: Invalid Origin")

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
