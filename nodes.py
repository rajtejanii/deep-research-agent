from pydantic import BaseModel, Field
from typing import List, TypedDict
from state import ResearchState
from tools import llm, search_tool
from langgraph.types import interrupt  # <-- 1. Import the interrupt function

class CriticOutput(BaseModel):
    is_approved: bool = Field(description="True if the report perfectly answers the user's question. False if missing critical information.")
    new_search_queries: List[str] = Field(description="If is_approved is False, provide exactly 2 new search queries to fill the gaps. If True, return an empty list.")

class SearchWorkerState(TypedDict):
    topic: str

def supervisor_node(state: ResearchState):
    question = state["question"]
    print(f"\n👨‍💼 Supervisor analyzing: {question}")
    
    prompt = f"Break down this research question into exactly 2 distinct DuckDuckGo search queries. Return ONLY the queries separated by commas. Question: {question}"
    response = llm.invoke(prompt)
    queries = [q.strip() for q in response.content.split(",")]
    
    # --- 2. THE SAFETY GATE ---
    # The graph will completely freeze here and surface this data to the terminal.
    human_decision = interrupt({
        "message": "Please review the planned search queries.",
        "planned_queries": queries
    })
    
    # 3. Handle the human's response when they resume the graph
    if human_decision.lower() != "approve":
        print(f"   -> ✍️ Human override applied! New queries: {human_decision}")
        queries = [q.strip() for q in human_decision.split(",")]
    else:
        print("   -> ✅ Human approved the original plan.")
        
    return {"sub_topics": queries}

# (Keep your existing search_node, synthesize_node, and critic_node below exactly as they are)
def search_node(state: SearchWorkerState):
    topic = state["topic"]
    print(f"   -> ⚡ PARALLEL SCRAPE INITIATED: {topic}")
    try:
        result = search_tool.invoke(topic)
        note = f"Topic: {topic}\nResult: {result}"
    except Exception as e:
        note = f"Topic: {topic}\nResult: Failed to search - {str(e)}"
    return {"research_notes": [note]}

def synthesize_node(state: ResearchState):
    print("\n📝 Synthesizer compiling report...")
    question = state["question"]
    notes = "\n\n".join(state["research_notes"])
    prompt = f"Write a brief, structured summary report answering the question '{question}' using ONLY the following raw notes:\n{notes}"
    response = llm.invoke(prompt)
    return {"final_report": response.content}

def critic_node(state: ResearchState):
    print("\n🧐 Critic evaluating the report for gaps...")
    question = state["question"]
    report = state["final_report"]
    iteration = state.get("iteration_count", 0)
    prompt = f"""
    You are an expert reviewer. Does this report fully and completely answer the original question?
    Question: {question}
    Report: {report}
    """
    structured_llm = llm.with_structured_output(CriticOutput)
    response = structured_llm.invoke(prompt)
    if response.is_approved:
        print("   -> Critic Approved! Report is final.")
        return {"is_complete": True, "critique": "Approved"}
    else:
        print(f"   -> Critic Rejected. Demanding new research on: {response.new_search_queries}")
        return {
            "is_complete": False, 
            "sub_topics": response.new_search_queries, 
            "iteration_count": iteration + 1,
            "critique": "Rejected"
        }