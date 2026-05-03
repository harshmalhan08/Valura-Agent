"""Fixtures loader utility for test data"""

import json
from pathlib import Path
from typing import Any, List, Dict

from src.models.domain import User


# Get the fixtures directory path
FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures"


def load_user_fixture(filename: str) -> User:
    """
    Load user profile from fixtures/users/ directory.
    
    Args:
        filename: User fixture filename (e.g., "user_001_active_trader_us.json")
        
    Returns:
        User: Parsed user profile
        
    Example:
        >>> user = load_user_fixture("user_001_active_trader_us.json")
        >>> print(user.user_id)
        'usr_001'
    """
    filepath = FIXTURES_DIR / "users" / filename
    
    if not filepath.exists():
        raise FileNotFoundError(f"User fixture not found: {filepath}")
    
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return User(**data)


def load_test_queries(filename: str) -> List[Dict[str, Any]]:
    """
    Load test queries from fixtures/test_queries/ directory.
    
    Args:
        filename: Test queries filename (e.g., "intent_classification.json", "safety_pairs.json")
        
    Returns:
        List[Dict]: List of test query dictionaries
        
    Example:
        >>> queries = load_test_queries("intent_classification.json")
        >>> print(len(queries))
        60
    """
    filepath = FIXTURES_DIR / "test_queries" / filename
    
    if not filepath.exists():
        raise FileNotFoundError(f"Test queries fixture not found: {filepath}")
    
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Handle both direct list and nested structure
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and "queries" in data:
        return data["queries"]
    else:
        raise ValueError(f"Unexpected fixture format in {filename}")


def load_conversation_fixture(filename: str) -> Dict[str, Any]:
    """
    Load conversation test case from fixtures/conversations/ directory.
    
    Args:
        filename: Conversation fixture filename (e.g., "follow_up_session.json")
        
    Returns:
        Dict: Conversation test case with session_id, turns, etc.
        
    Example:
        >>> conv = load_conversation_fixture("follow_up_session.json")
        >>> print(conv["session_id"])
        'sess_followup_001'
    """
    filepath = FIXTURES_DIR / "conversations" / filename
    
    if not filepath.exists():
        raise FileNotFoundError(f"Conversation fixture not found: {filepath}")
    
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return data


def load_all_user_fixtures() -> List[User]:
    """
    Load all user fixtures from fixtures/users/ directory.
    
    Returns:
        List[User]: List of all user profiles
    """
    users_dir = FIXTURES_DIR / "users"
    
    if not users_dir.exists():
        return []
    
    users = []
    for filepath in users_dir.glob("*.json"):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            users.append(User(**data))
    
    return users


def load_safety_queries() -> List[Dict[str, Any]]:
    """
    Load safety test queries from fixtures/test_queries/safety_pairs.json.
    
    Returns:
        List[Dict]: List of safety query test cases
    """
    return load_test_queries("safety_pairs.json")


def load_intent_classification_queries() -> List[Dict[str, Any]]:
    """
    Load intent classification test queries from fixtures/test_queries/intent_classification.json.
    
    Returns:
        List[Dict]: List of intent classification test cases
    """
    return load_test_queries("intent_classification.json")
