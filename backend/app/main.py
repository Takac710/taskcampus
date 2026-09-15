from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import Base, engine
from .routers import courses, extract, tasks

settings = get_settings()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="TaskCampus API", version="0.1.0")

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


@app.get("/health")
def health():
    return {"status": "ok"}
