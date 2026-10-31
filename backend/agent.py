"""VibeCheck cultural recommendation graph.

Qloo is the source of cultural correlations when configured. The deterministic
fallback keeps the demo usable without pretending it came from Qloo.
"""

import os
import re
from typing import Any, Dict, List, Optional, TypedDict

import httpx
from langgraph.graph import END, StateGraph

QLOO_API_KEY = os.getenv("QLOO_API_KEY")
QLOO_BASE_URL = os.getenv("QLOO_BASE_URL", "https://api.qloo.com/v2")


class AgentTasteState(TypedDict):
    raw_query: str
    extracted_anchors: Dict[str, str]
    target_domains: List[str]
    target_location: str
    qloo_entity_ids: Dict[str, str]
    correlations: Dict[str, Any]
    synthesized_vibe: str
    validation_passed: bool
    used_fallback: bool
    final_output: str


class QlooGraphQuery:
    def __init__(self, api_key: Optional[str] = QLOO_API_KEY) -> None:
        self.api_key = api_key

    @property
    def headers(self) -> Dict[str, str]:
        if not self.api_key:
            return {"Content-Type": "application/json"}
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    async def resolve_entity_id(self, domain: str, name: str) -> Optional[str]:
        """Resolve an anchor only when a Qloo credential is configured."""
        if not self.api_key:
            return None
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{QLOO_BASE_URL}/search",
                    headers=self.headers,
                    params={"query": name, "type": domain},
                )
            if response.is_success:
                results = response.json().get("results", [])
                if results and results[0].get("id"):
                    return results[0]["id"]
        except (httpx.HTTPError, ValueError):
            pass
        return None

    async def fetch_cross_domain_affinity(
        self, source_ids: List[str], target_domain: str, location: str
    ) -> List[Dict[str, Any]]:
        if not self.api_key or not source_ids:
            return []
        payload = {
            "sources": source_ids,
            "target_domain": target_domain,
            "filter": {"location": location} if location != "Global" else {},
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{QLOO_BASE_URL}/correlations", headers=self.headers, json=payload
                )
            if response.is_success:
                return response.json().get("correlations", [])
        except (httpx.HTTPError, ValueError):
            pass
        return []


qloo_client = QlooGraphQuery()


def _extract_anchors(raw: str) -> Dict[str, str]:
    """Keep the first meaningful phrases as explainable cultural seeds."""
    words = re.findall(r"[A-Za-z][A-Za-z'-]{3,}", raw)
    ignored = {"with", "that", "this", "from", "want", "find", "something", "feel"}
    anchors = [word.lower() for word in words if word.lower() not in ignored]
    return {f"anchor_{index + 1}": value for index, value in enumerate(dict.fromkeys(anchors[:6]))}


async def plan_node(state: AgentTasteState) -> AgentTasteState:
    raw = state["raw_query"].lower()
    domains: List[str] = []
    if any(key in raw for key in ("film", "movie", "cinema", "watch")):
        domains.append("film")
    if any(key in raw for key in ("music", "album", "jazz", "song", "listen")):
        domains.append("music")
    if any(key in raw for key in ("hotel", "stay", "lodging", "travel")):
        domains.append("hospitality")
    if any(key in raw for key in ("restaurant", "food", "dining", "bar", "eat")):
        domains.append("dining")
    if any(key in raw for key in ("place", "city", "museum", "architecture")):
        domains.append("place")
    location = "Global"
    for candidate in ("Tokyo", "Kyoto", "Lagos", "London", "New York", "Paris"):
        if candidate.lower() in raw:
            location = candidate
            break
    return {
        **state,
        "extracted_anchors": _extract_anchors(state["raw_query"]),
        "target_domains": list(dict.fromkeys(domains)) or ["dining", "hospitality"],
        "target_location": location,
    }


async def execute_qloo_node(state: AgentTasteState) -> AgentTasteState:
    resolved: Dict[str, str] = {}
    for domain, name in state["extracted_anchors"].items():
        entity_id = await qloo_client.resolve_entity_id("general", name)
        if entity_id:
            resolved[domain] = entity_id
    correlations: Dict[str, List[Dict[str, Any]]] = {}
    source_ids = list(resolved.values())
    for target in state["target_domains"]:
        correlations[target] = await qloo_client.fetch_cross_domain_affinity(
            source_ids, target, state["target_location"]
        )
    return {**state, "qloo_entity_ids": resolved, "correlations": correlations, "used_fallback": not bool(correlations)}


async def synthesize_node(state: AgentTasteState) -> AgentTasteState:
    lines = ["Your cultural direction", ""]
    if state["used_fallback"]:
        lines.append("This is a local demo reading of your signals. Connect QLOO_API_KEY to ground it in the live taste graph.")
    else:
        lines.append(f"Grounded across {state['target_location']} and the Qloo taste graph.")
    lines.append("")
    for domain, items in state["correlations"].items():
        if items:
            lines.append(f"{domain.title()}: {items[0].get('name', 'A strong match')} ({items[0].get('affinity_score', items[0].get('score', 0.9)):.2f} affinity)")
    if not any(state["correlations"].values()):
        lines.append(f"Your strongest anchors are: {', '.join(state['extracted_anchors'].values()) or 'an open mind'}.")
        lines.append("The pattern points toward atmosphere, specificity, and one unexpected detail.")
    return {**state, "synthesized_vibe": "\n".join(lines)}


async def reflect_node(state: AgentTasteState) -> AgentTasteState:
    has_seeds = bool(state["extracted_anchors"])
    state["validation_passed"] = has_seeds and bool(state["synthesized_vibe"])
    state["final_output"] = state["synthesized_vibe"] if state["validation_passed"] else "REJECTED: Add at least one cultural signal to begin."
    return state


workflow = StateGraph(AgentTasteState)
workflow.add_node("planner", plan_node)
workflow.add_node("qloo_executor", execute_qloo_node)
workflow.add_node("synthesizer", synthesize_node)
workflow.add_node("reflector", reflect_node)
workflow.set_entry_point("planner")
workflow.add_edge("planner", "qloo_executor")
workflow.add_edge("qloo_executor", "synthesizer")
workflow.add_edge("synthesizer", "reflector")
workflow.add_edge("reflector", END)
vibe_check_engine = workflow.compile()
