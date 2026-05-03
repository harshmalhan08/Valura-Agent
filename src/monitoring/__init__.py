"""Monitoring module for Valura AI Agent Ecosystem."""

from .prometheus import (
    # Decorators
    track_request,
    track_safety_check,
    track_classification,
    track_agent_execution,
    track_llm_call,
    
    # Manual tracking functions
    record_llm_tokens,
    record_llm_cost,
    record_session_operation,
    update_active_sessions,
    record_rate_limit_check,
    update_system_uptime,
    set_system_info,
    
    # Metrics (for direct access if needed)
    requests_total,
    request_duration_seconds,
    active_requests,
    safety_checks_total,
    safety_check_duration_seconds,
    blocked_queries_total,
    classifications_total,
    classification_duration_seconds,
    classification_confidence,
    agent_executions_total,
    agent_execution_duration_seconds,
    agent_errors_total,
    llm_calls_total,
    llm_tokens_total,
    llm_call_duration_seconds,
    llm_cost_usd,
    active_sessions,
    session_operations_total,
    rate_limit_checks_total,
    rate_limited_requests_total,
    system_info,
    system_uptime_seconds,
)

__all__ = [
    # Decorators
    'track_request',
    'track_safety_check',
    'track_classification',
    'track_agent_execution',
    'track_llm_call',
    
    # Manual tracking functions
    'record_llm_tokens',
    'record_llm_cost',
    'record_session_operation',
    'update_active_sessions',
    'record_rate_limit_check',
    'update_system_uptime',
    'set_system_info',
    
    # Metrics
    'requests_total',
    'request_duration_seconds',
    'active_requests',
    'safety_checks_total',
    'safety_check_duration_seconds',
    'blocked_queries_total',
    'classifications_total',
    'classification_duration_seconds',
    'classification_confidence',
    'agent_executions_total',
    'agent_execution_duration_seconds',
    'agent_errors_total',
    'llm_calls_total',
    'llm_tokens_total',
    'llm_call_duration_seconds',
    'llm_cost_usd',
    'active_sessions',
    'session_operations_total',
    'rate_limit_checks_total',
    'rate_limited_requests_total',
    'system_info',
    'system_uptime_seconds',
]
