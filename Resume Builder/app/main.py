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

# -------------------------
# Environment
# -------------------------
ENV = os.getenv("ENV", "development")
SECRET_KEY = os.getenv("SECRET_KEY")

# -------------------------
# FastAPI instance
# -------------------------
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
base_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://resumesub.xyz",
    "https://www.resumesub.xyz",
    "https://resumefrontend-65glk9ccl-gordonng26-gmailcoms-projects.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=base_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# Middleware: API key protection
# -------------------------
@app.middleware("http")
async def lock_api(request: Request, call_next):
    # Always allow preflight OPTIONS requests to pass
    if request.method == "OPTIONS":
        # Return an empty 200 response with CORS headers (or just pass to CORSMiddleware)
        return await call_next(request)

    if request.url.path.startswith("/api"):
        # Public auth endpoints - no key required
        if request.url.path.startswith("/api/auth/"):
            return await call_next(request)

        # Protected endpoints - require API key
        key = request.headers.get("x-api-key")
        if key != SECRET_KEY:
            return JSONResponse(
                status_code=403,
                content={"detail": "Forbidden: Invalid API Key"},
            )

        # Optional origin check
        origin = request.headers.get("origin")
        if origin:
            if origin not in base_origins and "vercel.app" not in origin and not (
                origin.startswith("http://localhost") or origin.startswith("http://127.0.0.1")
            ):
                if ENV == "production":
                    return JSONResponse(
                        status_code=403,
                        content={"detail": "Forbidden: Invalid Origin"},
                    )

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
