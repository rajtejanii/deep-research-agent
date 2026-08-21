import os
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_ollama import ChatOllama

# 1. We check if an environment variable exists, otherwise default to localhost
# Docker will inject 'http://host.docker.internal:11434' here so it can reach your host machine.
ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

search_tool = DuckDuckGoSearchRun()

# 2. We pass the base_url into the LLM configuration
llm = ChatOllama(
    model="llama3.2", 
    temperature=0,
    base_url=ollama_url
)