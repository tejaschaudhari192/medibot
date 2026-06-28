import os
from dotenv import load_dotenv
from langchain_cohere import ChatCohere
from langchain_community.tools.tavily_search import TavilySearchResults

# Load environment variables
load_dotenv('config.env')
assert os.getenv('COHERE_API_KEY') is not None, "COHERE_API_KEY is not set in config.env"
assert os.getenv('TAVILY_API_KEY') is not None, "TAVILY_API_KEY is not set in config.env"

# Initialize Cohere LLM and Tavily Search Tool
llm = ChatCohere(model="command-r-plus-08-2024", temperature=0)
search_tool = TavilySearchResults(max_results=3)
