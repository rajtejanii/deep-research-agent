from typing import TypedDict, List, Annotated
import operator

class ResearchState(TypedDict):
    question: str
    sub_topics: List[str]
    research_notes: Annotated[List[str], operator.add]
    final_report: str
    is_complete: bool
    
    # --- NEW FIELDS FOR THE REFLECTION LOOP ---
    iteration_count: int
    critique: str

print("State schema updated with reflection fields!")