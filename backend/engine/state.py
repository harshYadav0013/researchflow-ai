from typing import TypedDict

## state schema
class ResearchState(TypedDict):
    question:str
    search_result:list
    scrapped_content:list
    draft:str
    critic:str
    approved:bool
    final_version:str
    human_decision: dict