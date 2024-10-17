### This page describs some of the key objects and the respective usage for buidling an agentic applications.

Key points to be noted here are, how do these work in production specific deployement.

Do they support Multi Threading ?
Can they scale to handling different user using the platform simulatneously ?

User Session Management ?

AI Chat History Management ?

How to resume a Chat Thread from a different instance of the same application ?

**LLM** Object which allows for interacting with any LLM Module, these can be of type **ChatOpenAI** for interacting with Open AI <List Other Object Types with more examples>.

- This will be used to define Model configuration - temprature, model, API Key.

```
llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    # api_key="...",  # if you prefer to pass api key in directly instaed of using env vars
    # base_url="...",
    # organization="...",
    # other params...
)
```
Invocation
```
messages = [
    (
        "system",
        "You are a helpful assistant that translates English to French. Translate the user sentence.",
    ),
    ("human", "I love programming."),
]
ai_msg = llm.invoke(messages)
```

**Key Points**
- LLM object can be chained with tools to allows for tool invocation as determined by LLM with specific argumanets.
- LLM can be chained with Prompt.

Refer to the [langchain doc](https://python.langchain.com/api_reference/openai/chat_models/langchain_openai.chat_models.base.ChatOpenAI.html) for full details.

