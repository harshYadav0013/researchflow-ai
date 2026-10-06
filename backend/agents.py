from tools import web_search, reader
from langchain.agents import create_agent
from langchain_ollama import ChatOllama


## agents

## search agent
model  = ChatOllama( model = "qwen3:8b")

search_agent = create_agent(
    model = model,
    tools = [web_search]

)


## Reader agent
reader_agent = create_agent(
    model=model,
    tools=[reader]
)













    


