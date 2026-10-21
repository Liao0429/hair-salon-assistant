import os

from langchain_openai import ChatOpenAI


def create_llm(model: str | None = None, temperature: float = 0.3, **kwargs) -> ChatOpenAI:
    """Build an OpenAI-compatible chat model from environment config.

    Config (via .env):
        MODEL_NAME          - model id (default 'gpt-4o-mini')
        OPENAI_API_KEY      - API key
        OPENAI_BASE_URL     - /v1 endpoint (default https://api.openai.com/v1)
    """
    return ChatOpenAI(
        model=model or os.getenv("MODEL_NAME", "gpt-4o-mini"),
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        temperature=temperature,
        streaming=False,
        **kwargs,
    )