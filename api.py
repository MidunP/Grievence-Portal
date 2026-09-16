"""
Phase 8: FastAPI API Service.
Wraps all grievance models behind standardized REST API endpoints.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

from pipeline import pipeline_instance

if FASTAPI_AVAILABLE:
    app = FastAPI(
        title="Grievance AI Multilingual Intelligence API",
        description="AI model layer for complaint classification, duplicate detection, priority scoring, and department routing across English, Hindi, and Tamil.",
        version="1.0.0"
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Input Schemas
    class TextRequest(BaseModel):
        text: str = Field(..., example="Main water pipeline burst near Church Street.")

    class DuplicateCheckRequest(BaseModel):
        text: str = Field(..., example="Water pipeline leaking heavily near Church Street.")
        category: Optional[str] = Field(None, example="Water Supply & Quality")

    class PriorityRequest(BaseModel):
        text: str = Field(..., example="Transformer spark and power cut in block A.")
        language: str = Field("en", example="en")
        category: str = Field("Electricity & Power Cut", example="Electricity & Power Cut")
        days_open: int = Field(0, example=2)

    class RouteRequest(BaseModel):
        category: str = Field(..., example="Roads & Potholes")
        text: str = Field("", example="Potholes near highway")

    class FullProcessRequest(BaseModel):
        text: str = Field(..., example="वार्ड 10 में कचरा जमा हो गया है और बदबू आ रही है।")
        area: Optional[str] = Field("Gandhi Chowk", example="Gandhi Chowk")
        days_open: Optional[int] = Field(0, example=0)


    @app.on_event("startup")
    def startup_event():
        pipeline_instance.initialize()

    @app.get("/health")
    def health_check():
        return {
            "status": "online",
            "pipeline_initialized": pipeline_instance.is_initialized,
            "supported_languages": ["en", "hi", "ta"]
        }

    @app.post("/detect-language")
    def detect_lang_endpoint(req: TextRequest):
        from models.language_detector import detect_language
        return detect_language(req.text)

    @app.post("/classify")
    def classify_endpoint(req: TextRequest):
        if not pipeline_instance.is_initialized:
            pipeline_instance.initialize()
        return pipeline_instance.classifier.predict(req.text)

    @app.post("/duplicate-check")
    def duplicate_endpoint(req: DuplicateCheckRequest):
        if not pipeline_instance.is_initialized:
            pipeline_instance.initialize()
        return pipeline_instance.duplicate_detector.check_duplicate(req.text, req.category)

    @app.post("/priority")
    def priority_endpoint(req: PriorityRequest):
        return pipeline_instance.priority_predictor.predict_priority(
            text=req.text,
            language=req.language,
            category=req.category,
            days_open=req.days_open
        )

    @app.post("/route")
    def route_endpoint(req: RouteRequest):
        return pipeline_instance.router.route_complaint(req.category, req.text)

    @app.post("/process-grievance")
    def process_grievance_endpoint(req: FullProcessRequest):
        return pipeline_instance.process_grievance(
            text=req.text,
            area=req.area or "Unknown",
            days_open=req.days_open or 0
        )
else:
    app = None
    print("FastAPI is not installed yet. Run `pip install fastapi uvicorn` to launch server.")


if __name__ == "__main__":
    if FASTAPI_AVAILABLE:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        print("FastAPI not installed.")
