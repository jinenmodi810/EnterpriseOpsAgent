from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes.health import router as health_router
from .routes.analyze import router as analyze_router
from .routes.predict import router as predict_router
from .routes.recommend import router as recommend_router
from .routes.explain_hypothesis import router as explain_router
from .core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    # ---------------------------------------------------------
    # ✅ Add CORS middleware
    # ---------------------------------------------------------
    app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",          # ✅ local Next.js dev
        "http://127.0.0.1:3000",          # ✅ alternative localhost form
        "https://enterprise-ops-agent.vercel.app",  # ✅ production URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

    # ---------------------------------------------------------
    # ✅ Register all routers
    # ---------------------------------------------------------
    app.include_router(health_router, prefix=f"{settings.api_v1_prefix}/health")
    app.include_router(analyze_router, prefix=f"{settings.api_v1_prefix}/analyze")
    app.include_router(explain_router, prefix="/explain-hypothesis")
    app.include_router(predict_router, prefix=f"{settings.api_v1_prefix}/predict")
    app.include_router(recommend_router, prefix=f"{settings.api_v1_prefix}/recommend")

    return app


app = create_app()