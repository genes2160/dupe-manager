import logging
from fastapi import FastAPI
from app.settings import settings
from app.db import init_db
from app.api import router
from fastapi.staticfiles import StaticFiles


def configure_logging():
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )


configure_logging()
init_db()

app = FastAPI(title=settings.APP_NAME)
app.include_router(router)

app.mount(
    "/",
    StaticFiles(directory="app/frontend", html=True),
    name="frontend"
)