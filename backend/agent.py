from typing import Annotated, TypedDict, List, Optional
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import os

# --- State Definition ---
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], "The conversation history"]
    cultural_anchors: List[str]
    qloo_correlations: List[dict]
    current_domain: Optional[str]
    target_domain: Optional[str]
    reflection_count: int
    is_grounded: bool

import requests
import os
from typing import List, Optional

class QlooClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.qloo.com/v2"
        self.headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def map_entity(self, entity_name: str):
        # Actual API call to search for entities
        response = requests.post(f"{self.base_url}/entities/search", json={"query": entity_name}, headers=self.headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("results"):
                return data["results"][0]
        return {"id": "unknown", "name": entity_name}

    def get_correlations(self, source_id: str, source_domain: str, target_domain: str):
        # Actual API call to get cross-domain correlations
        payload = {
            "source_id": source_id,
            "source_domain": source_domain,
            "target_domain": target_domain
        }
        response = requests.post(f"{self.base_url}/correlations", json=payload, headers=self.headers)
        if response.status_code == 200:
            return response.json().get("correlations", [])
        return []


qloo = QlooClient(api_key=os.getenv("QLOO_API_KEY", "mock_key"))
llm = ChatOpenAI(model="gpt-4o")

# --- Nodes ---

def taste_mapper(state: AgentState):
    """Extracts cultural anchors from user input."""
    last_message = state['messages'][-1].content
    # In production: use LLM to extract entities and map to Qloo IDs
    # Mock: simple keyword extraction
    anchors = [word for word in last_message.split() if len(word) > 4] 
    return {
        "cultural_anchors": anchors, 
        "is_grounded": len(anchors) > 0
    }

def qloo_graph_query(state: AgentState):
    """Queries Qloo API for cross-domain correlations."""
    if not state['cultural_anchors']:
        return {"qloo_correlations": []}
    
    correlations = []
    for anchor in state['cultural_anchors']:
        entity = qloo.map_entity(anchor)
        # Default target domain as 'lifestyle' for demo
        res = qloo.get_correlations(entity['id'], "general", "lifestyle")
        correlations.extend(res)
    
    return {"qloo_correlations": correlations}

def vibe_synthesizer(state: AgentState):
    """Synthesizes final recommendation based STRICTLY on Qloo data."""
    context = "\n".join([f"{c['name']} (Score: {c['score']})" for c in state['qloo_correlations']])
    
    prompt = f"""
    You are the VibeCheck AI Cultural Concierge. 
    USER INPUT: {state['messages'][-1].content}
    QLOO CULTURAL CORRELATIONS:
    {context}
    
    RULE: Your recommendation MUST be derived from the Qloo correlations above. 
    If the list is empty, tell the user you need 'cultural anchor points' to begin.
    Cite the specific correlation that drove your choice.
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    return {"messages": [response]}

def reflector(state: AgentState):
    """Validates that the output is grounded in Qloo data."""
    last_ai_msg = state['messages'][-1].content
    # Check if the AI cited a Qloo correlation
    is_valid = any(item['name'] in last_ai_msg for item in state['qloo_correlations'])
    
    if not is_valid and state['reflection_count'] < 2:
        return {
            "messages": [AIMessage(content="Wait, I'm guessing. Let me re-calculate using the Taste Graph...")],
            "reflection_count": state['reflection_count'] + 1
        }
    return {"is_grounded": is_valid}

# --- Graph Construction ---

workflow = StateGraph(AgentState)

workflow.add_node("mapper", taste_mapper)
workflow.add_node("query", qloo_graph_query)
workflow.add_node("synthesize", vibe_synthesizer)
workflow.add_node("reflect", reflector)

workflow.set_entry_point("mapper")
workflow.add_edge("mapper", "query")
workflow.add_edge("query", "synthesize")
workflow.add_edge("synthesize", "reflect")

workflow.add_conditional_edges(
    "reflect",
    lambda x: "synthesize" if not x["is_grounded"] and x["reflection_count"] < 2 else END
)

app = workflow.compile()
