from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import Base, SessionLocal, engine
from .notifications import run_reminder_sweep
from .routers import courses, extract, push, tasks

settings = get_settings()

Base.metadata.create_all(bind=engine)

scheduler = BackgroundScheduler()


def _reminder_sweep_job() -> None:
    db = SessionLocal()
    try:
        run_reminder_sweep(db)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(
        _reminder_sweep_job,
        "interval",
        minutes=settings.notify_interval_minutes,
        id="reminder_sweep",
    )
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="TaskCampus API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(courses.router)
app.include_router(tasks.router)
app.include_router(extract.router)
app.include_router(push.router)


@app.get("/health")
def health():
    return {"status": "ok"}
