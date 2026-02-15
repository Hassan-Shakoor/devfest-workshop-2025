from typing import Any

from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from settings import DEFAULT_MODEL_ID, DEFAULT_TEMPERATURE, GOOGLE_API_KEY
from src.agents.prompts import get_system_prompt
from src.models import ConversationContext, ProcessMessageResponse
from src.tools import (
    get_order_status,
    make_reservation,
    notify_staff,
    place_order,
    search_menu,
)
from src.utils import get_logger
from src.utils.context import get_request_metadata

logger = get_logger(__name__)


def get_restaurant_tools() -> list[Any]:
    """Get all available tools for the restaurant agent."""
    return [
        search_menu,
        place_order,
        get_order_status,
        make_reservation,
        notify_staff,
    ]


class RestaurantAgent:
    """
    Main agent for handling restaurant customer interactions.

    Responsibilities:
    - Answer questions about menu items
    - Process food orders
    - Check order status
    - Make table reservations
    - Escalate to staff when needed
    """

    def __init__(
        self,
        model_id: str | None = None,
        temperature: float = DEFAULT_TEMPERATURE
    ) -> None:
        """
        Initialize the restaurant agent.

        Args:
            model_id: LLM model identifier
            temperature: Temperature for response generation (0.0-1.0)

        Raises:
            ValueError: If temperature is out of range
        """
        if not (0.0 <= temperature <= 1.0):
            raise ValueError(f"Temperature must be between 0.0 and 1.0, got {temperature}")

        self.model_id = model_id or DEFAULT_MODEL_ID
        self.temperature = temperature
        self.system_prompt = get_system_prompt()
        self.tools = get_restaurant_tools()

        # Initialize model
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY not set in environment")

        self.model = ChatGoogleGenerativeAI(
            model=self.model_id,
            temperature=self.temperature,
            google_api_key=GOOGLE_API_KEY
        )

        # Create agent using modern LangChain API
        self.agent = create_agent(
            model=self.model,
            tools=self.tools,
            system_prompt=self.system_prompt
        )

        logger.info(f"RestaurantAgent initialized with model: {self.model_id}")

    async def process_message(
        self,
        message: str,
        context: ConversationContext | None = None,
        message_history: list = None
    ) -> ProcessMessageResponse:
        """
        Process a customer message and return a response.

        Args:
            message: The customer's message
            context: Conversation context with session info
            message_history: Previous conversation messages

        Returns:
            ProcessMessageResponse with agent's response and updated context
        """
        try:
            # Validate input
            if not message or not message.strip():
                return ProcessMessageResponse(
                    success=False,
                    error="Message cannot be empty"
                )

            messages_to_send = []

            # Add conversation history as context if available
            if message_history and len(message_history) > 0:
                history_text = "CONVERSATION HISTORY:\n"
                for msg in message_history:
                    # Handle both dict and Pydantic model
                    if hasattr(msg, 'model_dump'):
                        msg_dict = msg.model_dump()
                    elif isinstance(msg, dict):
                        msg_dict = msg
                    else:
                        continue

                    role = msg_dict.get("role", "user")
                    content = msg_dict.get("content", "")
                    history_text += f"{role.upper()}: {content}\n"

                messages_to_send.append(HumanMessage(content=history_text))
                logger.info(f"Including {len(message_history)} previous messages as context")

            # Add current message
            messages_to_send.append(HumanMessage(content=message))

            logger.info(f"Processing message: {message[:100]}...")

            # Run agent with modern API
            try:
                result = await self.agent.ainvoke({
                    "messages": messages_to_send
                })

                # Extract output from messages
                messages = result.get("messages", [])
                output = ""
                if messages:
                    last_message = messages[-1]
                    if hasattr(last_message, "content"):
                        output = last_message.content
                    else:
                        output = str(last_message)

                # Extract tool calls from agent execution
                tool_calls = self._extract_tool_calls(messages)
                logger.info(f"Extracted {len(tool_calls)} tool calls from agent execution")

            except Exception as e:
                logger.error(f"Agent execution error: {e}")
                output = "I apologize, but I encountered an error processing your request. Please try again."
                tool_calls = []

            # Get metadata (tool calls, etc.)
            try:
                metadata = get_request_metadata()
            except RuntimeError:
                metadata = {}

            # Add extracted tool calls to metadata
            if tool_calls:
                metadata["tool_calls"] = tool_calls

            # Update context
            if context:
                context.message_count += 1

            return ProcessMessageResponse(
                success=True,
                response=output,
                context=context,
                metadata=metadata
            )

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return ProcessMessageResponse(
                success=False,
                error=f"Failed to process message: {str(e)}"
            )

    def _extract_tool_calls(self, messages: list[Any]) -> list[dict]:
        """
        Extract tool calls from LangChain message history.

        Args:
            messages: List of LangChain messages from agent execution

        Returns:
            List of dicts with format: [{"name": str, "arguments": dict, "result": str}]
        """
        tool_calls = []
        tool_results = {}

        # First pass: collect tool results by tool_call_id
        for msg in messages:
            if hasattr(msg, "__class__") and msg.__class__.__name__ == "ToolMessage":
                tool_call_id = getattr(msg, "tool_call_id", None)
                if tool_call_id:
                    tool_results[tool_call_id] = getattr(msg, "content", "")

        # Second pass: collect tool calls from AIMessage
        for msg in messages:
            if hasattr(msg, "__class__") and msg.__class__.__name__ == "AIMessage":
                msg_tool_calls = getattr(msg, "tool_calls", [])
                for tool_call in msg_tool_calls:
                    if isinstance(tool_call, dict):
                        tool_name = tool_call.get("name", "unknown")
                        tool_args = tool_call.get("args", {})
                        tool_id = tool_call.get("id", "")
                        tool_result = tool_results.get(tool_id)

                        tool_calls.append({
                            "name": tool_name,
                            "arguments": tool_args,
                            "result": tool_result,
                        })

        return tool_calls

    def _extract_text_from_response(self, content: Any) -> str:
        """
        Extract text from various response formats.

        Args:
            content: Response content from the model

        Returns:
            Extracted text as string
        """
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            text_parts = []
            for block in content:
                if isinstance(block, dict) and "text" in block:
                    text_parts.append(block["text"])
                elif isinstance(block, str):
                    text_parts.append(block)
            return " ".join(text_parts)

        return str(content) if content else ""