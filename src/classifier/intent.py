"""Intent classifier using OpenAI structured outputs for query routing."""

import os
from typing import Optional, List
from openai import AsyncOpenAI, AsyncAzureOpenAI
from pydantic import BaseModel

from ..models.api import (
    ClassificationResult,
    ExtractedEntities,
    AgentType,
    SafetyVerdict,
    ConversationTurn,
)


class IntentClassifier:
    """
    Classifies user queries using OpenAI structured outputs.
    
    Extracts intent, entities, and routes to appropriate agent.
    Handles conversation context for pronoun resolution and topic tracking.
    Supports both standard OpenAI and Azure OpenAI.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        """
        Initialize the Intent Classifier.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY or AZURE_OPENAI_API_KEY env var)
            model: OpenAI model to use (defaults to OPENAI_MODEL env var or gpt-4o)
        """
        # Check if using Azure OpenAI
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        
        if azure_endpoint and azure_api_key:
            # Use Azure OpenAI
            self.client = AsyncAzureOpenAI(
                api_key=azure_api_key,
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
                azure_endpoint=azure_endpoint
            )
            self.model = model or os.getenv("AZURE_OPENAI_DEPLOYMENT_CHAT") or os.getenv("OPENAI_MODEL", "gpt-4o")
            self.is_azure = True
        else:
            # Use standard OpenAI
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY or AZURE_OPENAI_API_KEY must be provided or set in environment")
            
            self.client = AsyncOpenAI(api_key=self.api_key)
            self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
            self.is_azure = False
    
    async def classify(
        self,
        query: str,
        conversation_history: List[ConversationTurn]
    ) -> ClassificationResult:
        """
        Classify a user query and extract entities.
        
        Args:
            query: The user's query text
            conversation_history: Previous conversation turns for context
            
        Returns:
            ClassificationResult with intent, entities, target_agent, and confidence
        """
        try:
            # Build prompt with conversation context
            prompt = self._build_prompt(query, conversation_history)
            
            # Call OpenAI with structured output
            response = await self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format=ClassificationResult,
                temperature=0.0
            )
            
            # Extract structured result
            result = response.choices[0].message.parsed
            
            # Ensure safety_verdict is set (default to safe)
            if result.safety_verdict is None:
                result.safety_verdict = SafetyVerdict(
                    is_safe=True,
                    category=None,
                    response=None
                )
            
            return result
            
        except Exception as e:
            # On LLM failure, route to general_query agent
            return ClassificationResult(
                intent="general_query",
                entities=ExtractedEntities(),
                target_agent=AgentType.GENERAL_QUERY,
                safety_verdict=SafetyVerdict(is_safe=True, category=None, response=None),
                confidence=0.0
            )
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for classification."""
        return """You are an intent classifier for a financial AI assistant.

Your job is to:
1. Classify the user's intent into one of these categories:
   - portfolio_status: User wants to know about their portfolio health, performance, or holdings
   - market_information: User wants market data, stock prices, or company information
   - investment_advice: User wants recommendations on what to buy/sell/hold
   - financial_planning: User wants long-term planning (retirement, education, goals)
   - financial_calculator: User wants numerical calculations (compound interest, returns)
   - risk_assessment: User wants risk metrics or risk analysis
   - product_recommendation: User wants product suggestions (ETFs, funds, accounts)
   - predictive_analysis: User wants forecasts or predictions
   - customer_support: User has platform issues or account problems
   - general_query: Educational questions, greetings, or conversational queries

2. Extract entities from the query:
   - tickers: Stock symbols (uppercase with exchange suffix, e.g., AAPL, TSLA)
   - amount: Monetary amounts (e.g., 10000, 50000)
   - currency: Currency codes (USD, EUR, GBP, JPY, CAD)
   - rate: Interest rates or return rates (e.g., 0.05 for 5%)
   - period_years: Time periods in years (e.g., 30, 10)
   - frequency: Payment frequency (monthly, quarterly, annually)
   - horizon: Investment horizon (short_term, medium_term, long_term)
   - time_period: Time ranges (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
   - topics: General topics (e.g., diversification, risk, taxes)
   - sectors: Market sectors (e.g., technology, healthcare, finance)
   - index: Market indices (e.g., S&P 500, NASDAQ, Dow Jones)
   - action: Investment actions (buy, sell, hold, hedge, rebalance)
   - goal: Financial goals (retirement, education, house, FIRE, emergency_fund)

3. Route to the appropriate agent based on intent:
   - portfolio_status → portfolio_health
   - market_information → market_research
   - investment_advice → investment_strategy
   - financial_planning → financial_planning
   - financial_calculator → financial_calculator
   - risk_assessment → risk_assessment
   - product_recommendation → product_recommendation
   - predictive_analysis → predictive_analysis
   - customer_support → customer_support
   - general_query → general_query

4. Use conversation context to resolve pronouns and track topics:
   - If user says "it" or "that stock", look at previous turns to identify the ticker
   - If user switches topics, don't carry forward inappropriate context
   - If user asks follow-up questions, maintain entity context

5. Provide a confidence score (0.0 to 1.0) for your classification.

Return a structured ClassificationResult with all fields populated."""

    def _build_prompt(
        self,
        query: str,
        conversation_history: List[ConversationTurn]
    ) -> str:
        """
        Build the classification prompt with conversation context.
        
        Args:
            query: Current user query
            conversation_history: Previous conversation turns
            
        Returns:
            Formatted prompt string
        """
        prompt_parts = []
        
        # Add conversation history for context
        if conversation_history:
            prompt_parts.append("Conversation history:")
            for turn in conversation_history[-5:]:  # Last 5 turns for context
                prompt_parts.append(f"User: {turn.user_query}")
                if turn.agent_response:
                    # Truncate long responses
                    response_preview = turn.agent_response[:200]
                    if len(turn.agent_response) > 200:
                        response_preview += "..."
                    prompt_parts.append(f"Assistant: {response_preview}")
            prompt_parts.append("")
        
        # Add current query
        prompt_parts.append(f"Current query: {query}")
        prompt_parts.append("")
        prompt_parts.append("Classify this query and extract all relevant entities.")
        
        return "\n".join(prompt_parts)
