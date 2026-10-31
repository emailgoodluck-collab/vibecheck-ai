from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
try:
    from .agent import vibe_check_engine
except ImportError:
    from agent import vibe_check_engine
import uvicorn

app = FastAPI(title="VibeCheck AI API")

class QueryRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat(request: QueryRequest):
    try:
        initial_state = {
            "messages": [HumanMessage(content=request.message)],
            "raw_query": request.message,
            "extracted_anchors": {},
            "target_domains": [],
            "target_location": "Global",
            "qloo_entity_ids": {},
            "correlations": {},
            "synthesized_vibe": "",
            "validation_passed": False,
            "used_fallback": False,
            "final_output": "",
        }
        final_state = await vibe_check_engine.ainvoke(initial_state)
        return {
            "response": final_state["final_output"],
            "grounded": final_state["validation_passed"] and not final_state["used_fallback"],
            "anchors": final_state["extracted_anchors"],
            "domains": final_state["target_domains"],
            "location": final_state["target_location"],
            "demo_mode": final_state["used_fallback"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
