"""
FastAPI application for lead scoring predictions
"""

import os
import logging
from typing import Dict, List, Optional
from datetime import datetime

import mlflow
import numpy as np
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import redis.asyncio as redis
from prometheus_fastapi_instrumentator import Instrumentator

from .routers import predict, health
from monitoring.drift_detection import DataDriftDetector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="RAKEZ Lead Scoring API",
    description="Real-time lead scoring predictions",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add routers
app.include_router(predict.router, prefix="/v1", tags=["predictions"])
app.include_router(health.router, prefix="/health", tags=["health"])

# Initialize Prometheus metrics
instrumentator = Instrumentator().instrument(app)

# Global variables
model = None
drift_detector = None
redis_client = None

class LeadData(BaseModel):
    """Lead data schema for prediction"""
    lead_id: str = Field(..., description="Unique lead identifier")
    company_size: str = Field(..., description="Size of company")
    industry: str = Field(..., description="Industry category")
    website_visits: int = Field(..., description="Number of website visits")
    time_on_site_avg: float = Field(..., description="Average time on site")
    downloads_count: int = Field(..., description="Number of downloads")
    contact_form_filled: int = Field(..., description="Contact form submitted")
    email_open_rate: float = Field(..., description="Email open rate")
    days_since_first_contact: float = Field(..., description="Days since first contact")
    previous_interactions: int = Field(..., description="Previous interactions count")
    lead_source: str = Field(..., description="Source of the lead")
    
    class Config:
        schema_extra = {
            "example": {
                "lead_id": "lead_12345",
                "company_size": "11-50",
                "industry": "Technology",
                "website_visits": 25,
                "time_on_site_avg": 320.5,
                "downloads_count": 3,
                "contact_form_filled": 1,
                "email_open_rate": 0.42,
                "days_since_first_contact": 5,
                "previous_interactions": 4,
                "lead_source": "Website"
            }
        }

class PredictionResponse(BaseModel):
    """Prediction response schema"""
    lead_id: str
    prediction: int
    probability: float
    score_category: str
    model_version: str
    timestamp: datetime
    features_used: List[str]
    latency_ms: float

async def get_model():
    """Dependency to get model instance"""
    global model
    if model is None:
        model = load_production_model()
    return model

async def get_redis():
    """Dependency to get Redis client"""
    global redis_client
    if redis_client is None:
        redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            decode_responses=True
        )
    return redis_client

def load_production_model():
    """Load production model from MLflow registry"""
    try:
        model_uri = f"models:/{os.getenv('MODEL_NAME', 'lead_scoring')}/Production"
        model = mlflow.pyfunc.load_model(model_uri)
        logger.info(f"Loaded model from {model_uri}")
        return model
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise HTTPException(status_code=500, detail="Model loading failed")

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    # Load model
    global model
    model = load_production_model()
    
    # Initialize drift detector
    global drift_detector
    drift_detector = DataDriftDetector()
    
    # Setup Prometheus
    instrumentator.expose(app)
    
    logger.info("Lead Scoring API started successfully")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "RAKEZ Lead Scoring API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "predict": "/v1/predict",
            "batch_predict": "/v1/predict/batch",
            "health": "/health",
            "metrics": "/metrics"
        }
    }

@app.middleware("http")
async def add_process_time_header(request, call_next):
    """Middleware to add processing time header"""
    import time
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("ENV", "development") == "development"
    )
