from typing import List, Optional, TypedDict
from langgraph.graph.message import AnyMessage

class AgentState(TypedDict):
    messages: List[AnyMessage]
    thread_id: str
    run_id: str
    current_topic: Optional[str]
    lesson_progress: Optional[dict] 