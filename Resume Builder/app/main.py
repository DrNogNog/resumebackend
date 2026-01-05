from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os

# Import your routers
from app.api.routes import users, resume_routes, generation, auth, usage, subscriptions, webhooks, suggestions

# Environment
ENV = os.getenv("ENV", "development")
SECRET_KEY = os.getenv("SECRET_KEY")  # backend secret key

# Disable docs in production
if ENV == "production":
    app = FastAPI(
        title="Resume Builder API",
        docs_url=None,
        redoc_url=None,
        openapi_url=None
    )
else:
    app = FastAPI(title="Resume Builder API")

# CORS setup (allow dev + production frontend)
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://resumesub.xyz"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Middleware: Lock /api endpoints ---
@app.middleware("http")
async def lock_api(request: Request, call_next):
    # Only enforce on /api routes
    if request.url.path.startswith("/api"):
        # 1️⃣ Check secret key header
        key = request.headers.get("x-api-key")
        if key != SECRET_KEY:
            raise HTTPException(status_code=403, detail="Forbidden: Invalid API Key")

        # 2️⃣ Optional: check Origin header to ensure frontend calls
        allowed_origins = ["https://resumesub.xyz"]
        origin = request.headers.get("origin")
        if origin not in allowed_origins:
            raise HTTPException(status_code=403, detail="Forbidden: Invalid Origin")

    response = await call_next(request)
    return response

# --- Include your routers with /api prefix ---
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(resume_routes.router, prefix="/api/resume", tags=["Resume"])
app.include_router(generation.router, prefix="/api/gen", tags=["Generator"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(subscriptions.router, prefix="/api/sub", tags=["Subscribe"])
app.include_router(usage.router, prefix="/api/protected", tags=["Protected"])
app.include_router(webhooks.router, prefix="/api/stripe", tags=["Stripe"])
app.include_router(suggestions.router, prefix="/api/sug", tags=["Suggestions"])
