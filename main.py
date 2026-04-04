from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from routes import whatsapp

app = FastAPI(
    title="Karigar AI API",
    description="AI-powered voice learning platform for blue collar workers",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(whatsapp.router, prefix="/webhook", tags=["WhatsApp"])

@app.get("/")
def root():
    return {
        "app": "Karigar AI",
        "status": "running",
        "message": "Empowering blue collar workers through voice-based learning"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
