"""Domain models for portfolio and user data"""

from datetime import datetime
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field


class Currency(str, Enum):
    """Supported currencies"""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    CAD = "CAD"
    SGD = "SGD"


class Position(BaseModel):
    """Individual portfolio holding"""
    ticker: str = Field(description="Stock ticker symbol (e.g., AAPL, NVDA)")
    exchange: str = Field(description="Exchange code (e.g., NASDAQ, NYSE)")
    quantity: float = Field(gt=0, description="Number of shares")
    avg_cost: float = Field(gt=0, description="Average cost basis per share")
    currency: str = Field(default="USD", description="Currency of the position")
    purchased_at: str = Field(description="Purchase date in YYYY-MM-DD format")

    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "AAPL",
                "exchange": "NASDAQ",
                "quantity": 100,
                "avg_cost": 150.0,
                "currency": "USD",
                "purchased_at": "2023-01-15"
            }
        }


class Portfolio(BaseModel):
    """User's complete portfolio"""
    positions: List[Position] = Field(default_factory=list, description="List of holdings")
    base_currency: str = Field(default="USD", description="Base currency for reporting")

    @property
    def total_cost_basis(self) -> float:
        """Calculate total amount invested"""
        return sum(p.quantity * p.avg_cost for p in self.positions)

    @property
    def is_empty(self) -> bool:
        """Check if portfolio has no positions"""
        return len(self.positions) == 0

    class Config:
        json_schema_extra = {
            "example": {
                "positions": [
                    {
                        "ticker": "AAPL",
                        "exchange": "NASDAQ",
                        "quantity": 100,
                        "avg_cost": 150.0,
                        "currency": "USD",
                        "purchased_at": "2023-01-15"
                    }
                ],
                "base_currency": "USD"
            }
        }


class User(BaseModel):
    """User profile with portfolio and preferences"""
    user_id: str = Field(description="Unique user identifier")
    name: str = Field(description="User's full name")
    age: Optional[int] = Field(default=None, description="User's age")
    country: str = Field(description="User's country code (e.g., US, UK, SG)")
    base_currency: str = Field(default="USD", description="User's base currency")
    kyc: dict = Field(default_factory=dict, description="KYC status and details")
    risk_profile: str = Field(description="Risk tolerance: conservative, moderate, aggressive")
    positions: List[Position] = Field(default_factory=list, description="Portfolio positions")
    preferences: dict = Field(default_factory=dict, description="User preferences (benchmark, etc.)")

    @property
    def portfolio(self) -> Portfolio:
        """Get user's portfolio"""
        return Portfolio(
            positions=self.positions,
            base_currency=self.base_currency
        )

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "usr_001",
                "name": "Alex Chen",
                "age": 28,
                "country": "US",
                "base_currency": "USD",
                "kyc": {"status": "verified"},
                "risk_profile": "aggressive",
                "positions": [],
                "preferences": {"preferred_benchmark": "S&P 500"}
            }
        }
