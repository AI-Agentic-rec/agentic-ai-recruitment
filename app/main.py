from fastapi import FastAPI

from app.api.offers import router as offers_router


app = FastAPI(title="Agentic AI Recruitment API", version="0.1.0")
app.include_router(offers_router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}
