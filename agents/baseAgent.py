import os
import json
import asyncio
from typing import List, Dict, Any, Optional, Callable, Union
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
from dotenv import load_dotenv
import google.generativeai as genai

# Import helper agents for tool usage
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util.perplexity import PerplexityAgent
from util.browseruse import BrowserUseAgent

load_dotenv()


class MessageRole(Enum):
    """Message roles in conversation"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


@dataclass
class Message:
    """Represents a message in the chat history"""
    role: MessageRole
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary format"""
        data = {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat()
        }
        if self.metadata:
            data["metadata"] = self.metadata
        if self.tool_calls:
            data["tool_calls"] = self.tool_calls
        if self.tool_call_id:
            data["tool_call_id"] = self.tool_call_id
        return data
    
    def to_gemini_format(self) -> Dict[str, Any]:
        """Convert message to Gemini API format"""
        if self.role == MessageRole.USER:
            return {"role": "user", "parts": [{"text": self.content}]}
        elif self.role == MessageRole.ASSISTANT:
            return {"role": "model", "parts": [{"text": self.content}]}
        elif self.role == MessageRole.SYSTEM:
            # Gemini doesn't have a system role, so we prepend it as a user message
            return {"role": "user", "parts": [{"text": f"System: {self.content}"}]}
        elif self.role == MessageRole.TOOL:
            # Handle tool responses
            return {"role": "user", "parts": [{"text": f"Tool Response: {self.content}"}]}
        else:
            return {"role": "user", "parts": [{"text": self.content}]}


class ToolType(Enum):
    """Available tool types"""
    PERPLEXITY_SEARCH = "perplexity_search"
    BROWSER_USE = "browser_use"


class BaseAgent:
    """
    Base agent class for multi-agent systems with Gemini integration.
    Features:
    - Chat history management
    - System prompt configuration
    - Tool calling (Perplexity and BrowserUse)
    - Inter-agent communication
    - Async support
    """
    
    def __init__(
        self,
        name: str,
        system_prompt: str = "",
        model_name: str = "gemini-2.5-flash",
        temperature: float = 0.7,
        max_output_tokens: int = 2048,
        enable_tools: bool = True,
        auto_execute_tools: bool = True,
        memory_limit: Optional[int] = None
    ):
        """
        Initialize the base agent.
        
        Args:
            name: Agent identifier name
            system_prompt: Initial system prompt for the agent
            model_name: Gemini model to use (gemini-2.5-pro, gemini-2.5-flash)
            temperature: Sampling temperature (0-1)
            max_output_tokens: Maximum tokens in response
            enable_tools: Whether to enable tool calling
            auto_execute_tools: Whether to automatically execute tool calls
            memory_limit: Maximum number of messages to keep in history (None for unlimited)
        """
        self.name = name
        self.system_prompt = system_prompt
        self.model_name = model_name
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.enable_tools = enable_tools
        self.auto_execute_tools = auto_execute_tools
        self.memory_limit = memory_limit
        
        # Initialize Gemini
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_output_tokens,
            }
        )
        
        # Initialize chat history
        self.chat_history: List[Message] = []
        if system_prompt:
            self._add_message(MessageRole.SYSTEM, system_prompt)
        
        # Initialize tool agents if enabled
        self.tools: Dict[str, Any] = {}
        if enable_tools:
            self._initialize_tools()
        
        # Agent communication
        self.connected_agents: Dict[str, 'BaseAgent'] = {}
        self.message_handlers: List[Callable] = []
        
    def _initialize_tools(self):
        """Initialize available tools"""
        try:
            self.tools['perplexity'] = PerplexityAgent()
        except Exception as e:
            print(f"Warning: Could not initialize Perplexity tool: {e}")
        
        try:
            self.tools['browseruse'] = BrowserUseAgent()
        except Exception as e:
            print(f"Warning: Could not initialize BrowserUse tool: {e}")
    
    def _add_message(
        self,
        role: MessageRole,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        tool_call_id: Optional[str] = None
    ):
        """Add a message to chat history"""
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.now(),
            metadata=metadata,
            tool_calls=tool_calls,
            tool_call_id=tool_call_id
        )
        self.chat_history.append(message)
        
        # Apply memory limit if set
        if self.memory_limit and len(self.chat_history) > self.memory_limit:
            # Keep system prompt if it exists
            system_messages = [m for m in self.chat_history if m.role == MessageRole.SYSTEM]
            other_messages = [m for m in self.chat_history if m.role != MessageRole.SYSTEM]
            
            # Keep only the most recent messages
            keep_count = self.memory_limit - len(system_messages)
            self.chat_history = system_messages + other_messages[-keep_count:]
    
    def _parse_tool_calls(self, response_text: str) -> List[Dict[str, Any]]:
        """
        Parse tool calls from response text.
        Looks for patterns like [TOOL: tool_name(params)]
        """
        tool_calls = []
        
        # Simple pattern matching for tool calls
        import re
        pattern = r'\[TOOL:\s*(\w+)\((.*?)\)\]'
        matches = re.finditer(pattern, response_text)
        
        for match in matches:
            tool_name = match.group(1)
            params_str = match.group(2)
            
            # Try to parse parameters as JSON or as a simple string
            try:
                params = json.loads(params_str) if params_str else {}
            except:
                params = {"query": params_str.strip('"').strip("'")}
            
            tool_calls.append({
                "tool": tool_name,
                "parameters": params
            })
        
        return tool_calls
    
    async def _execute_tool_async(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """Execute a tool call asynchronously"""
        if tool_name == "perplexity_search" and 'perplexity' in self.tools:
            query = parameters.get("query", "")
            result = await asyncio.to_thread(self.tools['perplexity'].search, query)
            return result
        
        elif tool_name == "browser_use" and 'browseruse' in self.tools:
            task = parameters.get("task", "")
            result = await asyncio.to_thread(self.tools['browseruse'].run_browseruse, task)
            return result
        
        else:
            return f"Tool '{tool_name}' not available"
    
    def _execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """Execute a tool call synchronously"""
        if tool_name == "perplexity_search" and 'perplexity' in self.tools:
            query = parameters.get("query", "")
            return self.tools['perplexity'].search(query)
        
        elif tool_name == "browser_use" and 'browseruse' in self.tools:
            task = parameters.get("task", "")
            return self.tools['browseruse'].run_browseruse(task)
        
        else:
            return f"Tool '{tool_name}' not available"
    
    def _prepare_conversation_for_gemini(self) -> List[Dict[str, Any]]:
        """Prepare conversation history for Gemini API"""
        gemini_messages = []
        
        for message in self.chat_history:
            gemini_msg = message.to_gemini_format()
            if gemini_msg:
                gemini_messages.append(gemini_msg)
        
        return gemini_messages
    
    def _get_tool_instructions(self) -> str:
        """Get instructions for tool usage"""
        if not self.enable_tools:
            return ""
        
        instructions = """
You have access to the following tools:

1. **perplexity_search**: Search the web for real-time information
   Usage: [TOOL: perplexity_search({"query": "your search query"})]
   
2. **browser_use**: Interact with web pages and perform browser automation
   Usage: [TOOL: browser_use({"task": "description of task to perform"})]

When you need to use a tool, include the tool call in your response using the exact format shown above.
"""
        return instructions
    
    def chat(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Send a message to the agent and get a response.
        
        Args:
            message: The message to send
            metadata: Optional metadata to attach to the message
            
        Returns:
            The agent's response
        """
        # Add user message to history
        self._add_message(MessageRole.USER, message, metadata)
        
        # Prepare prompt with tool instructions if enabled
        full_prompt = message
        if self.enable_tools and self.tools:
            tool_instructions = self._get_tool_instructions()
            full_prompt = f"{tool_instructions}\n\nUser: {message}"
        
        # Get conversation history for context
        conversation = self._prepare_conversation_for_gemini()
        
        try:
            # Generate response with Gemini
            response = self.model.generate_content(full_prompt)
            
            # Handle potential response issues
            try:
                response_text = response.text
            except Exception as text_error:
                # Fallback when response.text fails (e.g., safety filters, API issues)
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'finish_reason'):
                        if candidate.finish_reason == 2:  # SAFETY
                            response_text = "Response filtered for safety. Please rephrase your request."
                        elif candidate.finish_reason == 3:  # RECITATION
                            response_text = "Response blocked due to potential copyright concerns."
                        else:
                            response_text = f"Response unavailable (reason: {candidate.finish_reason})"
                    else:
                        response_text = "Response generation failed. Please try again."
                else:
                    response_text = f"API response error: {str(text_error)[:100]}"
            
            # Check for tool calls in the response
            if self.enable_tools and self.auto_execute_tools:
                tool_calls = self._parse_tool_calls(response_text)
                
                if tool_calls:
                    # Execute tool calls and get results
                    tool_results = []
                    for tool_call in tool_calls:
                        tool_name = tool_call["tool"]
                        parameters = tool_call["parameters"]
                        
                        # Execute the tool
                        result = self._execute_tool(tool_name, parameters)
                        tool_results.append({
                            "tool": tool_name,
                            "result": result
                        })
                        
                        # Add tool response to history
                        self._add_message(
                            MessageRole.TOOL,
                            f"Tool {tool_name} result: {result}",
                            metadata={"tool_call": tool_call}
                        )
                    
                    # Generate final response incorporating tool results
                    tool_context = "\n".join([
                        f"Tool {tr['tool']} returned: {tr['result']}"
                        for tr in tool_results
                    ])
                    
                    followup_prompt = f"""Based on the tool results:
{tool_context}

Please provide a comprehensive response to the user's query: {message}"""
                    
                    final_response = self.model.generate_content(followup_prompt)
                    try:
                        response_text = final_response.text
                    except Exception:
                        response_text = "Follow-up response unavailable. Tool results processed."
            
            # Add assistant response to history
            self._add_message(MessageRole.ASSISTANT, response_text, metadata)
            
            return response_text
            
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            self._add_message(MessageRole.ASSISTANT, error_msg, metadata={"error": True})
            return error_msg
    
    async def chat_async(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Async version of chat method.
        
        Args:
            message: The message to send
            metadata: Optional metadata to attach to the message
            
        Returns:
            The agent's response
        """
        # Add user message to history
        self._add_message(MessageRole.USER, message, metadata)
        
        # Prepare prompt with tool instructions if enabled
        full_prompt = message
        if self.enable_tools and self.tools:
            tool_instructions = self._get_tool_instructions()
            full_prompt = f"{tool_instructions}\n\nUser: {message}"
        
        # Get conversation history for context
        conversation = self._prepare_conversation_for_gemini()
        
        try:
            # Generate response with Gemini (async)
            response = await self.model.generate_content_async(full_prompt)
            
            # Handle potential response issues
            try:
                response_text = response.text
            except Exception as text_error:
                # Fallback when response.text fails (e.g., safety filters, API issues)
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'finish_reason'):
                        if candidate.finish_reason == 2:  # SAFETY
                            response_text = "Response filtered for safety. Please rephrase your request."
                        elif candidate.finish_reason == 3:  # RECITATION
                            response_text = "Response blocked due to potential copyright concerns."
                        else:
                            response_text = f"Response unavailable (reason: {candidate.finish_reason})"
                    else:
                        response_text = "Response generation failed. Please try again."
                else:
                    response_text = f"API response error: {str(text_error)[:100]}"
            
            # Check for tool calls in the response
            if self.enable_tools and self.auto_execute_tools:
                tool_calls = self._parse_tool_calls(response_text)
                
                if tool_calls:
                    # Execute tool calls asynchronously
                    tool_results = []
                    for tool_call in tool_calls:
                        tool_name = tool_call["tool"]
                        parameters = tool_call["parameters"]
                        
                        # Execute the tool asynchronously
                        result = await self._execute_tool_async(tool_name, parameters)
                        tool_results.append({
                            "tool": tool_name,
                            "result": result
                        })
                        
                        # Add tool response to history
                        self._add_message(
                            MessageRole.TOOL,
                            f"Tool {tool_name} result: {result}",
                            metadata={"tool_call": tool_call}
                        )
                    
                    # Generate final response incorporating tool results
                    tool_context = "\n".join([
                        f"Tool {tr['tool']} returned: {tr['result']}"
                        for tr in tool_results
                    ])
                    
                    followup_prompt = f"""Based on the tool results:
{tool_context}

Please provide a comprehensive response to the user's query: {message}"""
                    
                    final_response = await self.model.generate_content_async(followup_prompt)
                    try:
                        response_text = final_response.text
                    except Exception:
                        response_text = "Follow-up response unavailable. Tool results processed."
            
            # Add assistant response to history
            self._add_message(MessageRole.ASSISTANT, response_text, metadata)
            
            return response_text
            
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            self._add_message(MessageRole.ASSISTANT, error_msg, metadata={"error": True})
            return error_msg
    
    def connect_agent(self, agent: 'BaseAgent'):
        """
        Connect another agent for inter-agent communication.
        
        Args:
            agent: Another BaseAgent instance to connect
        """
        self.connected_agents[agent.name] = agent
    
    def disconnect_agent(self, agent_name: str):
        """
        Disconnect an agent.
        
        Args:
            agent_name: Name of the agent to disconnect
        """
        if agent_name in self.connected_agents:
            del self.connected_agents[agent_name]
    
    def send_to_agent(self, agent_name: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Send a message to a connected agent.
        
        Args:
            agent_name: Name of the target agent
            message: Message to send
            metadata: Optional metadata
            
        Returns:
            Response from the target agent, or None if agent not found
        """
        if agent_name not in self.connected_agents:
            return None
        
        target_agent = self.connected_agents[agent_name]
        
        # Add sender information to metadata
        if metadata is None:
            metadata = {}
        metadata["sender"] = self.name
        
        # Send message to target agent
        response = target_agent.receive_from_agent(message, metadata)
        
        # Log the inter-agent communication in our history
        self._add_message(
            MessageRole.ASSISTANT,
            f"Sent to {agent_name}: {message}",
            metadata={"inter_agent_send": True, "target": agent_name}
        )
        
        return response
    
    def receive_from_agent(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Receive and process a message from another agent.
        
        Args:
            message: Message from another agent
            metadata: Optional metadata including sender info
            
        Returns:
            Response to the sending agent
        """
        sender = metadata.get("sender", "Unknown") if metadata else "Unknown"
        
        # Process the message with context about it being from another agent
        agent_context_message = f"Message from agent '{sender}': {message}"
        
        # Generate response
        response = self.chat(agent_context_message, metadata)
        
        return response
    
    def broadcast_to_agents(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """
        Broadcast a message to all connected agents.
        
        Args:
            message: Message to broadcast
            metadata: Optional metadata
            
        Returns:
            Dictionary of responses from all agents
        """
        responses = {}
        
        for agent_name, agent in self.connected_agents.items():
            response = self.send_to_agent(agent_name, message, metadata)
            if response:
                responses[agent_name] = response
        
        return responses
    
    def add_message_handler(self, handler: Callable):
        """
        Add a custom message handler for processing incoming messages.
        
        Args:
            handler: Callable that takes (message, metadata) and returns processed message
        """
        self.message_handlers.append(handler)
    
    def clear_history(self, keep_system_prompt: bool = True):
        """
        Clear chat history.
        
        Args:
            keep_system_prompt: Whether to keep the system prompt in history
        """
        if keep_system_prompt and self.system_prompt:
            self.chat_history = [m for m in self.chat_history if m.role == MessageRole.SYSTEM]
        else:
            self.chat_history = []
    
    def get_history(self, format: str = "list") -> Union[List[Message], List[Dict[str, Any]], str]:
        """
        Get chat history in specified format.
        
        Args:
            format: Output format - "list" (Message objects), "dict" (dictionaries), or "text" (formatted string)
            
        Returns:
            Chat history in the specified format
        """
        if format == "list":
            return self.chat_history
        elif format == "dict":
            return [msg.to_dict() for msg in self.chat_history]
        elif format == "text":
            output = []
            for msg in self.chat_history:
                role = msg.role.value.upper()
                timestamp = msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                output.append(f"[{timestamp}] {role}: {msg.content}")
            return "\n".join(output)
        else:
            raise ValueError(f"Invalid format: {format}. Use 'list', 'dict', or 'text'")
    
    def save_history(self, filepath: str):
        """
        Save chat history to a JSON file.
        
        Args:
            filepath: Path to save the history
        """
        history_data = {
            "agent_name": self.name,
            "system_prompt": self.system_prompt,
            "model_name": self.model_name,
            "messages": [msg.to_dict() for msg in self.chat_history]
        }
        
        with open(filepath, 'w') as f:
            json.dump(history_data, f, indent=2)
    
    def load_history(self, filepath: str):
        """
        Load chat history from a JSON file.
        
        Args:
            filepath: Path to load the history from
        """
        with open(filepath, 'r') as f:
            history_data = json.load(f)
        
        # Clear current history
        self.chat_history = []
        
        # Reconstruct messages
        for msg_data in history_data.get("messages", []):
            role = MessageRole(msg_data["role"])
            content = msg_data["content"]
            timestamp = datetime.fromisoformat(msg_data["timestamp"])
            metadata = msg_data.get("metadata")
            tool_calls = msg_data.get("tool_calls")
            tool_call_id = msg_data.get("tool_call_id")
            
            message = Message(
                role=role,
                content=content,
                timestamp=timestamp,
                metadata=metadata,
                tool_calls=tool_calls,
                tool_call_id=tool_call_id
            )
            self.chat_history.append(message)
    
    def __repr__(self) -> str:
        return f"BaseAgent(name='{self.name}', model='{self.model_name}', history_length={len(self.chat_history)})"


# Example usage and testing
if __name__ == "__main__":
    # Example 1: Basic agent with system prompt
    print("Example 1: Basic Agent")
    agent = BaseAgent(
        name="Assistant",
        system_prompt="You are a helpful AI assistant that provides clear and concise answers.",
        temperature=0.7
    )
    
    response = agent.chat("What is the capital of France?")
    print(f"Response: {response}\n")
    
    # Example 2: Agent with tools
    print("Example 2: Agent with Tools")
    research_agent = BaseAgent(
        name="ResearchAgent",
        system_prompt="You are a research assistant that can search the web for information.",
        enable_tools=True,
        auto_execute_tools=True
    )
    
    # This would trigger tool usage if the agent decides it needs to search
    response = research_agent.chat("What are the latest developments in quantum computing?")
    print(f"Response: {response[:200]}...\n")
    
    # Example 3: Multi-agent communication
    print("Example 3: Multi-Agent Communication")
    
    # Create two agents
    agent1 = BaseAgent(
        name="Analyst",
        system_prompt="You are a data analyst who provides insights."
    )
    
    agent2 = BaseAgent(
        name="Critic",
        system_prompt="You are a critical thinker who evaluates ideas."
    )
    
    # Connect agents
    agent1.connect_agent(agent2)
    agent2.connect_agent(agent1)
    
    # Agent1 sends message to Agent2
    agent1_message = "I think we should increase marketing budget by 20%"
    response = agent1.send_to_agent("Critic", agent1_message)
    print(f"Agent1 → Agent2: {agent1_message}")
    print(f"Agent2 Response: {response[:200]}...\n")
    
    # Example 4: History management
    print("Example 4: History Management")
    print(f"History length: {len(agent1.chat_history)} messages")
    print(f"History preview:\n{agent1.get_history('text')[:300]}...\n")
    
    # Save history
    agent1.save_history("agent1_history.json")
    print("History saved to agent1_history.json")
