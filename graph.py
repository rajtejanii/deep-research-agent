from langgraph.graph import StateGraph, START, END
from langgraph.types import Send, Command # <-- Import Command
from langgraph.checkpoint.memory import MemorySaver # <-- Import the Checkpointer
from state import ResearchState
from nodes import supervisor_node, search_node, synthesize_node, critic_node

workflow = StateGraph(ResearchState)

workflow.add_node("supervisor", supervisor_node)
workflow.add_node("searcher", search_node)
workflow.add_node("synthesizer", synthesize_node)
workflow.add_node("critic", critic_node)

def route_from_supervisor(state: ResearchState):
    print(f"\n🚀 Fanning out {len(state['sub_topics'])} search clones in parallel...")
    return [Send("searcher", {"topic": t}) for t in state["sub_topics"]]

def route_after_critic(state: ResearchState):
    if state["is_complete"] or state["iteration_count"] >= 2:
        return END
    print(f"\n🚀 Critic triggered! Fanning out {len(state['sub_topics'])} NEW search clones in parallel...")
    return [Send("searcher", {"topic": t}) for t in state["sub_topics"]]

workflow.add_edge(START, "supervisor")
workflow.add_conditional_edges("supervisor", route_from_supervisor)
workflow.add_edge("searcher", "synthesizer")
workflow.add_edge("synthesizer", "critic")
workflow.add_conditional_edges("critic", route_after_critic)

# --- NEW: SQLITE DATABASE PERSISTENCE ---
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver

# 1. We create a connection to a local database file (it creates it if it doesn't exist)
db_connection = sqlite3.connect("research_memory.db", check_same_thread=False)

# 2. We inject the SQLite database into the LangGraph compiler
memory = SqliteSaver(db_connection)
app = workflow.compile(checkpointer=memory)