from typing import Optional

from langchain_core.prompts.chat import ChatPromptTemplate
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate
from langfuse import Langfuse


def load_prompt(
        prompt_name: str,
        prompt_version: Optional[int] = None,
    ) -> ChatPromptTemplate:
    """Loads a LangFuse prompt and returns it as ChatPromptTemplate type.

    Args:
        prompt_name (str): The prompt name on LangFuse dashboard.
        prompt_version (int, optional): The version of prompt.

    Returns:
        ChatPromptTemplate: ChatPromptTemplate constructed using LangFuse prompt.

    Example:
        ```python
        load_prompt(prompt_name="RAG", prompt_version=1)
        ```
    """

    langfuse = Langfuse(); langfuse.auth_check()
    prompt = langfuse.get_prompt(name=prompt_name, version=prompt_version).prompt

    # Text Prompt
    if type(prompt) == str:
        messages = [SystemMessagePromptTemplate.from_template(template=prompt)]

    # Chat Prompt
    if type(prompt) == list:
        messages = []
        for message in prompt:
            messages.append((message["role"], message["content"]))

    return ChatPromptTemplate.from_messages(messages)
