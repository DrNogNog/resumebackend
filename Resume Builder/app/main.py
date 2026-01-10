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
    # Allow preflight OPTIONS for all paths
    if request.method == "OPTIONS":
        # Always return 200 OK for preflight
        response = JSONResponse(status_code=200, content={"detail": "Preflight"})
        response.headers["Access-Control-Allow-Origin"] = request.headers.get("origin", "*")
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Authorization,Content-Type,x-api-key"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response

    # API key checks for /api (skip /api/auth)
    if request.url.path.startswith("/api") and not request.url.path.startswith("/api/auth/"):
        key = request.headers.get("x-api-key")
        if key != SECRET_KEY:
            return JSONResponse(status_code=403, content={"detail": "Forbidden: Invalid API Key"})

        origin = request.headers.get("origin")
        base_origins = [
            "https://resumesub.xyz",
            "https://www.resumesub.xyz",
            "https://resumefrontend-65glk9ccl-gordonng26-gmailcoms-projects.vercel.app",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
        if origin and origin not in base_origins:
            return JSONResponse(status_code=403, content={"detail": "Forbidden: Invalid Origin"})

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
