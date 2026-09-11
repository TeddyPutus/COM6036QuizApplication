import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import auth, quizzes, attempts

app = FastAPI(
    title="Online Assessment Platform - Application Tier API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration allowing Presentation Tier (SPA) ingress
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules under /api/v1
API_PREFIX = "/api/v1"
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(quizzes.router, prefix=API_PREFIX)
app.include_router(attempts.router, prefix=API_PREFIX)


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for load balancers / container probes."""
    return {"status": "ok", "tier": "application"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        # reload=True,
    )