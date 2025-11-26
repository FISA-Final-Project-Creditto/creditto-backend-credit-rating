from fastapi import FastAPI
from app.api.scoring import router as score_router

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Credit Rating API Server Running"}


# score 라우터 연결
app.include_router(score_router, prefix="/api/credit-score", tags=["Scoring Credit Rating"])
