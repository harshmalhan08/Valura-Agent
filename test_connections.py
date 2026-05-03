"""
Comprehensive Connection Test for Valura AI System
Tests: Azure OpenAI, MCP Client, yfinance integration
"""

import asyncio
import os
import sys
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

def print_success(text: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")

def print_error(text: str):
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")

def print_info(text: str):
    """Print info message."""
    print(f"{Colors.YELLOW}ℹ {text}{Colors.RESET}")

def print_result(test_name: str, passed: bool, details: str = ""):
    """Print test result."""
    status = f"{Colors.GREEN}PASSED{Colors.RESET}" if passed else f"{Colors.RED}FAILED{Colors.RESET}"
    print(f"\n{Colors.BOLD}{test_name}:{Colors.RESET} {status}")
    if details:
        print(f"  {details}")


async def test_azure_openai_connection() -> Dict[str, Any]:
    """Test Azure OpenAI connection and API call."""
    print_header("Testing Azure OpenAI Connection")
    
    result = {
        "name": "Azure OpenAI Connection",
        "passed": False,
        "details": "",
        "error": None
    }
    
    try:
        # Check environment variables
        print_info("Checking environment variables...")
        required_vars = [
            "AZURE_OPENAI_API_KEY",
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_DEPLOYMENT_CHAT",
            "AZURE_OPENAI_API_VERSION"
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            result["error"] = f"Missing environment variables: {', '.join(missing_vars)}"
            print_error(result["error"])
            return result
        
        print_success("All required environment variables found")
        
        # Import Azure OpenAI
        print_info("Importing Azure OpenAI SDK...")
        from openai import AzureOpenAI
        print_success("Azure OpenAI SDK imported successfully")
        
        # Initialize client
        print_info("Initializing Azure OpenAI client...")
        client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        print_success("Azure OpenAI client initialized")
        
        # Test API call
        print_info("Making test API call...")
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_CHAT"),
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Connection successful' if you can read this."}
            ],
            max_tokens=50,
            temperature=0.7
        )
        
        response_text = response.choices[0].message.content
        print_success(f"API call successful! Response: {response_text}")
        
        # Check token usage
        usage = response.usage
        print_info(f"Token usage - Prompt: {usage.prompt_tokens}, Completion: {usage.completion_tokens}, Total: {usage.total_tokens}")
        
        result["passed"] = True
        result["details"] = f"Response: {response_text[:100]}... | Tokens: {usage.total_tokens}"
        
    except ImportError as e:
        result["error"] = f"Import error: {str(e)}"
        print_error(result["error"])
    except Exception as e:
        result["error"] = f"Error: {str(e)}"
        print_error(result["error"])
    
    return result


async def test_mcp_client_connection() -> Dict[str, Any]:
    """Test MCP client connection to yfinance."""
    print_header("Testing MCP Client Connection")
    
    result = {
        "name": "MCP Client Connection",
        "passed": False,
        "details": "",
        "error": None
    }
    
    try:
        # Import MCP client
        print_info("Importing MCP client...")
        src_path = os.path.join(os.path.dirname(__file__), 'src')
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        
        from src.mcp_client.client import MCPClient
        print_success("MCP client imported successfully")
        
        # Initialize MCP client
        print_info("Initializing MCP client...")
        mcp_client = MCPClient()
        print_success("MCP client initialized")
        
        # Connect to MCP server
        print_info("Connecting to yfinance MCP server...")
        await mcp_client.connect()
        print_success("Connected to MCP server")
        
        # Test tool call - get ticker info
        print_info("Testing yfinance_get_ticker_info for AAPL...")
        ticker_result = await mcp_client.call_tool(
            "yfinance_get_ticker_info",
            {"symbol": "AAPL"}
        )
        
        if ticker_result and "content" in ticker_result:
            print_success("Successfully fetched AAPL ticker info")
            # Parse the response
            import json
            ticker_data = json.loads(ticker_result["content"][0]["text"])
            current_price = ticker_data.get("currentPrice", "N/A")
            market_cap = ticker_data.get("marketCap", "N/A")
            print_info(f"AAPL - Price: ${current_price}, Market Cap: ${market_cap:,}")
            
            result["passed"] = True
            result["details"] = f"AAPL Price: ${current_price}, Market Cap: ${market_cap:,}"
        else:
            result["error"] = "No data returned from MCP server"
            print_error(result["error"])
        
        # Disconnect
        print_info("Disconnecting from MCP server...")
        await mcp_client.disconnect()
        print_success("Disconnected from MCP server")
        
    except ImportError as e:
        result["error"] = f"Import error: {str(e)}"
        print_error(result["error"])
    except Exception as e:
        result["error"] = f"Error: {str(e)}"
        print_error(result["error"])
    
    return result


async def test_intent_classifier() -> Dict[str, Any]:
    """Test Intent Classifier with Azure OpenAI."""
    print_header("Testing Intent Classifier")
    
    result = {
        "name": "Intent Classifier",
        "passed": False,
        "details": "",
        "error": None
    }
    
    try:
        # Import classifier
        print_info("Importing Intent Classifier...")
        src_path = os.path.join(os.path.dirname(__file__), 'src')
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        
        # Add parent directory to path for absolute imports
        parent_path = os.path.dirname(os.path.dirname(__file__))
        if parent_path not in sys.path:
            sys.path.insert(0, parent_path)
        
        from src.classifier.intent import IntentClassifier
        print_success("Intent Classifier imported successfully")
        
        # Initialize classifier
        print_info("Initializing Intent Classifier...")
        classifier = IntentClassifier()
        print_success("Intent Classifier initialized")
        
        # Test classification
        test_query = "How is my portfolio doing?"
        print_info(f"Testing classification for: '{test_query}'")
        
        classification = await classifier.classify(test_query, [])
        
        print_success("Classification successful!")
        print_info(f"Intent: {classification.intent}")
        print_info(f"Target Agent: {classification.target_agent}")
        print_info(f"Confidence: {classification.confidence}")
        
        result["passed"] = True
        result["details"] = f"Intent: {classification.intent}, Agent: {classification.target_agent}"
        
    except ImportError as e:
        result["error"] = f"Import error: {str(e)}"
        print_error(result["error"])
    except Exception as e:
        result["error"] = f"Error: {str(e)}"
        print_error(result["error"])
    
    return result


async def test_safety_guard() -> Dict[str, Any]:
    """Test Safety Guard."""
    print_header("Testing Safety Guard")
    
    result = {
        "name": "Safety Guard",
        "passed": False,
        "details": "",
        "error": None
    }
    
    try:
        # Import safety guard
        print_info("Importing Safety Guard...")
        src_path = os.path.join(os.path.dirname(__file__), 'src')
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        
        from src.safety.guard import SafetyGuard
        print_success("Safety Guard imported successfully")
        
        # Initialize safety guard
        print_info("Initializing Safety Guard...")
        guard = SafetyGuard()
        print_success("Safety Guard initialized")
        
        # Test safe query
        safe_query = "How is my portfolio doing?"
        print_info(f"Testing safe query: '{safe_query}'")
        verdict = guard.check_query(safe_query)
        
        if verdict.is_safe:
            print_success("Safe query passed correctly")
        else:
            print_error(f"Safe query incorrectly blocked: {verdict.category}")
            result["error"] = "Safe query incorrectly blocked"
            return result
        
        # Test harmful query
        harmful_query = "How can I profit from insider information?"
        print_info(f"Testing harmful query: '{harmful_query}'")
        verdict = guard.check_query(harmful_query)
        
        if not verdict.is_safe:
            print_success(f"Harmful query blocked correctly: {verdict.category}")
            result["passed"] = True
            result["details"] = f"Blocked category: {verdict.category}"
        else:
            print_error("Harmful query not blocked")
            result["error"] = "Harmful query not blocked"
        
    except ImportError as e:
        result["error"] = f"Import error: {str(e)}"
        print_error(result["error"])
    except Exception as e:
        result["error"] = f"Error: {str(e)}"
        print_error(result["error"])
    
    return result


async def test_full_pipeline() -> Dict[str, Any]:
    """Test full pipeline: Safety Guard -> Classifier -> Router."""
    print_header("Testing Full Pipeline")
    
    result = {
        "name": "Full Pipeline",
        "passed": False,
        "details": "",
        "error": None
    }
    
    try:
        # Import components
        print_info("Importing pipeline components...")
        src_path = os.path.join(os.path.dirname(__file__), 'src')
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        
        from src.safety.guard import SafetyGuard
        from src.classifier.intent import IntentClassifier
        from src.router.router import Router
        print_success("All components imported successfully")
        
        # Initialize components
        print_info("Initializing pipeline components...")
        guard = SafetyGuard()
        classifier = IntentClassifier()
        router = Router()
        print_success("All components initialized")
        
        # Test query
        test_query = "How is my portfolio doing?"
        print_info(f"Testing pipeline with query: '{test_query}'")
        
        # Step 1: Safety Guard
        print_info("Step 1: Safety Guard check...")
        verdict = guard.check_query(test_query)
        if not verdict.is_safe:
            result["error"] = f"Query blocked by safety guard: {verdict.category}"
            print_error(result["error"])
            return result
        print_success("Query passed safety guard")
        
        # Step 2: Intent Classifier
        print_info("Step 2: Intent classification...")
        classification = await classifier.classify(test_query, [])
        print_success(f"Query classified - Agent: {classification.target_agent}")
        
        # Step 3: Router
        print_info("Step 3: Routing to agent...")
        # Create mock user data with all required fields
        from src.models.domain import User, Portfolio
        mock_user = User(
            user_id="test_user",
            name="Test User",
            country="US",
            risk_profile="moderate",
            positions=[]
        )
        
        response = await router.route(classification, mock_user)
        print_success(f"Router returned response")
        
        result["passed"] = True
        result["details"] = f"Pipeline completed successfully - Agent: {classification.target_agent}"
        
    except ImportError as e:
        result["error"] = f"Import error: {str(e)}"
        print_error(result["error"])
    except Exception as e:
        result["error"] = f"Error: {str(e)}"
        print_error(result["error"])
    
    return result


async def main():
    """Run all connection tests."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║     VALURA AI SYSTEM - COMPREHENSIVE CONNECTION TEST      ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"{Colors.RESET}")
    
    # Run all tests
    results = []
    
    # Test 1: Azure OpenAI
    results.append(await test_azure_openai_connection())
    
    # Test 2: MCP Client
    results.append(await test_mcp_client_connection())
    
    # Test 3: Safety Guard
    results.append(await test_safety_guard())
    
    # Test 4: Intent Classifier
    results.append(await test_intent_classifier())
    
    # Test 5: Full Pipeline
    results.append(await test_full_pipeline())
    
    # Print summary
    print_header("TEST SUMMARY")
    
    passed_count = sum(1 for r in results if r["passed"])
    total_count = len(results)
    
    for result in results:
        print_result(result["name"], result["passed"], result["details"] or result["error"])
    
    print(f"\n{Colors.BOLD}Overall Result: {passed_count}/{total_count} tests passed{Colors.RESET}")
    
    if passed_count == total_count:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ ALL TESTS PASSED! System is ready.{Colors.RESET}\n")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}✗ Some tests failed. Please check the errors above.{Colors.RESET}\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
