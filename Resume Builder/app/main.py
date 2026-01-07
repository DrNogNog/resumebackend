from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
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
    # === ALLOW OPTIONS PREFLIGHT IMMEDIATELY (CORS) ===
    if request.method == "OPTIONS":
        # Fast response with CORS headers
        response = Response(status_code=204)
        response.headers["Access-Control-Allow-Origin"] = request.headers.get("origin", "*")
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-API-Key"
        response.headers["Vary"] = "Origin"
        return response

    if request.url.path.startswith("/api"):
        # Public auth endpoints - no key required
        if request.url.path.startswith("/api/auth/"):
            response = await call_next(request)
            return response

        # Protected endpoints - require key
        key = request.headers.get("x-api-key")
        if key != SECRET_KEY:
            return JSONResponse(
                status_code=403,
                content={"detail": "Forbidden: Invalid API Key"}
            )

        # Origin check for protected
        origin = request.headers.get("origin")
        if origin:
            if origin not in base_origins and "vercel.app" not in origin and not (origin.startswith("http://localhost") or origin.startswith("http://127.0.0.1")):
                if ENV == "production":
                    return JSONResponse(
                        status_code=403,
                        content={"detail": "Forbidden: Invalid Origin"}
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