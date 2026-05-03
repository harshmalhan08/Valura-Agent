"""
Shared pytest fixtures for the Valura AI assignment.

CRITICAL: All tests must use mock_llm fixture to avoid real API calls.
CI runs without OPENAI_API_KEY and unmocked LLM calls will fail.
"""
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

import pytest

from src.models.api import ClassificationResult, ExtractedEntities, AgentType


FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


# ---------------------------------------------------------------------------
# Fixture loaders
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    """Return path to fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture
def load_user():
    """Load a user fixture by filename, e.g. load_user('user_001_active_trader_us.json')."""
    def _load(filename: str) -> dict:
        path = FIXTURES_DIR / "users" / filename
        if not path.exists():
            raise FileNotFoundError(f"No fixture file: {filename}")
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return _load


@pytest.fixture
def gold_classifier_queries() -> List[dict]:
    """Load gold standard intent classification test queries."""
    with open(FIXTURES_DIR / "test_queries" / "intent_classification.json", encoding="utf-8") as f:
        return json.load(f)["queries"]


@pytest.fixture
def gold_safety_queries() -> List[dict]:
    """Load gold standard safety test queries."""
    with open(FIXTURES_DIR / "test_queries" / "safety_pairs.json", encoding="utf-8") as f:
        return json.load(f)["queries"]


@pytest.fixture
def conversation_test_cases():
    """Returns a callable: conversation_test_cases('follow_up_session')."""
    def _load(name: str) -> List[dict]:
        path = FIXTURES_DIR / "conversations" / f"{name}.json"
        with open(path, encoding="utf-8") as f:
            return json.load(f)["test_cases"]
    return _load


# ---------------------------------------------------------------------------
# LLM Mocking - CRITICAL FOR CI
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_openai_client():
    """
    Mock the Azure OpenAI client to avoid real API calls.
    
    Returns a MagicMock that can be configured per-test.
    
    Usage:
        def test_something(mock_openai_client):
            mock_openai_client.beta.chat.completions.parse.return_value.choices = [
                MagicMock(message=MagicMock(parsed=ClassificationResult(...)))
            ]
    """
    with patch('src.classifier.intent.AzureOpenAI') as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


@pytest.fixture
def mock_classification_result():
    """
    Returns a factory function to create mock ClassificationResult objects.
    
    Usage:
        def test_something(mock_classification_result):
            result = mock_classification_result(
                intent="Check portfolio health",
                target_agent=AgentType.PORTFOLIO_HEALTH
            )
    """
    def _create(
        intent: str = "Check portfolio health",
        target_agent: AgentType = AgentType.PORTFOLIO_HEALTH,
        confidence: float = 0.95,
        entities: Dict[str, Any] = None
    ) -> ClassificationResult:
        if entities is None:
            entities = {}
        
        return ClassificationResult(
            intent=intent,
            entities=ExtractedEntities(**entities),
            target_agent=target_agent,
            safety_verdict="safe",
            confidence=confidence
        )
    return _create


@pytest.fixture
def mock_mcp_client():
    """
    Mock MCP client to avoid real Yahoo Finance API calls.
    
    Returns an AsyncMock that can be configured per-test.
    
    Usage:
        @pytest.mark.asyncio
        async def test_something(mock_mcp_client):
            mock_mcp_client.get_ticker_info.return_value = {
                "content": [{"text": "Price: $150.00"}]
            }
    """
    with patch('src.mcp_client.client.MCPClient') as mock:
        client = AsyncMock()
        client.connect = AsyncMock()
        client.disconnect = AsyncMock()
        client.get_ticker_info = AsyncMock(return_value={
            "content": [{"text": "Current Price: $150.00"}]
        })
        client.get_price_history = AsyncMock(return_value={
            "content": [{"text": "Historical data..."}]
        })
        mock.return_value = client
        yield client


@pytest.fixture
def sample_user_data():
    """Return sample user data for testing."""
    return {
        "user_id": "usr_001",
        "name": "Test User",
        "email": "test@example.com",
        "risk_tolerance": "moderate",
        "investment_goals": ["growth", "income"],
        "base_currency": "USD",
        "positions": [
            {
                "ticker": "AAPL",
                "quantity": 10,
                "cost_basis": 1500.00,
                "currency": "USD"
            },
            {
                "ticker": "GOOGL",
                "quantity": 5,
                "cost_basis": 750.00,
                "currency": "USD"
            }
        ]
    }


# ---------------------------------------------------------------------------
# Async Test Support
# ---------------------------------------------------------------------------

@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
