"""API request/response models"""

from datetime import datetime
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """HTTP request to /query endpoint"""
    user_id: str = Field(description="User identifier")
    query: str = Field(min_length=1, max_length=2000, description="User query text")
    session_id: Optional[str] = Field(default=None, description="Session identifier for conversation history")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "usr_001",
                "query": "How is my portfolio doing?",
                "session_id": "sess_abc123"
            }
        }


class SafetyVerdict(BaseModel):
    """Safety guard decision"""
    is_safe: bool = Field(description="Whether the query is safe to process")
    category: Optional[str] = Field(default=None, description="Harmful category if blocked")
    response: Optional[str] = Field(default=None, description="Professional response message if blocked")

    class Config:
        json_schema_extra = {
            "example": {
                "is_safe": False,
                "category": "insider_trading",
                "response": "I cannot assist with trading on material non-public information..."
            }
        }


class ExtractedEntities(BaseModel):
    """Entities extracted from user query"""
    tickers: List[str] = Field(default_factory=list, description="Stock ticker symbols (uppercase with exchange suffix)")
    amount: Optional[float] = Field(default=None, description="Monetary amount or quantity")
    currency: Optional[str] = Field(default=None, description="ISO 4217 currency code")
    rate: Optional[float] = Field(default=None, description="Interest rate or return rate as decimal (0.08 for 8%)")
    period_years: Optional[int] = Field(default=None, description="Time period in years")
    frequency: Optional[str] = Field(default=None, description="Frequency: daily, weekly, monthly, yearly")
    horizon: Optional[str] = Field(default=None, description="Investment horizon: short-term, medium-term, long-term")
    time_period: Optional[str] = Field(default=None, description="Time period: 1d, 1w, 1m, 3m, 1y, ytd, etc.")
    topics: List[str] = Field(default_factory=list, description="Topics or keywords")
    sectors: List[str] = Field(default_factory=list, description="Market sectors")
    index: Optional[str] = Field(default=None, description="Market index: S&P 500, NASDAQ, FTSE 100, etc.")
    action: Optional[str] = Field(default=None, description="Action: buy, sell, hold, hedge, rebalance")
    goal: Optional[str] = Field(default=None, description="Financial goal: retirement, education, house, FIRE, emergency_fund")

    class Config:
        json_schema_extra = {
            "example": {
                "tickers": ["AAPL", "MSFT"],
                "amount": 10000,
                "currency": "USD",
                "action": "buy"
            }
        }


class AgentType(str, Enum):
    """Available specialist agents"""
    PORTFOLIO_HEALTH = "portfolio_health"
    MARKET_RESEARCH = "market_research"
    INVESTMENT_STRATEGY = "investment_strategy"
    FINANCIAL_PLANNING = "financial_planning"
    FINANCIAL_CALCULATOR = "financial_calculator"
    RISK_ASSESSMENT = "risk_assessment"
    PRODUCT_RECOMMENDATION = "product_recommendation"
    PREDICTIVE_ANALYSIS = "predictive_analysis"
    CUSTOMER_SUPPORT = "customer_support"
    GENERAL_QUERY = "general_query"


class ClassificationResult(BaseModel):
    """Intent classifier output"""
    intent: str = Field(description="Natural language description of user intent")
    entities: ExtractedEntities = Field(description="Extracted entities from query")
    target_agent: AgentType = Field(description="Which specialist agent should handle this query")
    safety_verdict: str = Field(description="Informational safety assessment (not blocking)")
    confidence: float = Field(ge=0.0, le=1.0, description="Classification confidence score")

    class Config:
        json_schema_extra = {
            "example": {
                "intent": "Check portfolio health and performance",
                "entities": {},
                "target_agent": "portfolio_health",
                "safety_verdict": "safe",
                "confidence": 0.95
            }
        }


class ConcentrationRisk(BaseModel):
    """Portfolio concentration metrics"""
    top_position_pct: float = Field(description="Percentage of portfolio in largest holding")
    top_3_positions_pct: float = Field(description="Percentage of portfolio in top 3 holdings")
    level: str = Field(description="Risk level: high, medium, low")

    class Config:
        json_schema_extra = {
            "example": {
                "top_position_pct": 35.2,
                "top_3_positions_pct": 68.5,
                "level": "medium"
            }
        }


class Performance(BaseModel):
    """Portfolio performance metrics"""
    total_return_pct: float = Field(description="Total return percentage")
    annualized_return_pct: float = Field(description="Annualized return percentage")
    current_value: float = Field(description="Current portfolio value")
    cost_basis: float = Field(description="Total cost basis")

    class Config:
        json_schema_extra = {
            "example": {
                "total_return_pct": 12.5,
                "annualized_return_pct": 11.8,
                "current_value": 112500.0,
                "cost_basis": 100000.0
            }
        }


class BenchmarkComparison(BaseModel):
    """Portfolio vs benchmark comparison"""
    benchmark_name: str = Field(description="Benchmark index name (e.g., S&P 500)")
    benchmark_return_pct: float = Field(description="Benchmark return percentage")
    alpha_pct: float = Field(description="Portfolio return minus benchmark return")

    class Config:
        json_schema_extra = {
            "example": {
                "benchmark_name": "S&P 500",
                "benchmark_return_pct": 10.2,
                "alpha_pct": 2.3
            }
        }


class Observation(BaseModel):
    """Plain-language portfolio insight"""
    text: str = Field(description="Observation text grounded in actual holdings")
    severity: str = Field(description="Severity level: info, warning, critical")

    class Config:
        json_schema_extra = {
            "example": {
                "text": "Your portfolio is outperforming the S&P 500 by 2.3%",
                "severity": "info"
            }
        }


class PortfolioHealthResponse(BaseModel):
    """Portfolio Health Agent output"""
    concentration_risk: ConcentrationRisk = Field(description="Concentration risk metrics")
    performance: Performance = Field(description="Performance metrics")
    benchmark_comparison: BenchmarkComparison = Field(description="Benchmark comparison")
    observations: List[Observation] = Field(min_length=2, max_length=3, description="Key insights")
    disclaimer: str = Field(
        default="This analysis is for informational purposes only and does not constitute financial advice. "
                "Past performance does not guarantee future results. Consult a licensed financial advisor.",
        description="Regulatory disclaimer"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "concentration_risk": {
                    "top_position_pct": 35.2,
                    "top_3_positions_pct": 68.5,
                    "level": "medium"
                },
                "performance": {
                    "total_return_pct": 12.5,
                    "annualized_return_pct": 11.8,
                    "current_value": 112500.0,
                    "cost_basis": 100000.0
                },
                "benchmark_comparison": {
                    "benchmark_name": "S&P 500",
                    "benchmark_return_pct": 10.2,
                    "alpha_pct": 2.3
                },
                "observations": [
                    {
                        "text": "Your portfolio is outperforming the S&P 500 by 2.3%",
                        "severity": "info"
                    }
                ],
                "disclaimer": "This analysis is for informational purposes only..."
            }
        }


class ConversationTurn(BaseModel):
    """Single turn in conversation history"""
    turn_number: int = Field(description="Turn sequence number")
    user_query: str = Field(description="User's query text")
    agent_response: str = Field(description="Agent's response text")
    classification: ClassificationResult = Field(description="Classification result for this turn")
    timestamp: datetime = Field(description="Timestamp of this turn")

    class Config:
        json_schema_extra = {
            "example": {
                "turn_number": 1,
                "user_query": "How is my portfolio doing?",
                "agent_response": "Your portfolio shows...",
                "classification": {
                    "intent": "Check portfolio health",
                    "entities": {},
                    "target_agent": "portfolio_health",
                    "safety_verdict": "safe",
                    "confidence": 0.95
                },
                "timestamp": "2024-01-15T10:30:00"
            }
        }
