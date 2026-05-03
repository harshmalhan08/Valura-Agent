"""MCP client for connecting to yfmcp server and calling market data tools."""

import asyncio
import json
import logging
from typing import Optional, Any, Dict, List

logger = logging.getLogger(__name__)


class MCPClient:
    """
    Client for connecting to yfmcp MCP server via subprocess.
    
    Provides methods to fetch market data using yfinance tools:
    - yfinance_get_ticker_info: Get current price and company info
    - yfinance_get_price_history: Get historical price data
    - yfinance_search: Search for ticker symbols
    
    Note: This implementation uses subprocess to call uvx yfmcp directly,
    avoiding the need for the MCP SDK which requires Python 3.10+.
    """
    
    def __init__(self, server_command: Optional[List[str]] = None):
        """
        Initialize MCP client.
        
        Args:
            server_command: Command to start MCP server (default: ["py", "-3.12", "-m", "uv", "tool", "run", "yfmcp@latest"])
        """
        self.server_command = server_command or ["py", "-3.12", "-m", "uv", "tool", "run", "yfmcp@latest"]
        self._process: Optional[asyncio.subprocess.Process] = None
        self._connected = False
        self._request_id = 0
    
    async def connect(self) -> None:
        """Connect to the MCP server."""
        if self._connected:
            return
        
        try:
            # Start the MCP server process
            self._process = await asyncio.create_subprocess_exec(
                *self.server_command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Send initialize request
            init_request = {
                "jsonrpc": "2.0",
                "id": self._get_next_id(),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "valura-ai-client",
                        "version": "1.0.0"
                    }
                }
            }
            
            await self._send_request(init_request)
            response = await self._read_response()
            
            if "error" in response:
                raise ConnectionError(f"MCP initialization failed: {response['error']}")
            
            # Send initialized notification
            initialized_notification = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            }
            await self._send_request(initialized_notification)
            
            self._connected = True
            logger.info(f"Connected to MCP server: {' '.join(self.server_command)}")
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            if self._process:
                self._process.kill()
                await self._process.wait()
            raise ConnectionError(f"MCP connection failed: {e}")
    
    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if not self._connected:
            return
        
        try:
            if self._process:
                # Close stdin first to signal shutdown
                if self._process.stdin:
                    self._process.stdin.close()
                
                # Terminate the process
                self._process.terminate()
                
                # Wait for process to exit with timeout
                try:
                    await asyncio.wait_for(self._process.wait(), timeout=2.0)
                except asyncio.TimeoutError:
                    # Force kill if it doesn't terminate gracefully
                    self._process.kill()
                    await self._process.wait()
            
            self._connected = False
            self._process = None
            logger.info("Disconnected from MCP server")
            
        except Exception as e:
            logger.error(f"Error disconnecting from MCP server: {e}")
            self._connected = False
            self._process = None
    
    def _get_next_id(self) -> int:
        """Get next request ID."""
        self._request_id += 1
        return self._request_id
    
    async def _send_request(self, request: Dict[str, Any]) -> None:
        """Send a JSON-RPC request to the server."""
        if not self._process or not self._process.stdin:
            raise ConnectionError("Not connected to MCP server")
        
        request_str = json.dumps(request) + "\n"
        self._process.stdin.write(request_str.encode())
        await self._process.stdin.drain()
    
    async def _read_response(self) -> Dict[str, Any]:
        """Read a JSON-RPC response from the server."""
        if not self._process or not self._process.stdout:
            raise ConnectionError("Not connected to MCP server")
        
        try:
            line = await asyncio.wait_for(
                self._process.stdout.readline(),
                timeout=30.0
            )
            
            if not line:
                raise ConnectionError("Server closed connection")
            
            return json.loads(line.decode())
            
        except asyncio.TimeoutError:
            raise TimeoutError("Server response timeout")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response: {e}")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an MCP tool.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool response as dictionary
            
        Raises:
            ConnectionError: If not connected to server
            TimeoutError: If tool call times out
            Exception: For other errors
        """
        if not self._connected or not self._process:
            raise ConnectionError("Not connected to MCP server. Call connect() first.")
        
        try:
            # Send tool call request
            request = {
                "jsonrpc": "2.0",
                "id": self._get_next_id(),
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            await self._send_request(request)
            response = await self._read_response()
            
            if "error" in response:
                logger.error(f"Tool call error: {response['error']}")
                return {"error": response["error"].get("message", "Unknown error")}
            
            return response.get("result", {})
            
        except asyncio.TimeoutError:
            logger.error(f"Tool call timed out: {tool_name}")
            raise TimeoutError(f"Tool call timed out: {tool_name}")
        except Exception as e:
            logger.error(f"Tool call failed: {tool_name} - {e}")
            return {"error": str(e)}
    
    async def get_ticker_info(self, ticker: str) -> Dict[str, Any]:
        """
        Get current price and company information for a ticker.
        
        Args:
            ticker: Stock ticker symbol (e.g., "AAPL", "TSLA")
            
        Returns:
            Dictionary with ticker info including current price
        """
        try:
            result = await self.call_tool(
                "yfinance_get_ticker_info",
                {"symbol": ticker}
            )
            return result
        except Exception as e:
            logger.error(f"Failed to get ticker info for {ticker}: {e}")
            return {"error": str(e), "ticker": ticker}
    
    async def get_price_history(
        self,
        ticker: str,
        period: str = "1mo",
        interval: str = "1d"
    ) -> Dict[str, Any]:
        """
        Get historical price data for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
            
        Returns:
            Dictionary with historical price data
        """
        try:
            result = await self.call_tool(
                "yfinance_get_price_history",
                {
                    "symbol": ticker,
                    "period": period,
                    "interval": interval
                }
            )
            return result
        except Exception as e:
            logger.error(f"Failed to get price history for {ticker}: {e}")
            return {"error": str(e), "ticker": ticker}
    
    async def search_ticker(self, query: str) -> Dict[str, Any]:
        """
        Search for ticker symbols.
        
        Args:
            query: Search query (company name or ticker)
            
        Returns:
            Dictionary with search results
        """
        try:
            result = await self.call_tool(
                "yfinance_search",
                {"query": query, "search_type": "quotes"}
            )
            return result
        except Exception as e:
            logger.error(f"Failed to search for ticker '{query}': {e}")
            return {"error": str(e), "query": query}
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

