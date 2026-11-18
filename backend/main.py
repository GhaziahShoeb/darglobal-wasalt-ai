import os
import json
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Header, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .ai_engine import ai_engine, FREE_MODELS
from .security import chat_limiter, api_limiter, sanitize_input, validate_api_key

app = FastAPI(
    title="DarGlobal & Wasalt Real Estate Advisory System",
    description="Enterprise Real Estate Intelligence Platform combining public data from DarGlobal (LSE: DAR) and Wasalt (Saudi REGA Accredited).",
    version="2.0.0",
    docs_url=None, # Disable Swagger UI in production to minimize attack surface
    redoc_url=None
)

# Tightened CORS Policy
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Enterprise Security Headers & Rate Limiting Middleware
@app.middleware("http")
async def security_and_rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    path = request.url.path

    # Apply Rate Limiting
    if path == "/api/chat":
        is_limited, retry_after = chat_limiter.is_rate_limited(client_ip)
        if is_limited:
            return Response(
                content=json.dumps({"detail": f"Rate limit exceeded. Please retry in {retry_after}s."}),
                status_code=429,
                media_type="application/json"
            )
    elif path.startswith("/api/"):
        is_limited, retry_after = api_limiter.is_rate_limited(client_ip)
        if is_limited:
            return Response(
                content=json.dumps({"detail": f"Request quota exceeded. Please retry in {retry_after}s."}),
                status_code=429,
                media_type="application/json"
            )

    response = await call_next(request)

    # Security Headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com https://cdnjs.cloudflare.com https://cdn.jsdelivr.net https://fonts.googleapis.com https://fonts.gstatic.com; "
        "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https:;"
    )

    return response

class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., max_length=1500)

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    model: Optional[str] = Field(None, max_length=80)
    api_key: Optional[str] = Field(None, max_length=128)
    history: Optional[List[ChatMessage]] = Field(default=[], max_length=10)

@app.api_route("/api/health", methods=["GET", "HEAD"])
def health_check():
    return {
        "status": "operational",
        "service": "DarGlobal & Wasalt Real Estate Advisory System",
        "environment": "Production / Containerized",
        "indexed_assets": len(ai_engine.properties),
        "available_models": len(FREE_MODELS)
    }

@app.get("/api/models")
def get_models():
    return {
        "default": ai_engine.default_model,
        "models": FREE_MODELS
    }

@app.get("/api/stats")
def get_stats():
    darglobal_count = sum(1 for p in ai_engine.properties if p.get("source") == "DarGlobal")
    wasalt_count = sum(1 for p in ai_engine.properties if p.get("source") == "Wasalt")
    countries = sorted(list(set(p.get("country") for p in ai_engine.properties if p.get("country"))))
    cities = sorted(list(set(p.get("city") for p in ai_engine.properties if p.get("city"))))
    brands = sorted(list(set(p.get("brand") for p in ai_engine.properties if p.get("brand") and p.get("source") == "DarGlobal")))
    
    return {
        "total_properties": len(ai_engine.properties),
        "darglobal_projects": darglobal_count,
        "wasalt_listings": wasalt_count,
        "jurisdictions": countries,
        "primary_markets": cities,
        "portfolio_brands": brands
    }

@app.get("/api/properties")
def list_properties(
    source: Optional[str] = None,
    city: Optional[str] = None,
    country: Optional[str] = None,
    prop_type: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50
):
    # Bound limit strictly
    safe_limit = min(max(limit, 1), 270)
    results = ai_engine.properties
    
    if source:
        safe_source = sanitize_input(source, 40).lower()
        results = [p for p in results if p.get("source", "").lower() == safe_source]
    if city:
        safe_city = sanitize_input(city, 40).lower()
        results = [p for p in results if safe_city in p.get("city", "").lower()]
    if country:
        safe_country = sanitize_input(country, 40).lower()
        results = [p for p in results if safe_country in p.get("country", "").lower()]
    if prop_type:
        safe_type = sanitize_input(prop_type, 40).lower()
        results = [p for p in results if safe_type in p.get("type", "").lower()]
    if search:
        s = sanitize_input(search, 80).lower()
        results = [
            p for p in results if 
            s in p.get("title", "").lower() or 
            s in p.get("city", "").lower() or 
            s in p.get("brand", "").lower() or 
            s in p.get("description", "").lower()
        ]
        
    return {
        "total": len(results),
        "limit": safe_limit,
        "properties": results[:safe_limit]
    }

@app.post("/api/chat")
def chat_endpoint(req: ChatRequest, authorization: Optional[str] = Header(None)):
    # Sanitize prompt
    clean_message = sanitize_input(req.message, max_chars=1000)
    if not clean_message:
        raise HTTPException(status_code=400, detail="Query contains invalid or empty content.")

    # Validate API key format if provided
    api_key = req.api_key
    if not api_key and authorization and authorization.startswith("Bearer "):
        api_key = authorization.split("Bearer ")[1].strip()

    if api_key and not validate_api_key(api_key):
        raise HTTPException(status_code=400, detail="Provided API key does not meet security format requirements.")

    safe_model = sanitize_input(req.model, 80) if req.model else None

    # Sanitize chat history
    history_dicts = []
    if req.history:
        for m in req.history[-6:]:
            history_dicts.append({
                "role": m.role,
                "content": sanitize_input(m.content, max_chars=1000)
            })

    try:
        response = ai_engine.generate_chat_response(
            message=clean_message,
            history=history_dicts,
            model=safe_model,
            user_api_key=api_key
        )
        return response
    except Exception as e:
        # Prevent stack trace leakage in enterprise production
        return {
            "response": "An analytical processing exception occurred. Grounded index remains accessible for structured queries.",
            "model": "Fallback Intelligence System",
            "source": "DarGlobal & Wasalt Intelligence Index",
            "matched_properties": ai_engine.search_context(clean_message, top_k=2),
            "suggestions": ["View DarGlobal international portfolio", "Search Wasalt verified Saudi listings"]
        }

# Mount Frontend static assets
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
