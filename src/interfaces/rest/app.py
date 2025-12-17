# FastAPI app factory
from fastapi import FastAPI
from src.configuration.loader import get_config
from src.interfaces.rest.routes import (
    ingestion,
    query,
    articles,
    health,
    stats
)
from src.interfaces.rest.dependencies import setup_dependencies

def create_app() -> FastAPI:
    """FastAPI application factory."""
    config = get_config()
    
    app = FastAPI(
        title=config.api.title,
        description=config.api.description,
        version=config.api.version
    )
    
    # Setup dependency injection
    setup_dependencies(app)
    
    # Include routers
    app.include_router(ingestion.router, prefix="/api", tags=["Ingestion"])
    app.include_router(query.router, prefix="/api", tags=["Query"])
    app.include_router(articles.router, prefix="/api", tags=["Articles"])
    app.include_router(health.router, prefix="/api", tags=["Health"])
    app.include_router(stats.router, prefix="/api", tags=["Stats"])
    
    return app

app = create_app()