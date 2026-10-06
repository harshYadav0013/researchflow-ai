from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from .tools import web_search,reader
from langgraph.types import interrupt
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()





## model and parser

if os.getenv("MODEL_PROVIDER", "ollama").lower() == "gemini":
    model = ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-3-flash-preview"),
        google_api_key=os.getenv("GEMINI_API_KEY"),
    )
else:
    model = ChatOllama(
        model=os.getenv("OLLAMA_MODEL", "phi4-mini:3.8b")
    )
parser = StrOutputParser()


## search node
## state -> question -> search tool called, searches and return result -> update the  state with search result
def search_node(state):

    question = state["question"]

    result = web_search.invoke({
        "query":question
    })

    return ({
        "search_result":result
    })


## reader node 
## state-> result -> reader tool  return scrapped content -> update the state with content
def reader_node(state):

    search_result = state["search_result"]

    scrapped_content=[]

    for result in search_result:

        text = reader.invoke({
            "url":result["url"]
        })

        scrapped_content.append(text)

    return ({
        "scrapped_content": scrapped_content
    })



##writer chain and node 
## state -> questino and content -> writer_chain -> draft created by the model -> update state 

prompt = ChatPromptTemplate([
    ("system","you are a experienced reserach writer. write a clear and factaul research paper based only provided material"),
    (
    "human",
    """Research Question:
{question}

Research Material:
{scrapped_content}

Previous Draft:
{draft}

Critic Feedback:
{critic}

Write a well-structured research report answering the question.

If this is the first draft, there may be no previous draft or critic feedback.
If this is a revision, improve the draft according to the critic feedback."""
)
])

## writer chain
writer_chain = prompt | model | parser


## writer node
def writer_node(state):

    draft = writer_chain.invoke({
        "question": state["question"],
        "scrapped_content": state["scrapped_content"],
        "draft": state.get("draft", ""),
        "critic": state.get("critic", "")
    })

    return {
        "draft": draft
    }


## critique  chain and node
## state -> draft -> question,content,draft -> critique chain -> model -> parser
##  prompt
critic_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a critical research editor.

Review the draft against the provided research material.

If the draft is good enough, start your response with:
APPROVED

If the draft needs improvement, start your response with:
REVISE

After that, briefly explain your decision and what needs to be improved."""
    ),
    (
        "human",
        """Research Question:
{question}

Research Material:
{scrapped_content}

Draft:
{draft}

Evaluate the draft."""
    )
])
## chain
critic_chain = critic_prompt | model | parser


## critic node
def critic_node(state):

    result = critic_chain.invoke({
        "question": state["question"],
        "scrapped_content": state["scrapped_content"],
        "draft": state["draft"]
    })

    approved = result.strip().startswith("APPROVED")

    return {
        "critic": result,
        "approved": approved
    }


## humna in loop node

def human_review_node(state):

    decision = interrupt({
        "draft":state["draft"],
        "critic":state["critic"]
    })

    return {
        "human_decision":decision
    }

## final node

def final_node(state):

    return {
        "final_version":state["draft"]
    }


## routing after human feedback
def route_after_human(state):

    if state["human_decision"]["approved"]:
        return "final"
    else:
        return "writer"






