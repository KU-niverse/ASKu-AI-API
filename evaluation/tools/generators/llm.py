from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI


def get_OPENAI_llm(
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
    ) -> BaseChatModel:
    """Returns OpenAI chat models.

    Available OpenAI models: https://platform.openai.com/docs/models/gpt-3-5-turbo

    Args:
        model (str, optional): OpenAI Chat model name. Default to 'gpt-3.5-turbo'.
        temperature (float, optional): Chat model temperature. Default to '0.7'.

    Returns:
        BaseChatModel: OpenAI chat model.
    
    Example:
        ```python
        get_OPENAI_llm(model='gpt-3.5-turbo-0125', temperature=0.4)
        ```
    """
    llm = ChatOpenAI(
        model=model,
        temperature=temperature)
    
    return llm
