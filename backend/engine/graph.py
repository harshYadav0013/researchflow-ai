## workflow of the graph
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

from .state import ResearchState
from ..nodes import (
    search_node,
    reader_node,
    writer_node,
    critic_node,
    human_review_node,
    final_node,
    route_after_human
)

##checkpointer
checkpointer = InMemorySaver()




## state graph and adding the nodes and edges
## make graph -> add nodes -> add edges -> give start and end -> compile
graph = StateGraph(ResearchState)

graph.add_node("search",search_node)
graph.add_node("reader",reader_node)
graph.add_node("writer",writer_node)
graph.add_node("critic",critic_node)
graph.add_node("human_review", human_review_node)
graph.add_node("final",final_node)

## workflow
graph.add_edge(START,"search")
graph.add_edge("search","reader")
graph.add_edge("reader","writer")
graph.add_edge("writer","critic")
graph.add_edge("critic", "human_review")

graph.add_conditional_edges(
    "human_review",
    route_after_human,
    {
        "final": "final",
        "writer": "writer"
    }
)


graph.add_edge("final", END)
app = graph.compile(checkpointer=checkpointer)