"""Pattern-based safety guard for harmful query detection"""

import re
from typing import Pattern, List, Dict, Optional, Union

from src.models.api import SafetyVerdict


# =============================================================================
# Harmful Category Patterns
# =============================================================================

INSIDER_TRADING_PATTERNS: List[str] = [
    r"\b(insider|non-public|material information)\b",
    r"\b(tip from|friend at|works? at .{1,30}(told|gave|shared))\b",
    r"\b(before .{1,20}announcement|ahead of .{1,20}earnings)\b",
    r"\b(pre-market .{1,20}news|confidential|proprietary)\b",
    r"\b(internal .{1,20}memo|leaked|unannounced)\b",
    r"\b(material non-public|MNPI)\b",
]

MARKET_MANIPULATION_PATTERNS: List[str] = [
    r"\b(pump and dump|pump.{1,10}dump)\b",
    r"\b(coordinate.{0,30}(buy|purchase|sell|manipulate|market|to manipulate))\b",
    r"\b(organize.{1,20}(buy|purchase))\b",
    r"\b(group.{1,20}buying|collective.{1,20}buying)\b",
    r"\b(spoof|layering|wash trad(e|ing))\b",
    r"\b(painting the tape|manipulate.{1,20}(price|stock))\b",
    r"\b(artificial.{1,20}demand|fake.{1,20}volume)\b",
    r"\b(move.{1,20}price|drive.{1,20}(up|down))\b",
    r"\b(manipulate.{1,30}(stock|market|price))\b",
    r"\b(how.{0,20}(do|can).{0,20}(i|we).{0,20}coordinate.{0,30}manipulate)\b",
    r"\bcoordinate\s+to\s+manipulate\b",
]

MONEY_LAUNDERING_PATTERNS: List[str] = [
    r"\bhide\s+(illegal\s+)?funds\b",
    r"\blaunder\s+money\b",
    r"\b(launder|laundering).{0,20}(money|funds)\b",
    r"\b(money|funds).{0,20}(launder|laundering)\b",
    r"\b(structure.{1,20}transaction|split.{1,20}deposit)\b",
    r"\b(avoid.{1,20}reporting|evade.{1,20}reporting)\b",
    r"\b(layer|layering|placement|integration|smurfing)\b",
    r"\b(cash.{1,20}business|shell.{1,20}company)\b",
    r"\b(offshore.{1,20}account)\b",
    r"\b(obscure.{1,20}source|conceal.{1,20}origin)\b",
    r"\b(10k reporting|reporting threshold)\b",
    r"\b(money.{0,20}laundering.{0,20}techniques)\b",
    r"\b(how.{0,20}(do|can).{0,20}(i|we).{0,20}launder)\b",
]

GUARANTEED_RETURNS_PATTERNS: List[str] = [
    r"\b(guarantee.{0,20}(return|profit|gain|50%))\b",
    r"\b(guaranteed.{0,20}(return|profit|gain))\b",
    r"\b(promise.{1,20}(double|triple|return))\b",
    r"\b(100% certain|can't lose|risk-free)\b",
    r"\b(foolproof|guaranteed profit)\b",
    r"\b(sure thing|certain.{1,20}(win|profit))\b",
    r"\b(no risk|zero risk)\b",
    r"\b(risk.?free.{0,20}(way|investment))\b",
    r"\b(investment.{0,20}has.{0,20}guaranteed.{0,20}profits?)\b",
    r"\b(give.{0,20}me.{0,20}guaranteed.{0,20}returns?)\b",
]

RECKLESS_ADVICE_PATTERNS: List[str] = [
    r"\b(put|invest).{0,20}(all|entire).{0,30}(money|savings|retirement|emergency fund)\b",
    r"\b(all.{0,10}money).{0,20}(in|on).{0,20}(one|single)\b",
    r"\b(mortgage.{1,20}house for|sell.{1,20}house.{1,20}invest)\b",
    r"\b(margin loan to buy|leverage.{1,20}(all|everything))\b",
    r"\b(borrow.{1,20}invest|take.{1,20}loan.{1,20}(buy|invest))\b",
    r"\b(all.?in on|yolo|bet everything)\b",
    r"\b(entire.{0,20}savings).{0,20}(in|on)\b",
]

SANCTIONS_EVASION_PATTERNS: List[str] = [
    r"\b(evade|bypass|circumvent).{0,20}sanction\b",
    r"\b(sanction.{0,20}(evade|bypass|circumvent))\b",
    r"\b(bypass.{1,20}sanction|evade.{1,20}sanction)\b",
    r"\b(route.{1,20}through shell|circumvent.{1,20}OFAC)\b",
    r"\b(sanctioned.{1,20}(company|entity|country))\b",
    r"\b(without.{1,20}traced|avoid.{1,20}detection)\b",
    r"\b(bypass.{0,20}trade.{0,20}restrictions)\b",
    r"\b(circumvent.{0,20}financial.{0,20}sanctions)\b",
    r"\b(how.{0,20}(can|do).{0,20}(i|we).{0,20}(evade|circumvent).{0,20}sanctions?)\b",
    r"\bcircumvent\s+financial\s+sanctions\b",
]

# Educational query patterns (should pass through)
EDUCATIONAL_PATTERNS: List[str] = [
    r"\b(what is|what are|explain|define|describe)\b",
    r"\b(why is|why are)\b",
    r"\b(difference between|compare)\b",
    r"\b(penalties|regulations|rules)\b",
    r"\b(learn about|understand|educational)\b",
    r"\b(is.{1,20}illegal|are.{1,20}illegal)\b",  # "is X illegal?" is educational
]


# =============================================================================
# Category Response Messages
# =============================================================================

BLOCK_MESSAGES: Dict[str, str] = {
    "insider_trading": (
        "I cannot assist with trading on material non-public information. "
        "Insider trading is illegal under SEC regulations and carries severe penalties "
        "including fines and imprisonment. If you have questions about insider trading "
        "regulations for educational purposes, I'm happy to help."
    ),
    "market_manipulation": (
        "I cannot help with market manipulation schemes such as pump-and-dump, "
        "coordinated trading, or spoofing. These activities are illegal and undermine "
        "market integrity. Violators face significant fines and criminal prosecution. "
        "If you'd like to learn about market manipulation regulations, I can provide "
        "educational information."
    ),
    "money_laundering": (
        "I cannot assist with structuring transactions to evade reporting requirements "
        "or obscure the source of funds. This violates anti-money laundering (AML) "
        "regulations and is a serious criminal offense. If you have questions about "
        "AML compliance requirements for educational purposes, I'm happy to explain."
    ),
    "guaranteed_returns": (
        "I cannot promise guaranteed returns or risk-free investments. All investments "
        "carry risk, and claims of guaranteed returns are typically fraudulent. "
        "Past performance does not guarantee future results. I can help you understand "
        "risk-adjusted returns and realistic investment expectations."
    ),
    "reckless_advice": (
        "I cannot recommend putting your entire emergency fund, retirement savings, "
        "or taking on excessive leverage for high-risk investments. This violates "
        "prudent investment principles and fiduciary duty. I can help you develop "
        "a balanced investment strategy appropriate for your risk tolerance and goals."
    ),
    "sanctions_evasion": (
        "I cannot assist with evading sanctions or circumventing OFAC compliance "
        "requirements. Sanctions evasion is a serious criminal offense with severe "
        "penalties. If you have questions about sanctions compliance for educational "
        "purposes, I can provide information."
    ),
}


# =============================================================================
# Safety Guard Implementation
# =============================================================================

class SafetyGuard:
    """
    Pattern-based safety guard for detecting harmful queries.
    
    Blocks queries in 6 harmful categories:
    - insider_trading
    - market_manipulation
    - money_laundering
    - guaranteed_returns
    - reckless_advice
    - sanctions_evasion
    
    Passes through educational queries about harmful topics.
    
    Performance target: <10ms per query
    """
    
    def __init__(self):
        """Initialize safety guard with compiled regex patterns"""
        # Compile patterns for performance
        self.insider_trading_patterns = [re.compile(p, re.IGNORECASE) for p in INSIDER_TRADING_PATTERNS]
        self.market_manipulation_patterns = [re.compile(p, re.IGNORECASE) for p in MARKET_MANIPULATION_PATTERNS]
        self.money_laundering_patterns = [re.compile(p, re.IGNORECASE) for p in MONEY_LAUNDERING_PATTERNS]
        self.guaranteed_returns_patterns = [re.compile(p, re.IGNORECASE) for p in GUARANTEED_RETURNS_PATTERNS]
        self.reckless_advice_patterns = [re.compile(p, re.IGNORECASE) for p in RECKLESS_ADVICE_PATTERNS]
        self.sanctions_evasion_patterns = [re.compile(p, re.IGNORECASE) for p in SANCTIONS_EVASION_PATTERNS]
        
        # Educational patterns (queries that should pass through)
        self.educational_patterns = [re.compile(p, re.IGNORECASE) for p in EDUCATIONAL_PATTERNS]
    
    def _is_educational(self, query: str) -> bool:
        """Check if query is educational (asking about harmful topics for learning)"""
        return any(pattern.search(query) for pattern in self.educational_patterns)
    
    def _check_category(self, query: str, patterns: List[Pattern], category: str) -> Optional[SafetyVerdict]:
        """
        Check if query matches patterns for a specific category.
        
        Returns SafetyVerdict if blocked, None if safe.
        """
        for pattern in patterns:
            if pattern.search(query):
                # Check if it's an educational query
                if self._is_educational(query):
                    return None  # Pass through educational queries
                
                # Block harmful query
                return SafetyVerdict(
                    is_safe=False,
                    category=category,
                    response=BLOCK_MESSAGES[category]
                )
        
        return None
    
    def check_query(self, query: str) -> SafetyVerdict:
        """
        Check if query is safe to process.
        
        Args:
            query: User query text
            
        Returns:
            SafetyVerdict with is_safe, category, and response
            
        Performance: <10ms per query (synchronous, no LLM calls)
        """
        # Check each category in order
        verdict = self._check_category(query, self.insider_trading_patterns, "insider_trading")
        if verdict:
            return verdict
        
        verdict = self._check_category(query, self.market_manipulation_patterns, "market_manipulation")
        if verdict:
            return verdict
        
        verdict = self._check_category(query, self.money_laundering_patterns, "money_laundering")
        if verdict:
            return verdict
        
        verdict = self._check_category(query, self.guaranteed_returns_patterns, "guaranteed_returns")
        if verdict:
            return verdict
        
        verdict = self._check_category(query, self.reckless_advice_patterns, "reckless_advice")
        if verdict:
            return verdict
        
        verdict = self._check_category(query, self.sanctions_evasion_patterns, "sanctions_evasion")
        if verdict:
            return verdict
        
        # Query is safe
        return SafetyVerdict(is_safe=True, category=None, response=None)


# =============================================================================
# Convenience Function
# =============================================================================

# Global instance for convenience
_guard = SafetyGuard()


def check_query(query: str) -> SafetyVerdict:
    """
    Convenience function to check query safety using global SafetyGuard instance.
    
    Args:
        query: User query text
        
    Returns:
        SafetyVerdict with is_safe, category, and response
        
    Example:
        >>> verdict = check_query("How can I profit from insider information?")
        >>> print(verdict.is_safe)
        False
        >>> print(verdict.category)
        'insider_trading'
    """
    return _guard.check_query(query)
