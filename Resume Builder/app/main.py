from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# Import your routers
from app.api.routes import users, resume_routes, generation, auth, usage, subscriptions, webhooks, suggestions

# Check environment
ENV = os.getenv("ENV", "development")

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

# CORS setup
origins = [
    "http://localhost:3000",    # React dev server
    "http://127.0.0.1:3000",
    "https://resumesub.xyz"     # production frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prefix all routes with /api for consistent proxying
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(resume_routes.router, prefix="/api/resume", tags=["Resume"])
app.include_router(generation.router, prefix="/api/gen", tags=["Generator"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(subscriptions.router, prefix="/api/sub", tags=["Subscribe"])
app.include_router(usage.router, prefix="/api/protected", tags=["Protected"])
app.include_router(webhooks.router, prefix="/api/stripe", tags=["Stripe"])
app.include_router(suggestions.router, prefix="/api/sug", tags=["Suggestions"])
