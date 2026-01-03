from fastapi import FastAPI
from app.api.routes import users, resume_routes, generation, auth,usage, subscriptions, webhooks, suggestions  # must match folder structure
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Resume Builder API")

origins = [
    "http://localhost:3000",  # React dev server
    "http://127.0.0.1:3000",
    "https://plotbreaks.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # allow POST, OPTIONS, etc.
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(resume_routes.router,prefix="/resume", tags=["Resume"])
app.include_router(generation.router,prefix="/gen",tags=["Generator"])
app.include_router(auth.router,prefix="/auth", tags=["Authentication"])
app.include_router(subscriptions.router,prefix="/sub",tags=["Subscribe"])
app.include_router(usage.router,prefix="/protected", tags=["Protected"])
app.include_router(webhooks.router,prefix="/stripe",tags=["Stripe"])
app.include_router(suggestions.router, prefix="/sug", tags=["Suggestions"])

