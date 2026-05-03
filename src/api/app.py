"""FastAPI application with SSE streaming for query processing."""

import asyncio
import json
import time
import uuid
import sys
from pathlib import Path
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

# Load environment variables from .env file
load_dotenv()

from ..models.api import QueryRequest, ClassificationResult
from ..models.domain import User
from ..safety.guard import SafetyGuard
from ..classifier.intent import IntentClassifier
from ..router.router import Router
from ..mcp_client.client import MCPClient
from ..session.manager import SessionManager
from ..utils.fixtures import load_user_fixture
from ..utils.logger import get_logger
from ..utils.error_codes import (
    ErrorCode, ErrorResponse, ERROR_STATUS_CODES, create_error_response
)
from ..utils.rate_limiter import RateLimiter
from ..utils.job_queue import JobQueue
from ..monitoring import (
    track_request,
    record_llm_tokens,
    record_llm_cost,
    record_session_operation,
    update_active_sessions,
    record_rate_limit_check,
    update_system_uptime,
    set_system_info,
    safety_checks_total,
    blocked_queries_total,
    classifications_total,
    agent_executions_total,
)

# Initialize structured logger
logger = get_logger(__name__)

# Global instances
mcp_client: Optional[MCPClient] = None
safety_guard: Optional[SafetyGuard] = None
intent_classifier: Optional[IntentClassifier] = None
router: Optional[Router] = None
session_manager: Optional[SessionManager] = None
rate_limiter: Optional[RateLimiter] = None
job_queue: Optional[JobQueue] = None
startup_time: float = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    global mcp_client, safety_guard, intent_classifier, router, session_manager, rate_limiter, job_queue, startup_time
    
    # Startup
    logger.info("Starting Valura AI Agent Ecosystem...")
    startup_time = time.time()
    
    # Set system info for Prometheus
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    set_system_info(version="1.0.0", python_version=python_version, environment="production")
    
    # Initialize components
    mcp_client = MCPClient()
    safety_guard = SafetyGuard()
    intent_classifier = IntentClassifier()
    router = Router(mcp_client=mcp_client)
    session_manager = SessionManager()
    rate_limiter = RateLimiter(max_requests=10, window_seconds=60)
    job_queue = JobQueue(max_workers=5)
    
    # Start job queue
    await job_queue.start()
    
    logger.info("All components initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Valura AI Agent Ecosystem...")
    
    # Stop job queue
    if job_queue:
        await job_queue.stop()
    
    # Cleanup MCP client if connected
    if mcp_client and mcp_client._connected:
        await mcp_client.disconnect()
    
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Valura AI Agent Ecosystem",
    description="AI co-investor microservice for novice investors",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
STATIC_DIR = PROJECT_ROOT / "static"

# Mount static files if directory exists
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def root():
    """Serve the UI or return API info."""
    # Try multiple paths for index.html
    paths_to_try = [
        PROJECT_ROOT / "index.html",
        STATIC_DIR / "index.html",
        Path("index.html"),
        Path("static/index.html")
    ]
    
    for index_path in paths_to_try:
        if index_path.exists():
            return FileResponse(str(index_path))
    
    # Otherwise return API info
    return {
        "service": "Valura AI Agent Ecosystem",
        "status": "running",
        "version": "1.0.0",
        "ui": "/static/index.html",
        "api": {
            "health": "/health",
            "query": "/query"
        },
        "error": "index.html not found",
        "tried_paths": [str(p) for p in paths_to_try]
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    # Update system uptime
    uptime = time.time() - startup_time
    update_system_uptime(uptime)
    
    # Update active sessions count
    if session_manager:
        update_active_sessions(session_manager.get_session_count())
    
    return {
        "status": "healthy",
        "uptime_seconds": uptime,
        "components": {
            "safety_guard": "initialized" if safety_guard else "not_initialized",
            "intent_classifier": "initialized" if intent_classifier else "not_initialized",
            "router": "initialized" if router else "not_initialized",
            "mcp_client": "initialized" if mcp_client else "not_initialized",
            "session_manager": "initialized" if session_manager else "not_initialized",
            "rate_limiter": "initialized" if rate_limiter else "not_initialized",
            "job_queue": "initialized" if job_queue else "not_initialized"
        },
        "sessions": {
            "total": session_manager.get_session_count() if session_manager else 0
        },
        "job_queue": job_queue.get_queue_stats() if job_queue else {}
    }


@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.
    
    Returns metrics in Prometheus text format for scraping.
    
    Metrics include:
    - Request counts and latencies
    - Safety Guard performance
    - Intent Classifier performance
    - Agent execution metrics
    - Error rates
    - Token usage and costs
    - Session metrics
    - Rate limiter metrics
    - System uptime
    """
    # Update system uptime before returning metrics
    uptime = time.time() - startup_time
    update_system_uptime(uptime)
    
    # Update active sessions count
    if session_manager:
        update_active_sessions(session_manager.get_session_count())
    
    # Generate Prometheus metrics
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


async def process_query_stream(
    request: QueryRequest,
    request_id: str
) -> AsyncGenerator[str, None]:
    """
    Process query through pipeline and stream results via SSE.
    
    Pipeline: Safety Guard → Intent Classifier → Router → Agent
    
    Args:
        request: Query request with user_id, query, session_id
        request_id: Unique request identifier
        
    Yields:
        SSE events (safety_check, classification, routing, agent_start, data, done, error)
    """
    start_time = time.time()
    latency_metrics = {}
    
    try:
        # Load user data
        try:
            user = load_user_fixture(f"user_{request.user_id}.json")
            logger.debug("User loaded", request_id=request_id, user_id=user.user_id)
        except Exception as e:
            logger.error("Failed to load user", request_id=request_id, user_id=request.user_id, error=e)
            yield f"data: {json.dumps({'event': 'error', 'data': create_error_response(ErrorCode.USER_NOT_FOUND, details={'user_id': request.user_id}, request_id=request_id).model_dump()})}\n\n"
            return
        
        # Stage 1: Safety Guard
        safety_start = time.time()
        safety_verdict = safety_guard.check_query(request.query)
        latency_metrics["safety_guard_ms"] = (time.time() - safety_start) * 1000
        
        # Track safety check metrics
        verdict_label = 'safe' if safety_verdict.is_safe else 'blocked'
        category_label = safety_verdict.category or 'none'
        safety_checks_total.labels(verdict=verdict_label, category=category_label).inc()
        
        if not safety_verdict.is_safe:
            blocked_queries_total.labels(category=category_label).inc()
        
        # Stream safety check result
        yield f"data: {json.dumps({'event': 'safety_check', 'data': {'is_safe': safety_verdict.is_safe, 'category': safety_verdict.category, 'verdict': 'safe' if safety_verdict.is_safe else 'blocked', 'latency_ms': latency_metrics['safety_guard_ms']}})}\n\n"
        
        if not safety_verdict.is_safe:
            logger.warning(f"Query blocked by safety guard: {safety_verdict.category}")
            yield f"data: {json.dumps({'event': 'error', 'data': {'blocked': True, 'category': safety_verdict.category, 'message': safety_verdict.response}})}\n\n"
            
            # Send done event with metrics
            total_latency = (time.time() - start_time) * 1000
            yield f"data: {json.dumps({'event': 'done', 'data': {'latency_ms': total_latency, 'metrics': latency_metrics, 'blocked': True}})}\n\n"
            return
        
        # Stage 2: Intent Classification
        classifier_start = time.time()
        
        # Load conversation history from Session Manager
        conversation_history = session_manager.get_history(request.session_id) if request.session_id else []
        
        # Create session if it doesn't exist
        if request.session_id and not conversation_history:
            session_manager.create_session(request.session_id, request.user_id)
        
        classification = await intent_classifier.classify(
            request.query,
            conversation_history
        )
        
        latency_metrics["classifier_ms"] = (time.time() - classifier_start) * 1000
        latency_metrics["first_token_ms"] = (time.time() - start_time) * 1000
        
        # Track classification metrics
        classifications_total.labels(
            intent=classification.intent,
            target_agent=classification.target_agent.value
        ).inc()
        
        # Stream classification result
        yield f"data: {json.dumps({'event': 'classification', 'data': {'intent': classification.intent, 'target_agent': classification.target_agent.value, 'confidence': classification.confidence, 'entities': classification.entities.model_dump() if classification.entities else {}, 'latency_ms': latency_metrics['classifier_ms']}})}\n\n"
        
        # Stage 3: Router
        yield f"data: {json.dumps({'event': 'routing', 'data': {'agent': classification.target_agent.value, 'status': 'dispatching'}})}\n\n"
        
        # Stage 4: Agent Processing
        router_start = time.time()
        
        # Notify agent start
        yield f"data: {json.dumps({'event': 'agent_start', 'data': {'agent': classification.target_agent.value, 'status': 'processing'}})}\n\n"
        
        # Set timeout for agent execution (60 seconds)
        try:
            agent_response = await asyncio.wait_for(
                router.route(classification, user),
                timeout=60.0
            )
            
            latency_metrics["agent_ms"] = (time.time() - router_start) * 1000
            
            # Track agent execution metrics
            agent_executions_total.labels(
                agent_type=classification.target_agent.value,
                status='success'
            ).inc()
            
            # Stream agent response
            yield f"data: {json.dumps({'event': 'data', 'data': agent_response})}\n\n"
            
            # Store conversation turn in Session Manager
            if request.session_id:
                session_manager.store_turn(
                    session_id=request.session_id,
                    user_query=request.query,
                    agent_response=json.dumps(agent_response),
                    classification=classification
                )
            
        except asyncio.TimeoutError:
            logger.error("Agent execution timed out after 60 seconds")
            yield f"data: {json.dumps({'event': 'error', 'data': {'error': 'timeout', 'message': 'Query processing took too long. Please try again with a simpler query.'}})}\n\n"
            
            latency_metrics["agent_ms"] = 60000  # Timeout
        
        # Stage 5: Done event with metrics
        total_latency = (time.time() - start_time) * 1000
        latency_metrics["total_latency_ms"] = total_latency
        
        yield f"data: {json.dumps({'event': 'done', 'data': {'latency_ms': total_latency, 'metrics': latency_metrics, 'session_id': request.session_id}})}\n\n"
        
    except Exception as e:
        logger.error(f"Unexpected error processing query: {e}", exc_info=True)
        
        # Stream error event
        yield f"data: {json.dumps({'event': 'error', 'data': {'error': 'internal_error', 'message': 'An unexpected error occurred. Please try again.'}})}\n\n"
        
        # Send done event with error
        total_latency = (time.time() - start_time) * 1000
        yield f"data: {json.dumps({'event': 'done', 'data': {'latency_ms': total_latency, 'metrics': latency_metrics, 'error': True}})}\n\n"


@app.post("/query")
async def query_endpoint(request: QueryRequest, req: Request):
    """
    Process user query with SSE streaming.
    
    Args:
        request: QueryRequest with user_id, query, session_id
        req: FastAPI Request object
        
    Returns:
        EventSourceResponse with SSE stream
    """
    # Generate request ID
    request_id = str(uuid.uuid4())
    
    logger.info(
        "Received query",
        request_id=request_id,
        user_id=request.user_id,
        query_length=len(request.query),
        session_id=request.session_id
    )
    
    # Validate components are initialized
    if not all([safety_guard, intent_classifier, router, mcp_client, session_manager, rate_limiter]):
        error_response = create_error_response(
            ErrorCode.SERVICE_UNAVAILABLE,
            request_id=request_id
        )
        logger.error("Service not ready", request_id=request_id)
        return JSONResponse(
            status_code=ERROR_STATUS_CODES[ErrorCode.SERVICE_UNAVAILABLE],
            content=error_response.model_dump()
        )
    
    # Check rate limit
    is_allowed, rate_info = rate_limiter.is_allowed(request.user_id)
    
    # Track rate limit check
    record_rate_limit_check(is_allowed, request.user_id)
    
    if not is_allowed:
        error_response = create_error_response(
            ErrorCode.RATE_LIMIT_EXCEEDED,
            details=rate_info,
            request_id=request_id
        )
        logger.warning(
            "Rate limit exceeded",
            request_id=request_id,
            user_id=request.user_id,
            rate_info=rate_info
        )
        return JSONResponse(
            status_code=ERROR_STATUS_CODES[ErrorCode.RATE_LIMIT_EXCEEDED],
            content=error_response.model_dump(),
            headers={"Retry-After": str(rate_info.get("retry_after", 60))}
        )
    
    # Validate query length
    if len(request.query) > 2000:
        error_response = create_error_response(
            ErrorCode.QUERY_TOO_LONG,
            details={"max_length": 2000, "actual_length": len(request.query)},
            request_id=request_id
        )
        logger.warning(
            "Query too long",
            request_id=request_id,
            query_length=len(request.query)
        )
        return JSONResponse(
            status_code=ERROR_STATUS_CODES[ErrorCode.QUERY_TOO_LONG],
            content=error_response.model_dump()
        )
    
    # Return SSE stream
    return StreamingResponse(
        process_query_stream(request, request_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Request-ID": request_id,
            "X-RateLimit-Limit": str(rate_info.get("limit", 10)),
            "X-RateLimit-Remaining": str(rate_info.get("remaining", 0)),
            "X-RateLimit-Reset": rate_info.get("reset_at", "")
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
