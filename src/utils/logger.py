"""Structured logging system with context and sensitive data redaction."""

import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path


class StructuredLogger:
    """
    Structured logger with JSON formatting and sensitive data redaction.
    
    Features:
    - JSON structured logs
    - Request ID tracking
    - Sensitive data redaction (API keys, portfolio values)
    - Performance metrics
    - Error context
    """
    
    def __init__(self, name: str, log_level: str = "INFO"):
        """
        Initialize structured logger.
        
        Args:
            name: Logger name (usually module name)
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Remove existing handlers
        self.logger.handlers.clear()
        
        # Console handler with JSON formatter
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(console_handler)
        
        # File handler for persistent logs
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        file_handler = logging.FileHandler(log_dir / "valura_ai.log")
        file_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(file_handler)
    
    def _redact_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Redact sensitive information from logs."""
        sensitive_keys = [
            "api_key", "password", "token", "secret", "authorization",
            "portfolio_value", "cost_basis", "current_value"
        ]
        
        redacted = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                redacted[key] = "***REDACTED***"
            elif isinstance(value, dict):
                redacted[key] = self._redact_sensitive_data(value)
            elif isinstance(value, list):
                redacted[key] = [
                    self._redact_sensitive_data(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                redacted[key] = value
        
        return redacted
    
    def info(self, message: str, **context):
        """Log info message with context."""
        context = self._redact_sensitive_data(context)
        self.logger.info(message, extra={"context": context})
    
    def warning(self, message: str, **context):
        """Log warning message with context."""
        context = self._redact_sensitive_data(context)
        self.logger.warning(message, extra={"context": context})
    
    def error(self, message: str, error: Optional[Exception] = None, **context):
        """Log error message with context and exception."""
        context = self._redact_sensitive_data(context)
        if error:
            context["error_type"] = type(error).__name__
            context["error_message"] = str(error)
        self.logger.error(message, extra={"context": context}, exc_info=error)
    
    def debug(self, message: str, **context):
        """Log debug message with context."""
        context = self._redact_sensitive_data(context)
        self.logger.debug(message, extra={"context": context})
    
    def critical(self, message: str, **context):
        """Log critical message with context."""
        context = self._redact_sensitive_data(context)
        self.logger.critical(message, extra={"context": context})


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add context if available
        if hasattr(record, "context"):
            log_data["context"] = record.context
        
        # Add exception info if available
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


# Global logger instance
def get_logger(name: str) -> StructuredLogger:
    """Get or create a structured logger."""
    return StructuredLogger(name)
