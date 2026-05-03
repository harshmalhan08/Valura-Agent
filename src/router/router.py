"""Router for dispatching queries to specialist agents."""

import logging
from typing import Dict, Any, Optional

from ..models.domain import User
from ..models.api import ClassificationResult, AgentType, PortfolioHealthResponse
from ..agents.portfolio_health import PortfolioHealthAgent
from ..mcp_client.client import MCPClient

logger = logging.getLogger(__name__)


class Router:
    """
    Routes classified queries to appropriate specialist agents.
    
    Maintains agent registry with:
    - Portfolio Health Agent (fully implemented)
    - 9 stub agents (return structured "not implemented" responses)
    
    Never crashes regardless of target agent.
    """
    
    def __init__(
        self,
        mcp_client: Optional[MCPClient] = None,
        openai_api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        """
        Initialize Router with agent registry.
        
        Args:
            mcp_client: MCP client for market data (optional)
            openai_api_key: OpenAI API key for agents
            model: OpenAI model to use
        """
        self.mcp_client = mcp_client or MCPClient()
        
        # Initialize Portfolio Health Agent (fully implemented)
        self.portfolio_health_agent = PortfolioHealthAgent(
            mcp_client=self.mcp_client,
            openai_api_key=openai_api_key,
            model=model
        )
        
        # Agent registry mapping
        self.agents = {
            AgentType.PORTFOLIO_HEALTH: self.portfolio_health_agent,
            # All other agents are stubs
            AgentType.MARKET_RESEARCH: None,
            AgentType.INVESTMENT_STRATEGY: None,
            AgentType.FINANCIAL_PLANNING: None,
            AgentType.FINANCIAL_CALCULATOR: None,
            AgentType.RISK_ASSESSMENT: None,
            AgentType.PRODUCT_RECOMMENDATION: None,
            AgentType.PREDICTIVE_ANALYSIS: None,
            AgentType.CUSTOMER_SUPPORT: None,
            AgentType.GENERAL_QUERY: None,
        }
    
    async def route(
        self,
        classification: ClassificationResult,
        user: User
    ) -> Dict[str, Any]:
        """
        Route query to appropriate agent.
        
        Args:
            classification: Classification result with intent and entities
            user: User data including portfolio
            
        Returns:
            Agent response as dictionary
        """
        target_agent = classification.target_agent
        
        try:
            # Route to Portfolio Health Agent if fully implemented
            if target_agent == AgentType.PORTFOLIO_HEALTH:
                logger.info(f"Routing to Portfolio Health Agent for user {user.user_id}")
                response = await self.portfolio_health_agent.execute(user, classification)
                
                # Convert to dictionary
                return {
                    "agent": "portfolio_health",
                    "intent": classification.intent,
                    "response": response.model_dump()
                }
            
            # All other agents return structured stub responses
            else:
                logger.info(f"Routing to stub agent: {target_agent.value}")
                return self._create_stub_response(classification, target_agent)
        
        except Exception as e:
            logger.error(f"Error routing to agent {target_agent.value}: {e}")
            
            # Return error response without crashing
            return {
                "agent": target_agent.value,
                "intent": classification.intent,
                "error": "An error occurred while processing your request. Please try again.",
                "entities": classification.entities.model_dump() if classification.entities else {}
            }
    
    def _create_stub_response(
        self,
        classification: ClassificationResult,
        target_agent: AgentType
    ) -> Dict[str, Any]:
        """
        Create structured stub response for unimplemented agents.
        
        Args:
            classification: Classification result
            target_agent: Target agent type
            
        Returns:
            Structured stub response
        """
        # Agent-specific stub messages
        stub_messages = {
            AgentType.MARKET_RESEARCH: "Market research functionality is coming soon. I can help you with portfolio health analysis in the meantime.",
            AgentType.INVESTMENT_STRATEGY: "Investment strategy recommendations are coming soon. I can analyze your current portfolio health if you'd like.",
            AgentType.FINANCIAL_PLANNING: "Financial planning tools are coming soon. I can provide insights on your current portfolio in the meantime.",
            AgentType.FINANCIAL_CALCULATOR: "Financial calculators are coming soon. I can help you understand your portfolio performance for now.",
            AgentType.RISK_ASSESSMENT: "Risk assessment tools are coming soon. I can analyze your portfolio concentration risk if you'd like.",
            AgentType.PRODUCT_RECOMMENDATION: "Product recommendations are coming soon. I can review your current holdings in the meantime.",
            AgentType.PREDICTIVE_ANALYSIS: "Predictive analysis is coming soon. I can show you your portfolio's historical performance for now.",
            AgentType.CUSTOMER_SUPPORT: "Customer support integration is coming soon. Please contact support@valura.ai for assistance.",
            AgentType.GENERAL_QUERY: "I'm here to help! I can analyze your portfolio health, or answer questions about investing. What would you like to know?",
        }
        
        message = stub_messages.get(
            target_agent,
            "This feature is not yet implemented. I can help you with portfolio health analysis."
        )
        
        return {
            "agent": target_agent.value,
            "intent": classification.intent,
            "message": message,
            "status": "not_implemented",
            "entities": classification.entities.model_dump() if classification.entities else {},
            "suggestions": [
                "Ask about your portfolio health",
                "Check your portfolio performance",
                "Review your concentration risk"
            ]
        }
