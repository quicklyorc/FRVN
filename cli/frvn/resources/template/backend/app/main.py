from fastapi import FastAPI

from .core.config import settings
from .core.logging import configure_logging

app = FastAPI(title=settings.project_name)
configure_logging()


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def root() -> dict[str, str]:
    return {"service": settings.project_name, "env": settings.env}



