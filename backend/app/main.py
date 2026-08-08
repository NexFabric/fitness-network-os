from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone

def create_app() -> FastAPI:
    app = FastAPI(
        title="Fitness Network OS",
        version="0.1.0",
        description="Core backend for Fitness Network OS"
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health_check():
        return {
            "status": "ok", 
            "timestamp": datetime.now(timezone.utc).isoformat(), 
            "checks": {}
        }

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

    return app

app = create_app()
