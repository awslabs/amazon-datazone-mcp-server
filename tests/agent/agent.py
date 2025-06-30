"""Main LangGraph agent implementation for SMUS Admin Agent."""

import asyncio
import os
import sys
from contextlib import AsyncExitStack
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List
import re


from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from langchain_core.tools import BaseTool
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field

from .config import config

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    ClientSession = None
    StdioServerParameters = None
    stdio_client = None

import pandas as pd
import re
from tqdm.asyncio import tqdm

DATASET_PATH = "tests/agent/smus_test.csv"
df = pd.read_csv(DATASET_PATH)


class MCPTool(BaseTool):
    """A LangChain tool that wraps an MCP tool."""
    
    mcp_tool_name: str = Field(description="The name of the MCP tool")
    agent: Any = Field(description="Reference to the agent")
    
    def _run(self, **kwargs) -> str:
        """Synchronous run - not implemented for async tools."""
        raise NotImplementedError("This tool only supports async execution")
    
    async def _arun(self, **kwargs) -> str:
        """Execute the MCP tool asynchronously."""
        try:
            result = await self.agent.call_mcp_tool(self.mcp_tool_name, kwargs)
            # Convert result to string if it's not already
            if isinstance(result, list):
                # Handle list of content items
                content_parts = []
                for item in result:
                    if hasattr(item, 'text'):
                        content_parts.append(item.text)
                    elif isinstance(item, dict) and 'text' in item:
                        content_parts.append(item['text'])
                    else:
                        content_parts.append(str(item))
                return "\n".join(content_parts)
            elif hasattr(result, 'text'):
                return result.text
            elif isinstance(result, dict) and 'text' in result:
                return result['text']
            return str(result)
        except Exception as e:
            return f"Error calling {self.mcp_tool_name}: {str(e)}"


class ConversationState(BaseModel):
    """State for the conversation graph."""
    messages: List[BaseMessage] = field(default_factory=list)
    user_input: str = ""
    response: str = ""
    
    class Config:
        arbitrary_types_allowed = True


@dataclass
class ChatSession:
    """Represents a chat session with conversation history."""
    session_id: str
    messages: List[BaseMessage] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def add_message(self, message: BaseMessage):
        """Add a message to the session history."""
        self.messages.append(message)
        self.updated_at = datetime.now()
    
    def get_recent_messages(self, limit: int = 10) -> List[BaseMessage]:
        """Get recent messages from the session."""
        return self.messages[-limit:] if self.messages else []


class SMUSAdminAgent:
    """LangGraph-based AI agent for SMUS admin queries."""
    
    def __init__(self):
        self.config = config  # Store config as instance variable
        
        # Validate API key before initializing LLM
        config.validate_api_key()
        
        self.llm = ChatAnthropic(
            model=config.default_model,
            api_key=config.anthropic_api_key,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            streaming=True
        )
        self.graph = self._build_graph()
        self.sessions: Dict[str, ChatSession] = {}
        self.mcp_client = None
        self.exit_stack = None
        self.mcp_tools = []  # Store converted MCP tools
        if config.is_mcp_configured and ClientSession:
            self._initialize_mcp_client()
    
    def _initialize_mcp_client(self):
        """Initialize the MCP client."""
        try:
            # The mcp_server_path should point to the project root directory
            server_path = config.mcp_server_path
            if not os.path.exists(server_path):
                raise ValueError(f"MCP server path does not exist: {server_path}")
            
            print(f"🔍 Debug: Initializing MCP client with server path: {server_path}")
            
            # Check if there's a virtual environment in the server directory
            server_venv_python = os.path.join(server_path, ".venv", "bin", "python")
            if os.path.exists(server_venv_python):
                python_cmd = server_venv_python
                print(f"🔍 Debug: Using server's virtual environment: {python_cmd}")
            else:
                # Use system python and hope the package is installed globally
                python_cmd = "python"
                print(f"🔍 Debug: Using system python: {python_cmd}")
            
            # Create server parameters for stdio connection
            # Run the datazone server directly
            server_params = StdioServerParameters(
                command=python_cmd,
                args=["servers/datazone/server.py"],
                env={
                    "PYTHONPATH": "servers",
                    "AWS_ACCESS_KEY_ID": "ASIAQGYBP5OXW5MTKVKQ_test",
                    "AWS_SECRET_ACCESS_KEY": "test_secret_key",
                    "AWS_SESSION_TOKEN": "test_session_token",
                    "AWS_DEFAULT_REGION": "us-east-1"
                },
                cwd=server_path
            )
            
            print(f"🔍 Debug: Server params - command: {server_params.command}, args: {server_params.args}, cwd: {server_params.cwd}")
            
            # This is an async operation, but we are in a sync constructor.
            # For now, we'll set up the parameters and initialize later
            self.server_params = server_params
            print("✅ MCP client parameters set up successfully!")
        except Exception as e:
            print(f"Failed to set up MCP client: {e}")
            import traceback
            traceback.print_exc()
            self.mcp_client = None
    
    async def _ensure_mcp_client(self):
        """Ensure MCP client is connected (lazy initialization)."""
        if self.mcp_client is None and hasattr(self, 'server_params'):
            try:
                self.exit_stack = AsyncExitStack()
                stdio_transport = await self.exit_stack.enter_async_context(
                    stdio_client(self.server_params)
                )
                self.stdio, self.write = stdio_transport
                self.mcp_client = await self.exit_stack.enter_async_context(
                    ClientSession(self.stdio, self.write)
                )
                await self.mcp_client.initialize()
                print("✅ MCP client connected and initialized!")
                
                # Convert MCP tools to LangChain tools
                await self._setup_mcp_tools()
                return True
            except Exception as e:
                print(f"Failed to connect MCP client: {e}")
                import traceback
                traceback.print_exc()
                return False
        return self.mcp_client is not None

    async def list_mcp_tools(self) -> List[str]:
        """List available MCP tools."""
        if not await self._ensure_mcp_client():
            return []
        
        try:
            tools = await self.mcp_client.list_tools()
            return [tool.name for tool in tools.tools]
        except Exception as e:
            print(f"Failed to list MCP tools: {e}")
            return []

    async def call_mcp_tool(self, tool_name: str, arguments: dict):
        """Call an MCP tool with the given arguments."""
        if not await self._ensure_mcp_client():
            raise Exception("MCP client not available")
        
        try:
            result = await self.mcp_client.call_tool(tool_name, arguments)
            return result
        except Exception as e:
            raise Exception(f"Error calling MCP tool {tool_name}: {e}")

    async def _setup_mcp_tools(self):
        """Convert MCP tools to LangChain tools."""
        if not self.mcp_client:
            return
        
        try:
            # Get MCP tools
            tools_response = await self.mcp_client.list_tools()
            self.mcp_tools = []
            
            for mcp_tool in tools_response.tools:
                # Create a LangChain tool wrapper
                langchain_tool = MCPTool(
                    name=mcp_tool.name,
                    description=mcp_tool.description or f"MCP tool: {mcp_tool.name}",
                    mcp_tool_name=mcp_tool.name,
                    agent=self
                )
                self.mcp_tools.append(langchain_tool)
            
            # Bind tools to the LLM
            if self.mcp_tools:
                self.llm_with_tools = self.llm.bind_tools(self.mcp_tools)
                print(f"✅ Bound {len(self.mcp_tools)} MCP tools to LLM")
            else:
                self.llm_with_tools = self.llm
                
        except Exception as e:
            print(f"Failed to setup MCP tools: {e}")
            self.llm_with_tools = self.llm
    
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph conversation graph."""
        
        def chat_node(state: ConversationState) -> ConversationState:
            """Main chat node that processes user input and generates responses."""
            try:
                # Prepare messages for the LLM
                messages = state.messages.copy()
                if state.user_input:
                    messages.append(HumanMessage(content=state.user_input))
                
                # Generate response using the LLM
                response = self.llm.invoke(messages)
                
                # Update state
                state.messages = messages + [response]
                state.response = response.content
                
                return state
            
            except Exception as e:
                error_msg = f"Error processing request: {str(e)}"
                state.response = error_msg
                state.messages.append(AIMessage(content=error_msg))
                return state
        
        # Build the graph
        workflow = StateGraph(ConversationState)
        
        # Add nodes
        workflow.add_node("chat", chat_node)
        
        # Add edges
        workflow.add_edge(START, "chat")
        workflow.add_edge("chat", END)
        
        return workflow.compile()
    
    def get_or_create_session(self, session_id: str) -> ChatSession:
        """Get an existing session or create a new one."""
        if session_id not in self.sessions:
            self.sessions[session_id] = ChatSession(session_id=session_id)
        return self.sessions[session_id]
    
    async def test_response(
        self, 
        session_id: str = "default",
        output_path: str = None
    ) -> str:
        try:
            session = self.get_or_create_session(session_id)
            
            # Try to connect to MCP server and get actual tools
            print("🔄 Attempting to connect to MCP server...")
            mcp_connected = await self._ensure_mcp_client()
            
            available_tools = []
            if mcp_connected:
                print("✅ MCP client connected successfully!")
                available_tools = await self.list_mcp_tools()
                print(f"📋 Found {len(available_tools)} MCP tools: {', '.join(available_tools[:5])}...")
            else:
                print("❌ MCP connection failed, using fallback tool list")
            
            # Create system message with actual available tools
            tools_list = ", ".join(available_tools)
            system_message = SystemMessage(content=(
                """

                You are an IT admin tool selector. Your task is to analyze the user input and output exactly one word: the name of the tool to call.
                Regardless of the user question or the required parameters, only output which tool best matches the user's request. 

                RULES:

                Output ONLY the tool name (e.g., "get_asset")

                If no tool matches, output EXACTLY: "None"

                NEVER add any other text, explanation, or formatting

                NEVER ask for parameters or additional information

                NEVER respond with complete sentences

                NEVER respond the user question or request

                BAD EXAMPLES (NEVER DO THIS):
                "GetConnection - to retrieve connection information..."
                "To search for a specific asset..."
                "Please provide parameters for..."

                GOOD EXAMPLES (ONLY DO THIS):
                "get_connection"
                "search"
                "None"

                Now analyze this input and output ONLY the tool name

                REMEMBER: If you output ANYTHING other than the tool name or "none", the system will crash.

                """
            ))
            session.add_message(system_message)

            for index in tqdm(range(len(df))):
                row = df.iloc[index]
                user_input = row["question"]
                llm_to_use = getattr(self, 'llm_with_tools', self.llm)
                response_content = ""

                # Use only SystemMessage + current question (independent processing)
                current_messages = [system_message, HumanMessage(content=user_input)]
                async for chunk in llm_to_use.astream(current_messages):
                    content = getattr(chunk, 'content', '')
                    if isinstance(content, list):
                        response_content += "".join([part['text'] for part in content if 'text' in part])
                    else:
                        response_content += str(content)

                if response_content:
                    session.add_message(AIMessage(content=response_content))
                    df.at[index, "api_called"] = ''.join(word.capitalize() for word in response_content.strip().split('_'))
            
        except Exception as e:
            print(f"Error: {str(e)}")

        if output_path is None:
            output_path = "/Users/jiayixin/Desktop/results.csv"
        df.to_csv(output_path, index=False)
        print(f"✅ Results saved to: {output_path}")

    async def cleanup_mcp(self):
        """Clean up MCP resources."""
        try:
            if self.exit_stack:
                # Set client to None first to prevent further use
                self.mcp_client = None
                # Then close the exit stack
                await self.exit_stack.aclose()
                self.exit_stack = None
        except Exception as e:
            # Suppress cleanup errors to avoid confusing users
            # These are usually harmless asyncio context manager issues
            pass 