"""LLM service using OpenAI."""
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings


class LLMService:
    """Service for LLM interactions."""

    def __init__(self) -> None:
        """Initialize LLM client."""
        self.llm = ChatOpenAI(
            temperature=0,
            model=settings.LLM_MODEL,
            api_key=settings.OPENAI_API_KEY,
        )

    async def generate(self, messages: list[BaseMessage]) -> str:
        """Generate response from messages."""
        response = await self.llm.ainvoke(messages)
        return str(response.content)

    def build_messages(
        self,
        system_prompt: str,
        history: list[tuple[str, str]],
        query: str,
    ) -> list[BaseMessage]:
        """Build message list for LLM."""
        messages: list[BaseMessage] = [SystemMessage(content=system_prompt)]

        for role, content in history:
            if role == "user":
                messages.append(HumanMessage(content=content))
            else:
                messages.append(AIMessage(content=content))

        messages.append(HumanMessage(content=query))
        return messages


llm_service = LLMService()
