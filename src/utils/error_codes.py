"""Standardized error codes and responses."""

from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel


class ErrorCode(str, Enum):
    """Standardized error codes."""
    
    # Client Errors (4xx)
    INVALID_REQUEST = "INVALID_REQUEST"
    MISSING_FIELD = "MISSING_FIELD"
    INVALID_USER = "INVALID_USER"
    INVALID_SESSION = "INVALID_SESSION"
    QUERY_TOO_LONG = "QUERY_TOO_LONG"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    
    # Safety Errors
    SAFETY_VIOLATION = "SAFETY_VIOLATION"
    HARMFUL_CONTENT = "HARMFUL_CONTENT"
    
    # Service Errors (5xx)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    TIMEOUT = "TIMEOUT"
    
    # Component Errors
    CLASSIFIER_ERROR = "CLASSIFIER_ERROR"
    AGENT_ERROR = "AGENT_ERROR"
    MCP_ERROR = "MCP_ERROR"
    LLM_ERROR = "LLM_ERROR"
    
    # Data Errors
    USER_NOT_FOUND = "USER_NOT_FOUND"
    PORTFOLIO_ERROR = "PORTFOLIO_ERROR"
    INVALID_TICKER = "INVALID_TICKER"


class ErrorResponse(BaseModel):
    """Standardized error response."""
    
    error_code: ErrorCode
    message: str
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None
    timestamp: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "error_code": "RATE_LIMIT_EXCEEDED",
                "message": "Too many requests. Please try again later.",
                "details": {
                    "limit": 10,
                    "window": "60s",
                    "retry_after": 45
                },
                "request_id": "req_abc123",
                "timestamp": "2026-05-03T12:00:00Z"
            }
        }


# Error code to HTTP status code mapping
ERROR_STATUS_CODES = {
    ErrorCode.INVALID_REQUEST: 400,
    ErrorCode.MISSING_FIELD: 400,
    ErrorCode.INVALID_USER: 400,
    ErrorCode.INVALID_SESSION: 400,
    ErrorCode.QUERY_TOO_LONG: 400,
    ErrorCode.RATE_LIMIT_EXCEEDED: 429,
    ErrorCode.SAFETY_VIOLATION: 403,
    ErrorCode.HARMFUL_CONTENT: 403,
    ErrorCode.INTERNAL_ERROR: 500,
    ErrorCode.SERVICE_UNAVAILABLE: 503,
    ErrorCode.TIMEOUT: 504,
    ErrorCode.CLASSIFIER_ERROR: 500,
    ErrorCode.AGENT_ERROR: 500,
    ErrorCode.MCP_ERROR: 500,
    ErrorCode.LLM_ERROR: 500,
    ErrorCode.USER_NOT_FOUND: 404,
    ErrorCode.PORTFOLIO_ERROR: 500,
    ErrorCode.INVALID_TICKER: 400,
}


# User-friendly error messages
ERROR_MESSAGES = {
    ErrorCode.INVALID_REQUEST: "Invalid request format. Please check your input.",
    ErrorCode.MISSING_FIELD: "Required field is missing.",
    ErrorCode.INVALID_USER: "Invalid user ID.",
    ErrorCode.INVALID_SESSION: "Invalid or expired session.",
    ErrorCode.QUERY_TOO_LONG: "Query is too long. Maximum 2000 characters.",
    ErrorCode.RATE_LIMIT_EXCEEDED: "Too many requests. Please try again later.",
    ErrorCode.SAFETY_VIOLATION: "Query violates safety guidelines.",
    ErrorCode.HARMFUL_CONTENT: "Query contains harmful content.",
    ErrorCode.INTERNAL_ERROR: "An internal error occurred. Please try again.",
    ErrorCode.SERVICE_UNAVAILABLE: "Service is temporarily unavailable.",
    ErrorCode.TIMEOUT: "Request timed out. Please try again.",
    ErrorCode.CLASSIFIER_ERROR: "Failed to classify query.",
    ErrorCode.AGENT_ERROR: "Agent execution failed.",
    ErrorCode.MCP_ERROR: "Market data service error.",
    ErrorCode.LLM_ERROR: "Language model service error.",
    ErrorCode.USER_NOT_FOUND: "User not found.",
    ErrorCode.PORTFOLIO_ERROR: "Portfolio data error.",
    ErrorCode.INVALID_TICKER: "Invalid ticker symbol.",
}


def create_error_response(
    error_code: ErrorCode,
    message: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> ErrorResponse:
    """
    Create standardized error response.
    
    Args:
        error_code: Error code
        message: Custom error message (defaults to standard message)
        details: Additional error details
        request_id: Request ID for tracking
        
    Returns:
        ErrorResponse object
    """
    from datetime import datetime
    
    return ErrorResponse(
        error_code=error_code,
        message=message or ERROR_MESSAGES.get(error_code, "An error occurred."),
        details=details,
        request_id=request_id,
        timestamp=datetime.utcnow().isoformat() + "Z"
    )
