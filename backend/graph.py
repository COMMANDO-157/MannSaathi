from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional
from backend.agents import interaction_agent, analysis_agent, knowledge_agent, response_agent

class PipelineState(TypedDict):
    user_id: str
    raw_text: Optional[str]
    audio_path: Optional[str]
    entry: Optional[dict]
    reading: Optional[dict]
    knowledge: Optional[dict]
    tier: Optional[dict]
    final_response: Optional[str]
    user_history: list[float]

def interaction_node(state: PipelineState) -> PipelineState:
    entry = interaction_agent.build_journal_entry(state["user_id"], state.get("raw_text"), state.get("audio_path"))
    state["entry"] = entry.model_dump()
    return state

def analysis_node(state: PipelineState) -> PipelineState:
    from backend.models.schemas import JournalEntry
    entry = JournalEntry(**state["entry"])
    reading = analysis_agent.analyze(entry, state["user_history"])
    state["reading"] = reading.model_dump()
    return state

def knowledge_node(state: PipelineState) -> PipelineState:
    # TODO: only call when tier warrants grounding
    state["knowledge"] = None
    return state

def response_node(state: PipelineState) -> PipelineState:
    from backend.models.schemas import EmotionalReading
    reading = EmotionalReading(**state["reading"])
    tier = response_agent.determine_tier(reading)
    state["tier"] = tier.model_dump()
    state["final_response"] = response_agent.compose_response(tier, state["knowledge"])
    return state

def build_graph():
    graph = StateGraph(PipelineState)
    graph.add_node("interaction", interaction_node)
    graph.add_node("analysis", analysis_node)
    graph.add_node("knowledge", knowledge_node)
    graph.add_node("response", response_node)

    graph.set_entry_point("interaction")
    graph.add_edge("interaction", "analysis")
    graph.add_edge("analysis", "knowledge")
    graph.add_edge("knowledge", "response")
    graph.add_edge("response", END)

    return graph.compile()