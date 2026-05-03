"""In-memory session manager for conversation history."""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict

from ..models.api import ConversationTurn, ClassificationResult

logger = logging.getLogger(__name__)


class SessionManager:
    """
    In-memory session manager for conversation history.
    
    Stores conversation turns in memory for context-aware query processing.
    No database required - simple and fast for development and testing.
    """
    
    def __init__(self):
        """Initialize in-memory session storage."""
        # sessions[session_id] = {
        #     "user_id": str,
        #     "created_at": datetime,
        #     "turns": List[ConversationTurn]
        # }
        self.sessions: Dict[str, dict] = {}
        logger.info("SessionManager initialized with in-memory storage")
    
    def create_session(self, session_id: str, user_id: str) -> None:
        """
        Create a new session.
        
        Args:
            session_id: Unique session identifier
            user_id: User identifier
        """
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "user_id": user_id,
                "created_at": datetime.now(),
                "turns": []
            }
            logger.info(f"Created new session: {session_id} for user {user_id}")
        else:
            logger.debug(f"Session {session_id} already exists")
    
    def get_history(self, session_id: str) -> List[ConversationTurn]:
        """
        Get conversation history for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of conversation turns (empty if session doesn't exist)
        """
        if session_id not in self.sessions:
            logger.debug(f"Session {session_id} not found, returning empty history")
            return []
        
        turns = self.sessions[session_id]["turns"]
        logger.debug(f"Retrieved {len(turns)} turns for session {session_id}")
        return turns
    
    def store_turn(
        self,
        session_id: str,
        user_query: str,
        agent_response: str,
        classification: ClassificationResult
    ) -> None:
        """
        Store a conversation turn.
        
        Args:
            session_id: Session identifier
            user_query: User's query text
            agent_response: Agent's response text
            classification: Classification result for this turn
        """
        # Create session if it doesn't exist
        if session_id not in self.sessions:
            logger.warning(f"Session {session_id} not found, creating it")
            self.sessions[session_id] = {
                "user_id": "unknown",
                "created_at": datetime.now(),
                "turns": []
            }
        
        # Get current turn number
        turn_number = len(self.sessions[session_id]["turns"]) + 1
        
        # Create conversation turn
        turn = ConversationTurn(
            turn_number=turn_number,
            user_query=user_query,
            agent_response=agent_response,
            classification=classification,
            timestamp=datetime.now()
        )
        
        # Store turn
        self.sessions[session_id]["turns"].append(turn)
        
        logger.info(f"Stored turn {turn_number} for session {session_id}")
    
    def get_session_count(self) -> int:
        """Get total number of sessions."""
        return len(self.sessions)
    
    def get_turn_count(self, session_id: str) -> int:
        """Get number of turns in a session."""
        if session_id not in self.sessions:
            return 0
        return len(self.sessions[session_id]["turns"])
    
    def clear_session(self, session_id: str) -> None:
        """
        Clear a session's history.
        
        Args:
            session_id: Session identifier
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Cleared session {session_id}")
        else:
            logger.debug(f"Session {session_id} not found, nothing to clear")
    
    def clear_all(self) -> None:
        """Clear all sessions."""
        count = len(self.sessions)
        self.sessions.clear()
        logger.info(f"Cleared all {count} sessions")
