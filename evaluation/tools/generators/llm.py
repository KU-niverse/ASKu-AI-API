from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI


def get_OPENAI_llm(
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
    ) -> BaseChatModel:
    """Returns OpenAI chat models.
    Available OpenAI models: https://platform.openai.com/docs/models/gpt-3-5-turbo
    """
    llm = ChatOpenAI(
        model=model,
        temperature=temperature)
    
    return llm
