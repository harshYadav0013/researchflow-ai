from langchain_tavily import TavilySearch
from tavily import TavilyClient
from langchain.tools import tool
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os



## Search tool

tavily = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
)


@tool
def web_search(query:str)->list:
    """ Tool for web Searching any topic given and return the title, urls, content """
    results = tavily.search(query, max_results=5)

    out = []

    for r in results["results"]:
        result = {
            "title": r["title"],
            "url": r["url"],
            "content": r["content"][:500]
        }

        out.append(result)

    return out



## Scrapper tool for fetching the content from the webpage 
@tool
def reader(url:str) -> str:
    """Scrape and return the clean text from a given url for deeper reading"""
    try:
        response = requests.get(url)

        response.raise_for_status()
        
        soup = BeautifulSoup(response.text,"html.parser")

        for tag in soup.find_all(["nav","footer","script","style"]):
            tag.decompose()

        text = soup.get_text()

        text = " ".join(text.split())
        return text[:5000]
    
    except Exception as e:
        return f"failed to fetch URL : {e}"


    





