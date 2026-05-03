"""
Prometheus metrics for Valura AI Agent Ecosystem.

Tracks:
- Request counts and latencies
- Safety Guard performance
- Intent Classifier performance
- Agent execution metrics
- Error rates
- Token usage and costs
"""

from prometheus_client import Counter, Histogram, Gauge, Info
import time
from functools import wraps
from typing import Callable, Any


# =============================================================================
# Request Metrics
# =============================================================================

# Total requests counter
requests_total = Counter(
    'valura_requests_total',
    'Total number of requests',
    ['endpoint', 'method', 'status']
)

# Request duration histogram
request_duration_seconds = Histogram(
    'valura_request_duration_seconds',
    'Request duration in seconds',
    ['endpoint', 'method'],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

# Active requests gauge
active_requests = Gauge(
    'valura_active_requests',
    'Number of active requests',
    ['endpoint']
)


# =============================================================================
# Safety Guard Metrics
# =============================================================================

# Safety checks counter
safety_checks_total = Counter(
    'valura_safety_checks_total',
    'Total number of safety checks',
    ['verdict', 'category']
)

# Safety check duration
safety_check_duration_seconds = Histogram(
    'valura_safety_check_duration_seconds',
    'Safety check duration in seconds',
    buckets=(0.001, 0.002, 0.005, 0.01, 0.025, 0.05, 0.1)
)

# Blocked queries counter
blocked_queries_total = Counter(
    'valura_blocked_queries_total',
    'Total number of blocked queries',
    ['category']
)


# =============================================================================
# Intent Classifier Metrics
# =============================================================================

# Classifications counter
classifications_total = Counter(
    'valura_classifications_total',
    'Total number of intent classifications',
    ['intent', 'target_agent']
)

# Classification duration
classification_duration_seconds = Histogram(
    'valura_classification_duration_seconds',
    'Classification duration in seconds',
    buckets=(0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0)
)

# Classification confidence
classification_confidence = Histogram(
    'valura_classification_confidence',
    'Classification confidence score',
    buckets=(0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1.0)
)


# =============================================================================
# Agent Metrics
# =============================================================================

# Agent executions counter
agent_executions_total = Counter(
    'valura_agent_executions_total',
    'Total number of agent executions',
    ['agent_type', 'status']
)

# Agent execution duration
agent_execution_duration_seconds = Histogram(
    'valura_agent_execution_duration_seconds',
    'Agent execution duration in seconds',
    ['agent_type'],
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0)
)

# Agent errors counter
agent_errors_total = Counter(
    'valura_agent_errors_total',
    'Total number of agent errors',
    ['agent_type', 'error_type']
)


# =============================================================================
# LLM Metrics
# =============================================================================

# LLM calls counter
llm_calls_total = Counter(
    'valura_llm_calls_total',
    'Total number of LLM API calls',
    ['model', 'purpose']
)

# LLM token usage
llm_tokens_total = Counter(
    'valura_llm_tokens_total',
    'Total number of tokens used',
    ['model', 'token_type']  # token_type: input, output
)

# LLM call duration
llm_call_duration_seconds = Histogram(
    'valura_llm_call_duration_seconds',
    'LLM call duration in seconds',
    ['model', 'purpose'],
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0)
)

# LLM cost (estimated)
llm_cost_usd = Counter(
    'valura_llm_cost_usd_total',
    'Total estimated LLM cost in USD',
    ['model']
)


# =============================================================================
# Session Metrics
# =============================================================================

# Active sessions gauge
active_sessions = Gauge(
    'valura_active_sessions',
    'Number of active sessions'
)

# Session operations counter
session_operations_total = Counter(
    'valura_session_operations_total',
    'Total number of session operations',
    ['operation']  # operation: create, get, update
)


# =============================================================================
# Rate Limiter Metrics
# =============================================================================

# Rate limit checks counter
rate_limit_checks_total = Counter(
    'valura_rate_limit_checks_total',
    'Total number of rate limit checks',
    ['result']  # result: allowed, blocked
)

# Rate limited requests counter
rate_limited_requests_total = Counter(
    'valura_rate_limited_requests_total',
    'Total number of rate limited requests',
    ['user_id']
)


# =============================================================================
# System Metrics
# =============================================================================

# System info
system_info = Info(
    'valura_system',
    'System information'
)

# Uptime gauge
system_uptime_seconds = Gauge(
    'valura_system_uptime_seconds',
    'System uptime in seconds'
)


# =============================================================================
# Decorator Functions
# =============================================================================

def track_request(endpoint: str, method: str = 'POST'):
    """Decorator to track request metrics."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            active_requests.labels(endpoint=endpoint).inc()
            start_time = time.time()
            status = 'success'
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = 'error'
                raise
            finally:
                duration = time.time() - start_time
                active_requests.labels(endpoint=endpoint).dec()
                request_duration_seconds.labels(endpoint=endpoint, method=method).observe(duration)
                requests_total.labels(endpoint=endpoint, method=method, status=status).inc()
        
        return wrapper
    return decorator


def track_safety_check(func: Callable) -> Callable:
    """Decorator to track safety check metrics."""
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time
        
        # Track metrics
        safety_check_duration_seconds.observe(duration)
        verdict = 'safe' if result.is_safe else 'blocked'
        category = result.category or 'none'
        safety_checks_total.labels(verdict=verdict, category=category).inc()
        
        if not result.is_safe:
            blocked_queries_total.labels(category=category).inc()
        
        return result
    
    return wrapper


def track_classification(func: Callable) -> Callable:
    """Decorator to track classification metrics."""
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start_time
        
        # Track metrics
        classification_duration_seconds.observe(duration)
        classifications_total.labels(
            intent=result.intent,
            target_agent=result.target_agent
        ).inc()
        classification_confidence.observe(result.confidence)
        
        return result
    
    return wrapper


def track_agent_execution(agent_type: str):
    """Decorator to track agent execution metrics."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            status = 'success'
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = 'error'
                error_type = type(e).__name__
                agent_errors_total.labels(agent_type=agent_type, error_type=error_type).inc()
                raise
            finally:
                duration = time.time() - start_time
                agent_execution_duration_seconds.labels(agent_type=agent_type).observe(duration)
                agent_executions_total.labels(agent_type=agent_type, status=status).inc()
        
        return wrapper
    return decorator


def track_llm_call(model: str, purpose: str):
    """Decorator to track LLM call metrics."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            llm_calls_total.labels(model=model, purpose=purpose).inc()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                llm_call_duration_seconds.labels(model=model, purpose=purpose).observe(duration)
                return result
            except Exception:
                raise
        
        return wrapper
    return decorator


# =============================================================================
# Manual Tracking Functions
# =============================================================================

def record_llm_tokens(model: str, input_tokens: int, output_tokens: int):
    """Record LLM token usage."""
    llm_tokens_total.labels(model=model, token_type='input').inc(input_tokens)
    llm_tokens_total.labels(model=model, token_type='output').inc(output_tokens)


def record_llm_cost(model: str, cost: float):
    """Record LLM cost."""
    llm_cost_usd.labels(model=model).inc(cost)


def record_session_operation(operation: str):
    """Record session operation."""
    session_operations_total.labels(operation=operation).inc()


def update_active_sessions(count: int):
    """Update active sessions count."""
    active_sessions.set(count)


def record_rate_limit_check(allowed: bool, user_id: str = None):
    """Record rate limit check."""
    result = 'allowed' if allowed else 'blocked'
    rate_limit_checks_total.labels(result=result).inc()
    
    if not allowed and user_id:
        rate_limited_requests_total.labels(user_id=user_id).inc()


def update_system_uptime(uptime_seconds: float):
    """Update system uptime."""
    system_uptime_seconds.set(uptime_seconds)


def set_system_info(version: str, python_version: str, environment: str):
    """Set system information."""
    system_info.info({
        'version': version,
        'python_version': python_version,
        'environment': environment
    })
