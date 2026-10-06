from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langgraph.types import Command

from ..engine.graph import app
from ..history.database import (
    create_research,
    update_research,
    get_all_research,
    get_research,
)


router = APIRouter(
    prefix="/api/research",
    tags=["research"]
)


class ResearchRequest(BaseModel):
    question: str


class ResumeRequest(BaseModel):
    thread_id: str
    approved: bool


def get_interrupt_data(result):

    interrupts = result.get("__interrupt__", [])

    if not interrupts:
        return None

    return interrupts[0].value


@router.post("/start")
def start_research(request: ResearchRequest):

    thread_id = str(uuid4())

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    result = app.invoke(
        {
            "question": request.question
        },
        config=config
    )

    interrupt_data = get_interrupt_data(result)

    if interrupt_data:

        create_research(
            thread_id=thread_id,
            question=request.question,
            draft=interrupt_data["draft"],
            critic=interrupt_data["critic"],
            sources=result.get("search_result", [])
        )

        return {
            "thread_id": thread_id,
            "interrupted": True,
            "draft": interrupt_data["draft"],
            "critic": interrupt_data["critic"],
            "sources": result.get("search_result", [])
        }

    return {
        "thread_id": thread_id,
        "interrupted": False,
        "final_version": result.get("final_version", ""),
        "sources": result.get("search_result", [])
    }


@router.post("/resume")
def resume_research(request: ResumeRequest):

    config = {
        "configurable": {
            "thread_id": request.thread_id
        }
    }

    result = app.invoke(
        Command(
            resume={
                "approved": request.approved
            }
        ),
        config=config
    )

    interrupt_data = get_interrupt_data(result)

    # Graph paused again for another human review
    if interrupt_data:

        update_research(
            thread_id=request.thread_id,
            status="in_review",
            draft=interrupt_data["draft"],
            critic=interrupt_data["critic"],
            sources=result.get("search_result", [])
        )

        return {
            "thread_id": request.thread_id,
            "interrupted": True,
            "draft": interrupt_data["draft"],
            "critic": interrupt_data["critic"],
            "sources": result.get("search_result", [])
        }

    # Graph reached the final state
    final_version = result.get("final_version", "")

    update_research(
        thread_id=request.thread_id,
        status="completed",
        draft=result.get("draft", ""),
        critic=result.get("critic", ""),
        final_version=final_version,
        sources=result.get("search_result", [])
    )

    return {
        "thread_id": request.thread_id,
        "interrupted": False,
        "final_version": final_version,
        "sources": result.get("search_result", [])
    }

@router.get("/history")
def research_history():
    return {
        "research": get_all_research()
    }



@router.get("/history/{thread_id}")
def research_detail(thread_id: str):
    research = get_research(thread_id)

    if research is None:
        raise HTTPException(
            status_code=404,
            detail="Research not found"
        )

    return research