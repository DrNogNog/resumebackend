from fastapi import FastAPI, Request, HTTPException
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

# CORS (unchanged)
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
# Fixed Middleware: Return JSONResponse instead of raising
# -------------------------
@app.middleware("http")
async def lock_api(request: Request, call_next):
    if request.url.path.startswith("/api"):
        # API key check
        key = request.headers.get("x-api-key")
        if key != SECRET_KEY:
            return JSONResponse(
                status_code=403,
                content={"detail": "Forbidden: Invalid API Key"}
            )

        # Origin check
        origin = request.headers.get("origin")
        if origin:
            # Allow exact production domains
            if origin in base_origins:
                pass
            # Allow any Vercel preview/deploy
            elif "vercel.app" in origin:
                pass
            # Allow localhost variants
            elif origin.startswith("http://localhost") or origin.startswith("http://127.0.0.1"):
                pass
            # Block everything else in production
            elif ENV == "production":
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Forbidden: Invalid Origin"}
                )
            else:
                # In development: allow unknown origins (optional – remove if you want strict)
                pass
        # If no origin header (e.g., curl, Postman), allow if key is valid
        # (you can block these too if desired)

    # Proceed to route handler
    response = await call_next(request)
    return response

# -------------------------
# Routers (unchanged)
# -------------------------
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(resume_routes.router, prefix="/api/resume", tags=["Resume"])
app.include_router(generation.router, prefix="/api/gen", tags=["Generator"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(subscriptions.router, prefix="/api/sub", tags=["Subscribe"])
app.include_router(usage.router, prefix="/api/protected", tags=["Protected"])
app.include_router(webhooks.router, prefix="/api/stripe", tags=["Stripe"])
app.include_router(suggestions.router, prefix="/api/sug", tags=["Suggestions"])