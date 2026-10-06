## main execution file
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.research import router


app = FastAPI(
    title="Research AI API",
    description="AI-powered research workflow API",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router)


@app.get("/")
def root():
    return {
        "message": "Research AI API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


