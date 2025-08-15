#!/usr/bin/env python3
"""
Design Team Pod API
REST API interface for design tools and analysis
"""

import os
import sys
import json
import asyncio
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Union
import logging
import time
import uuid

try:
    from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
    from fastapi.responses import JSONResponse, FileResponse
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
    import uvicorn
    from rich.console import Console
    import structlog
except ImportError:
    print("Missing dependencies. Install with: pip install -r requirements.txt")
    sys.exit(1)

# Setup logging
logger = structlog.get_logger()
console = Console()

# Import design tools
sys.path.append('/app/tools')
try:
    from visual_diff import VisualDiffAnalyzer
    from scrape_content import ContentScraper
    from ai_analyzer import AIAnalyzer
except ImportError as e:
    logger.error("Failed to import design tools", error=str(e))
    sys.exit(1)

app = FastAPI(
    title="Design Team Pod API",
    description="Pixel-perfect design analysis and cloning toolkit",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global configuration
WORKSPACE_DIR = Path(os.getenv('WORKSPACE_DIR', '/app/workspace'))
TOOLS_DIR = Path(os.getenv('TOOLS_DIR', '/app/tools'))
KNOWLEDGE_DIR = Path(os.getenv('KNOWLEDGE_DIR', '/app/knowledge'))

# Ensure directories exist
for directory in [WORKSPACE_DIR, WORKSPACE_DIR / "projects", WORKSPACE_DIR / "output", WORKSPACE_DIR / "temp"]:
    directory.mkdir(parents=True, exist_ok=True)

# Background task storage
active_tasks = {}

# API Models
class AnalysisRequest(BaseModel):
    url: str = Field(..., description="URL to analyze")
    auth: Optional[str] = Field(None, description="Basic auth credentials (user:pass)")
    options: Optional[Dict] = Field(default_factory=dict, description="Analysis options")

class ComparisonRequest(BaseModel):
    image1_url: Optional[str] = Field(None, description="First image URL")
    image2_url: Optional[str] = Field(None, description="Second image URL")
    ai_provider: Optional[str] = Field("anthropic", description="AI provider")
    options: Optional[Dict] = Field(default_factory=dict, description="Comparison options")

class TaskStatus(BaseModel):
    task_id: str
    status: str
    progress: float
    message: str
    result: Optional[Dict] = None
    error: Optional[str] = None

# Utility functions
def generate_task_id() -> str:
    """Generate unique task ID"""
    return f"task_{int(time.time())}_{str(uuid.uuid4())[:8]}"

def parse_auth(auth_string: str) -> Optional[tuple]:
    """Parse basic auth string"""
    if not auth_string:
        return None
    try:
        username, password = auth_string.split(':', 1)
        return (username, password)
    except ValueError:
        return None

async def save_uploaded_file(upload_file: UploadFile, directory: Path) -> Path:
    """Save uploaded file to directory"""
    file_path = directory / f"{int(time.time())}_{upload_file.filename}"
    
    with open(file_path, "wb") as f:
        content = await upload_file.read()
        f.write(content)
    
    return file_path

# API Endpoints

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "Design Team Pod API",
        "version": "2.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "analyze": "/analyze/",
            "compare": "/compare/",
            "scrape": "/scrape/",
            "ai-analyze": "/ai-analyze/",
            "tasks": "/tasks/",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "workspace": str(WORKSPACE_DIR),
        "disk_usage": _get_disk_usage()
    }

def _get_disk_usage() -> Dict:
    """Get disk usage information"""
    import shutil
    
    try:
        total, used, free = shutil.disk_usage(WORKSPACE_DIR)
        return {
            "total_gb": round(total / (1024**3), 2),
            "used_gb": round(used / (1024**3), 2),
            "free_gb": round(free / (1024**3), 2),
            "usage_percent": round((used / total) * 100, 1)
        }
    except Exception:
        return {"error": "Unable to get disk usage"}

@app.post("/scrape/", response_model=Dict)
async def scrape_content(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """Scrape website content for analysis"""
    task_id = generate_task_id()
    active_tasks[task_id] = TaskStatus(
        task_id=task_id,
        status="started",
        progress=0.0,
        message="Initializing content scraping..."
    )
    
    # Parse auth
    auth = parse_auth(request.auth) if request.auth else None
    
    # Start background task
    background_tasks.add_task(
        _run_content_scraping,
        task_id,
        request.url,
        auth,
        request.options
    )
    
    return {
        "task_id": task_id,
        "status": "started",
        "message": f"Content scraping started for {request.url}",
        "check_status_url": f"/tasks/{task_id}"
    }

async def _run_content_scraping(task_id: str, url: str, auth: Optional[tuple], options: Dict):
    """Background task for content scraping"""
    try:
        active_tasks[task_id].status = "running"
        active_tasks[task_id].message = "Scraping website content..."
        active_tasks[task_id].progress = 10.0
        
        scraper = ContentScraper(url, str(WORKSPACE_DIR), auth)
        
        active_tasks[task_id].progress = 50.0
        active_tasks[task_id].message = "Extracting content and assets..."
        
        results = await scraper.run_full_scrape()
        
        active_tasks[task_id].status = "completed"
        active_tasks[task_id].progress = 100.0
        active_tasks[task_id].message = "Content scraping completed successfully"
        active_tasks[task_id].result = results
        
    except Exception as e:
        logger.error("Content scraping failed", task_id=task_id, error=str(e))
        active_tasks[task_id].status = "failed"
        active_tasks[task_id].error = str(e)
        active_tasks[task_id].message = f"Scraping failed: {str(e)}"

@app.post("/compare/", response_model=Dict)
async def compare_images(
    background_tasks: BackgroundTasks,
    image1: UploadFile = File(..., description="First image"),
    image2: UploadFile = File(..., description="Second image"),
    ai_provider: str = Form("anthropic", description="AI provider"),
    options: str = Form("{}", description="JSON options")
):
    """Compare two images for visual differences"""
    task_id = generate_task_id()
    active_tasks[task_id] = TaskStatus(
        task_id=task_id,
        status="started",
        progress=0.0,
        message="Initializing image comparison..."
    )
    
    try:
        # Parse options
        parsed_options = json.loads(options) if options else {}
        
        # Save uploaded files
        temp_dir = WORKSPACE_DIR / "temp" / task_id
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        image1_path = await save_uploaded_file(image1, temp_dir)
        image2_path = await save_uploaded_file(image2, temp_dir)
        
        # Start background task
        background_tasks.add_task(
            _run_image_comparison,
            task_id,
            str(image1_path),
            str(image2_path),
            ai_provider,
            parsed_options
        )
        
        return {
            "task_id": task_id,
            "status": "started",
            "message": "Image comparison started",
            "check_status_url": f"/tasks/{task_id}"
        }
        
    except Exception as e:
        active_tasks[task_id].status = "failed"
        active_tasks[task_id].error = str(e)
        raise HTTPException(status_code=400, detail=str(e))

async def _run_image_comparison(task_id: str, image1_path: str, image2_path: str, ai_provider: str, options: Dict):
    """Background task for image comparison"""
    try:
        active_tasks[task_id].status = "running"
        active_tasks[task_id].message = "Running visual diff analysis..."
        active_tasks[task_id].progress = 25.0
        
        # Visual diff analysis
        analyzer = VisualDiffAnalyzer(str(WORKSPACE_DIR))
        visual_results = await analyzer.run_full_analysis(image1_path, image2_path, ai_provider)
        
        active_tasks[task_id].progress = 75.0
        active_tasks[task_id].message = "Running AI analysis..."
        
        # AI analysis
        ai_analyzer = AIAnalyzer(str(WORKSPACE_DIR))
        ai_results = await ai_analyzer.compare_images(image1_path, image2_path, ai_provider)
        
        # Combine results
        combined_results = {
            "visual_analysis": visual_results,
            "ai_analysis": ai_results,
            "summary": {
                "accuracy_score": visual_results.get('summary', {}).get('overall_accuracy', 0),
                "ai_provider": ai_provider,
                "timestamp": time.time()
            }
        }
        
        active_tasks[task_id].status = "completed"
        active_tasks[task_id].progress = 100.0
        active_tasks[task_id].message = "Image comparison completed successfully"
        active_tasks[task_id].result = combined_results
        
    except Exception as e:
        logger.error("Image comparison failed", task_id=task_id, error=str(e))
        active_tasks[task_id].status = "failed"
        active_tasks[task_id].error = str(e)
        active_tasks[task_id].message = f"Comparison failed: {str(e)}"

@app.post("/ai-analyze/", response_model=Dict)
async def ai_analyze_image(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(..., description="Image to analyze"),
    provider: str = Form("all", description="AI provider (openai, anthropic, or all)"),
    prompt: str = Form("", description="Custom analysis prompt"),
    options: str = Form("{}", description="JSON options")
):
    """Analyze image with AI vision models"""
    task_id = generate_task_id()
    active_tasks[task_id] = TaskStatus(
        task_id=task_id,
        status="started",
        progress=0.0,
        message="Initializing AI analysis..."
    )
    
    try:
        # Parse options
        parsed_options = json.loads(options) if options else {}
        
        # Save uploaded file
        temp_dir = WORKSPACE_DIR / "temp" / task_id
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        image_path = await save_uploaded_file(image, temp_dir)
        
        # Start background task
        background_tasks.add_task(
            _run_ai_analysis,
            task_id,
            str(image_path),
            provider,
            prompt if prompt else None,
            parsed_options
        )
        
        return {
            "task_id": task_id,
            "status": "started",
            "message": "AI analysis started",
            "check_status_url": f"/tasks/{task_id}"
        }
        
    except Exception as e:
        active_tasks[task_id].status = "failed"
        active_tasks[task_id].error = str(e)
        raise HTTPException(status_code=400, detail=str(e))

async def _run_ai_analysis(task_id: str, image_path: str, provider: str, prompt: Optional[str], options: Dict):
    """Background task for AI analysis"""
    try:
        active_tasks[task_id].status = "running"
        active_tasks[task_id].message = f"Analyzing with {provider}..."
        active_tasks[task_id].progress = 25.0
        
        analyzer = AIAnalyzer(str(WORKSPACE_DIR))
        
        if provider == "all":
            results = await analyzer.run_comprehensive_analysis(image_path)
        elif provider == "openai":
            results = await analyzer.analyze_with_openai(image_path, prompt)
        elif provider == "anthropic":
            results = await analyzer.analyze_with_anthropic(image_path, prompt)
        else:
            raise ValueError(f"Unknown provider: {provider}")
        
        active_tasks[task_id].status = "completed"
        active_tasks[task_id].progress = 100.0
        active_tasks[task_id].message = "AI analysis completed successfully"
        active_tasks[task_id].result = results
        
    except Exception as e:
        logger.error("AI analysis failed", task_id=task_id, error=str(e))
        active_tasks[task_id].status = "failed"
        active_tasks[task_id].error = str(e)
        active_tasks[task_id].message = f"Analysis failed: {str(e)}"

@app.get("/tasks/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """Get status of background task"""
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return active_tasks[task_id]

@app.get("/tasks/", response_model=List[TaskStatus])
async def list_tasks():
    """List all tasks"""
    return list(active_tasks.values())

@app.delete("/tasks/{task_id}")
async def cancel_task(task_id: str):
    """Cancel or remove task"""
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    del active_tasks[task_id]
    return {"message": f"Task {task_id} removed"}

@app.get("/workspace/projects/")
async def list_projects():
    """List all projects in workspace"""
    projects_dir = WORKSPACE_DIR / "projects"
    if not projects_dir.exists():
        return {"projects": []}
    
    projects = []
    for project_dir in projects_dir.iterdir():
        if project_dir.is_dir():
            # Try to read project metadata
            results_file = project_dir / "scrape_results.json"
            if results_file.exists():
                try:
                    with open(results_file) as f:
                        metadata = json.load(f).get('metadata', {})
                        projects.append({
                            "name": project_dir.name,
                            "path": str(project_dir),
                            "created": metadata.get('timestamp'),
                            "url": metadata.get('base_url'),
                            "size": _get_directory_size(project_dir)
                        })
                except Exception:
                    projects.append({
                        "name": project_dir.name,
                        "path": str(project_dir),
                        "created": project_dir.stat().st_mtime,
                        "size": _get_directory_size(project_dir)
                    })
    
    return {"projects": projects}

def _get_directory_size(directory: Path) -> str:
    """Get human-readable directory size"""
    total_size = 0
    for file_path in directory.rglob('*'):
        if file_path.is_file():
            total_size += file_path.stat().st_size
    
    # Convert to human readable
    for unit in ['B', 'KB', 'MB', 'GB']:
        if total_size < 1024.0:
            return f"{total_size:.1f} {unit}"
        total_size /= 1024.0
    return f"{total_size:.1f} TB"

@app.get("/workspace/projects/{project_name}")
async def get_project(project_name: str):
    """Get project details"""
    project_dir = WORKSPACE_DIR / "projects" / project_name
    if not project_dir.exists():
        raise HTTPException(status_code=404, detail="Project not found")
    
    results_file = project_dir / "scrape_results.json"
    if results_file.exists():
        with open(results_file) as f:
            return json.load(f)
    else:
        raise HTTPException(status_code=404, detail="Project results not found")

@app.get("/knowledge/")
async def get_knowledge_base():
    """Get knowledge base summary"""
    if not KNOWLEDGE_DIR.exists():
        return {"error": "Knowledge base not found"}
    
    knowledge_files = []
    for file_path in KNOWLEDGE_DIR.rglob('*.md'):
        knowledge_files.append({
            "name": file_path.name,
            "path": str(file_path.relative_to(KNOWLEDGE_DIR)),
            "size": file_path.stat().st_size,
            "modified": file_path.stat().st_mtime
        })
    
    return {
        "knowledge_base": str(KNOWLEDGE_DIR),
        "files": knowledge_files,
        "total_files": len(knowledge_files)
    }

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error("Unhandled exception", error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

if __name__ == "__main__":
    # Production server configuration
    host = os.getenv('API_HOST', '0.0.0.0')
    port = int(os.getenv('API_PORT', 8080))
    workers = int(os.getenv('API_WORKERS', 1))
    log_level = os.getenv('LOG_LEVEL', 'info')
    
    console.print(f"[bold green]Starting Design Team Pod API...[/bold green]")
    console.print(f"Host: {host}:{port}")
    console.print(f"Workspace: {WORKSPACE_DIR}")
    console.print(f"Tools: {TOOLS_DIR}")
    console.print(f"Knowledge: {KNOWLEDGE_DIR}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        workers=workers,
        log_level=log_level,
        reload=False
    )