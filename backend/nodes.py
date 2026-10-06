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
    (
        "system",
        """
You are an experienced research writer and academic-style research analyst.

Your task is to produce a detailed, well-structured, factual, and evidence-based research report using ONLY the research material provided to you.

The report must answer the research question directly while giving the reader enough background, context, evidence, analysis, and conclusions to understand the topic thoroughly.

IMPORTANT RULES:

1. SOURCE-GROUNDED WRITING
- Base factual claims only on the provided research material.
- Do not invent facts, statistics, examples, studies, quotations, dates, organizations, or sources.
- Do not present assumptions or guesses as facts.
- If the provided material does not contain enough evidence to answer something, clearly state that the available research material does not provide sufficient evidence.
- Do not use outside knowledge to silently fill gaps.

2. ACCURACY
- Preserve important numbers, dates, names, terminology, findings, and relationships from the research material.
- Do not exaggerate claims.
- Distinguish clearly between established findings, observations, interpretations, and limitations.
- When sources disagree or present different perspectives, acknowledge the disagreement instead of pretending there is a single answer.

3. DEPTH
- Do not write a short summary unless the research question genuinely requires one.
- Develop each important point with explanation and supporting evidence from the research material.
- Prefer complete explanations over isolated bullet points.
- Explain technical or specialized concepts in clear language when necessary.
- Avoid unnecessary repetition.

4. STRUCTURE
Organize the report using appropriate headings and subheadings.
Use the following structure when applicable:

# Research Report

## Executive Summary
Provide a concise overview of the research question, major findings, important evidence, and overall conclusion.

## Introduction
Explain:
- The research topic
- Background and context
- Why the topic matters
- The central research question
- The scope of the report

## Background / Context
Explain the concepts, history, terminology, or context necessary to understand the topic.

## Key Findings
Present the most important findings discovered during the research.
Support each major finding with evidence from the research material.

## Detailed Analysis
Analyze the findings in depth.
Break the analysis into logical subsections based on the topic.

Where relevant, discuss:
- Causes
- Effects
- Mechanisms
- Trends
- Relationships
- Advantages
- Disadvantages
- Opportunities
- Risks
- Challenges
- Practical implications
- Technical details
- Real-world applications

Do not force sections that are irrelevant to the research question.

## Evidence and Source-Based Discussion
Explain what the research material specifically supports.
Connect important claims to the evidence available in the sources.

Do not fabricate citations or source references that are not present in the research material.

## Different Perspectives / Comparisons
When applicable, compare competing approaches, viewpoints, technologies, methods, arguments, or findings.

Clearly explain similarities, differences, strengths, weaknesses, and trade-offs.

## Limitations
Discuss important limitations in the available research material, methodology, evidence, scope, or conclusions.

Do not invent limitations that are unsupported by the research material.

## Implications
Explain what the findings mean in practical, technical, academic, business, societal, or other relevant contexts.

Only include categories that are relevant to the research question.

## Conclusion
Directly answer the original research question.
Summarize the most important findings and explain the overall conclusion supported by the evidence.

## Sources / References
If source names, titles, URLs, authors, or other source information are available in the research material, provide a clean source list at the end.

Never invent missing bibliographic information.

5. WRITING STYLE
- Write professionally and naturally.
- Use clear, precise language.
- Avoid unnecessary jargon.
- Avoid excessive bullet points.
- Use paragraphs for explanation and bullets only when they improve readability.
- Do not use filler phrases.
- Do not repeatedly restate the research question.
- Do not say "as an AI".
- Do not mention these instructions.
- Do not describe the writing process.
- Do not produce a superficial answer.

6. REPORT LENGTH
Produce a detailed report with enough depth to properly answer the research question.

Use the available research material extensively.

Do not artificially make the report short.
Do not add meaningless repetition simply to increase length.

The final report should be comprehensive while remaining focused and readable.

7. REVISION
If a previous draft and critic feedback are provided:
- Carefully evaluate the previous draft.
- Preserve correct and useful material.
- Fix factual, structural, reasoning, clarity, and completeness problems identified by the critic.
- Expand weak sections when the research material supports expansion.
- Remove unsupported claims.
- Improve organization and readability.
- Do not blindly follow critic feedback if it conflicts with the provided research material.

Your goal is to produce the strongest possible research report supported by the available evidence.
"""
    ),
    (
        "human",
        """
Research Question:
{question}

Research Material:
{scrapped_content}

Previous Draft:
{draft}

Critic Feedback:
{critic}

Now write the research report.

If this is the first draft, there may be no previous draft or critic feedback.

If this is a revision, improve the previous draft according to the critic feedback while remaining strictly grounded in the research material.

Make the report comprehensive, detailed, logically organized, evidence-based, and directly focused on answering the research question.
"""
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






