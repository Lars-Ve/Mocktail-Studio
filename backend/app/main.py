from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .database import Base, engine, SessionLocal
from .seed_data import seed_defaults
from .routes.pages import router as pages_router
from .routes.api import router as api_router


app = FastAPI(title="Mocktail Studio")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(pages_router)
app.include_router(api_router)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_defaults(db)
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok", "app": "Mocktail Studio"}
