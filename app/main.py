from fastapi import FastAPI
from app.api.v1 import user
from app.api.v1 import extract
from app.api.v1 import ai

app = FastAPI()
app.include_router(user.router, prefix="/api/v1", tags=["Protected"])
app.include_router(extract.router, prefix="/api/v1", tags=["Public"])
app.include_router(ai.router, prefix="/api/v1", tags=["Protected"])