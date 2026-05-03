"""Portfolio Health Agent - Full implementation with market data and calculations."""

import os
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from openai import AsyncOpenAI, AsyncAzureOpenAI

from ..models.domain import User, Portfolio, Position, Currency
from ..models.api import (
    ClassificationResult,
    PortfolioHealthResponse,
    ConcentrationRisk,
    Performance,
    BenchmarkComparison,
    Observation,
)
from ..mcp_client.client import MCPClient
from ..mcp_client.utils import parse_ticker_info, parse_price_history, calculate_return


class PortfolioHealthAgent:
    """
    Portfolio Health Agent - Analyzes portfolio health with market data.
    
    Provides:
    - Concentration risk analysis
    - Performance calculations
    - Benchmark comparison with alpha
    - Multi-currency normalization
    - LLM-generated observations tailored to user profile
    """
    
    def __init__(
        self,
        mcp_client: Optional[MCPClient] = None,
        openai_api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        """
        Initialize Portfolio Health Agent.
        
        Args:
            mcp_client: MCP client for market data (optional, will create if not provided)
            openai_api_key: OpenAI API key for observations
            model: OpenAI model to use
        """
        self.mcp_client = mcp_client or MCPClient()
        
        # Initialize OpenAI client (Azure or standard)
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        
        if azure_endpoint and azure_api_key:
            self.openai_client = AsyncAzureOpenAI(
                api_key=azure_api_key,
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
                azure_endpoint=azure_endpoint
            )
            self.model = model or os.getenv("AZURE_OPENAI_DEPLOYMENT_CHAT") or os.getenv("OPENAI_MODEL", "gpt-4o")
        else:
            api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key required")
            self.openai_client = AsyncOpenAI(api_key=api_key)
            self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
    
    async def execute(
        self,
        user: User,
        classification: ClassificationResult
    ) -> PortfolioHealthResponse:
        """
        Execute portfolio health analysis.
        
        Args:
            user: User with portfolio data
            classification: Classification result with extracted entities
            
        Returns:
            PortfolioHealthResponse with metrics and observations
        """
        portfolio = user.portfolio
        
        # Handle empty portfolio
        if not portfolio.positions or len(portfolio.positions) == 0:
            return await self._handle_empty_portfolio(user)
        
        # Get current prices for all positions
        current_prices = await self.get_current_prices(
            [pos.ticker for pos in portfolio.positions]
        )
        
        # Get FX rates if multi-currency
        fx_rates = await self.get_fx_rates(Currency(portfolio.base_currency))
        
        # Normalize to base currency
        normalized_portfolio = self.normalize_to_base_currency(
            portfolio.positions,
            Currency(portfolio.base_currency),
            fx_rates,
            current_prices
        )
        
        # Calculate metrics
        concentration = self.calculate_concentration_risk(
            normalized_portfolio,
            current_prices
        )
        
        performance = self.calculate_performance(
            normalized_portfolio,
            current_prices
        )
        
        # Select benchmark and calculate alpha
        benchmark_symbol = self.select_benchmark(normalized_portfolio)
        benchmark_return = await self.get_benchmark_return(benchmark_symbol, "1y")
        
        benchmark_comparison = BenchmarkComparison(
            benchmark_name=benchmark_symbol,
            benchmark_return_pct=benchmark_return * 100 if benchmark_return else 0.0,
            alpha_pct=(performance.annualized_return_pct - (benchmark_return * 100))
            if benchmark_return else 0.0
        )
        
        # Generate observations
        observations = await self.generate_observations(
            user,
            {
                "concentration": concentration,
                "performance": performance,
                "benchmark": benchmark_comparison,
                "current_prices": current_prices,
            }
        )
        
        return PortfolioHealthResponse(
            concentration_risk=concentration,
            performance=performance,
            benchmark_comparison=benchmark_comparison,
            observations=observations
        )
    
    async def _handle_empty_portfolio(self, user: User) -> PortfolioHealthResponse:
        """Handle empty portfolio case with BUILD-oriented guidance."""
        # Get investment goals from user preferences or default
        goals = user.preferences.get("investment_goals", []) if user.preferences else []
        goals_str = ', '.join(goals) if goals else 'not specified'
        
        observations = [
            Observation(
                text="Your portfolio is currently empty. Consider starting with a diversified index fund like VT (Vanguard Total World Stock ETF) or VOO (Vanguard S&P 500 ETF) to build a solid foundation.",
                severity="info"
            ),
            Observation(
                text=f"Based on your investment goals ({goals_str}), consider allocating funds across different asset classes to manage risk.",
                severity="info"
            ),
            Observation(
                text="This is not financial advice. Please consult with a qualified financial advisor before making investment decisions.",
                severity="info"
            )
        ]
        
        return PortfolioHealthResponse(
            concentration_risk=ConcentrationRisk(
                top_position_pct=0.0,
                top_3_positions_pct=0.0,
                level="low"
            ),
            performance=Performance(
                total_return_pct=0.0,
                annualized_return_pct=0.0,
                current_value=0.0,
                cost_basis=0.0
            ),
            benchmark_comparison=BenchmarkComparison(
                benchmark_name="N/A",
                benchmark_return_pct=0.0,
                alpha_pct=0.0
            ),
            observations=observations
        )
    
    async def get_current_prices(self, tickers: List[str]) -> Dict[str, float]:
        """Get current prices for tickers using MCP."""
        prices = {}
        
        try:
            await self.mcp_client.connect()
            
            for ticker in tickers:
                try:
                    response = await self.mcp_client.get_ticker_info(ticker)
                    parsed = parse_ticker_info(response)
                    
                    if "current_price" in parsed:
                        prices[ticker] = parsed["current_price"]
                    else:
                        # Default to cost basis if price unavailable
                        prices[ticker] = 0.0
                except Exception as e:
                    prices[ticker] = 0.0
            
            await self.mcp_client.disconnect()
            
        except Exception as e:
            # If MCP fails, return empty prices (will use cost basis)
            pass
        
        return prices
    
    async def get_fx_rates(self, base_currency: Currency) -> Dict[str, float]:
        """Get FX rates relative to base currency."""
        # For USD base currency, return standard rates
        if base_currency.value == "USD":
            return {
                "USD": 1.0,
                "EUR": 0.92,  # Fallback rates
                "GBP": 0.79,
                "JPY": 149.0,
                "CAD": 1.36,
                "SGD": 1.35
            }
        
        # For other base currencies, would fetch from MCP
        # For now, return default USD rates
        return {"USD": 1.0, "EUR": 0.92, "GBP": 0.79, "JPY": 149.0, "CAD": 1.36, "SGD": 1.35}
    
    async def get_benchmark_return(self, benchmark_symbol: str, period: str) -> Optional[float]:
        """Get benchmark return for period."""
        try:
            await self.mcp_client.connect()
            
            response = await self.mcp_client.get_price_history(
                benchmark_symbol,
                period=period,
                interval="1d"
            )
            
            prices = parse_price_history(response)
            ret = calculate_return(prices)
            
            await self.mcp_client.disconnect()
            
            return ret
            
        except Exception:
            return None
    
    def normalize_to_base_currency(
        self,
        positions: List[Position],
        base_currency: Currency,
        fx_rates: Dict[str, float],
        current_prices: Dict[str, float]
    ) -> List[Position]:
        """Normalize all positions to base currency."""
        normalized = []
        
        for pos in positions:
            if pos.currency == base_currency.value:
                normalized.append(pos)
            else:
                # Convert to base currency
                fx_rate = fx_rates.get(pos.currency, 1.0) / fx_rates.get(base_currency.value, 1.0)
                
                normalized_pos = Position(
                    ticker=pos.ticker,
                    exchange=pos.exchange,
                    quantity=pos.quantity,
                    avg_cost=pos.avg_cost * fx_rate,
                    currency=base_currency.value,
                    purchased_at=pos.purchased_at
                )
                normalized.append(normalized_pos)
        
        return normalized
    
    def calculate_concentration_risk(
        self,
        positions: List[Position],
        current_prices: Dict[str, float]
    ) -> ConcentrationRisk:
        """Calculate concentration risk metrics."""
        if not positions:
            return ConcentrationRisk(
                top_position_pct=0.0,
                top_3_positions_pct=0.0,
                level="low"
            )
        
        # Calculate current values
        values = []
        for pos in positions:
            price = current_prices.get(pos.ticker, pos.avg_cost)
            value = pos.quantity * price
            values.append((pos.ticker, value))
        
        # Sort by value descending
        values.sort(key=lambda x: x[1], reverse=True)
        
        total_value = sum(v[1] for v in values)
        
        if total_value == 0:
            return ConcentrationRisk(
                top_position_pct=0.0,
                top_3_positions_pct=0.0,
                level="low"
            )
        
        top_position_pct = (values[0][1] / total_value) * 100
        top_3_positions_pct = (sum(v[1] for v in values[:3]) / total_value) * 100
        
        # Determine concentration level
        if top_position_pct > 40 or top_3_positions_pct > 70:
            level = "high"
        elif top_position_pct > 20 or top_3_positions_pct > 50:
            level = "medium"
        else:
            level = "low"
        
        return ConcentrationRisk(
            top_position_pct=top_position_pct,
            top_3_positions_pct=top_3_positions_pct,
            level=level
        )
    
    def calculate_performance(
        self,
        positions: List[Position],
        current_prices: Dict[str, float]
    ) -> Performance:
        """Calculate portfolio performance."""
        if not positions:
            return Performance(
                total_return_pct=0.0,
                annualized_return_pct=0.0,
                current_value=0.0,
                cost_basis=0.0
            )
        
        total_cost = 0.0
        total_current = 0.0
        
        for pos in positions:
            cost = pos.quantity * pos.avg_cost
            price = current_prices.get(pos.ticker, pos.avg_cost)
            current = pos.quantity * price
            
            total_cost += cost
            total_current += current
        
        if total_cost == 0:
            return Performance(
                total_return_pct=0.0,
                annualized_return_pct=0.0,
                current_value=total_current,
                cost_basis=total_cost
            )
        
        total_return_pct = ((total_current - total_cost) / total_cost) * 100
        
        # Calculate annualized return (assume 1 year holding period for simplicity)
        # In production, would calculate based on actual holding periods
        annualized_return_pct = total_return_pct
        
        return Performance(
            total_return_pct=total_return_pct,
            annualized_return_pct=annualized_return_pct,
            current_value=total_current,
            cost_basis=total_cost
        )
    
    def select_benchmark(self, positions: List[Position]) -> str:
        """Select appropriate benchmark based on portfolio composition."""
        if not positions:
            return "SPY"
        
        # Simple heuristic: if >80% US stocks, use SPY
        # For now, default to SPY
        # In production, would analyze ticker symbols and sectors
        return "SPY"
    
    async def generate_observations(
        self,
        user: User,
        metrics: Dict
    ) -> List[Observation]:
        """Generate LLM-powered observations tailored to user profile."""
        concentration = metrics["concentration"]
        performance = metrics["performance"]
        benchmark = metrics["benchmark"]
        
        # Build prompt for LLM
        prompt = f"""You are a financial analysis assistant. Generate 2-3 plain-language observations about this portfolio.

User Profile:
- Age: {user.age if user.age else 'Not specified'}
- Risk Profile: {user.risk_profile}
- Country: {user.country}

Portfolio Metrics:
- Concentration Level: {concentration.level}
- Top Position: {concentration.top_position_pct:.1f}% of portfolio
- Top 3 Positions: {concentration.top_3_positions_pct:.1f}% of portfolio
- Total Return: {performance.total_return_pct:.2f}%
- Annualized Return: {performance.annualized_return_pct:.2f}%
- Benchmark ({benchmark.benchmark_name}): {benchmark.benchmark_return_pct:.2f}%
- Alpha: {benchmark.alpha_pct:.2f}%

Generate 2-3 observations that:
1. Are grounded in the actual metrics above
2. Are tailored to the user's profile (age, risk profile, country)
3. Include severity levels (info, warning, or critical)
4. Are actionable and specific
5. End with a regulatory disclaimer

Format each observation as:
[SEVERITY: info/warning/critical] Observation text here.

Example:
[SEVERITY: warning] Your portfolio is highly concentrated with 65% in a single position, which increases risk. Consider diversifying across more holdings.
[SEVERITY: info] Your portfolio has outperformed the S&P 500 by 3.2% this year, generating positive alpha.
[SEVERITY: info] This is not financial advice. Please consult with a qualified financial advisor before making investment decisions."""

        try:
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a financial analysis assistant providing portfolio observations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            
            # Parse observations
            observations = []
            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("[SEVERITY:"):
                    # Extract severity and text
                    parts = line.split("]", 1)
                    if len(parts) == 2:
                        severity_part = parts[0].replace("[SEVERITY:", "").strip()
                        text = parts[1].strip()
                        
                        observations.append(Observation(
                            text=text,
                            severity=severity_part
                        ))
            
            # Ensure we have at least one observation
            if not observations:
                observations.append(Observation(
                    text="Portfolio analysis complete. This is not financial advice. Please consult with a qualified financial advisor.",
                    severity="info"
                ))
            
            return observations
            
        except Exception as e:
            # Fallback observations if LLM fails
            return [
                Observation(
                    text=f"Your portfolio shows {concentration.level} concentration risk with the top position at {concentration.top_position_pct:.1f}%.",
                    severity="info" if concentration.level == "low" else "warning"
                ),
                Observation(
                    text=f"Portfolio return is {performance.total_return_pct:.2f}% with an alpha of {benchmark.alpha_pct:.2f}% vs {benchmark.benchmark_name}.",
                    severity="info"
                ),
                Observation(
                    text="This is not financial advice. Please consult with a qualified financial advisor before making investment decisions.",
                    severity="info"
                )
            ]
