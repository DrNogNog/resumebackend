from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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

# CORS
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
# Middleware: API Protection with Public Auth Bypass
# -------------------------
@app.middleware("http")
async def lock_api(request: Request, call_next):
    if request.url.path.startswith("/api"):
        # === PUBLIC AUTH ENDPOINTS - NO KEY REQUIRED ===
        # Allow signup, login, verify, password reset, etc.
        if request.url.path.startswith("/api/auth/"):
            response = await call_next(request)
            return response

        # === PROTECTED ENDPOINTS - REQUIRE API KEY ===
        key = request.headers.get("x-api-key")
        if key != SECRET_KEY:
            return JSONResponse(
                status_code=403,
                content={"detail": "Forbidden: Invalid API Key"}
            )

        # === ORIGIN CHECK (for protected endpoints) ===
        origin = request.headers.get("origin")
        if origin:
            if origin in base_origins:
                pass
            elif "vercel.app" in origin:
                pass
            elif origin.startswith("http://localhost") or origin.startswith("http://127.0.0.1"):
                pass
            elif ENV == "production":
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Forbidden: Invalid Origin"}
                )
            # In dev: allow unknown origins

    # Proceed for non-/api routes or allowed cases
    response = await call_next(request)
    return response

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