from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from app.api.v1.reviews import ReviewRouter

app = FastAPI(
    title="TeamBlind Data Scraper API",
    description="",
    version="1.0.0"
)
app.include_router(ReviewRouter, prefix="/api/v1")


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")