"""
MedAudit Backend API
FastAPI application for medical audit system
"""
from fastapi import FastAPI
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = FastAPI(
    title="MedAudit Backend API",
    description="Medical audit system backend",
    version="0.1.0"
)

@app.get("/")
async def root():
    return {"message": "MedAudit Backend API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
