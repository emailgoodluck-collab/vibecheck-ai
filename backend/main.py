from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .agent import app as agent_app
import uvicorn

app = FastAPI(title="VibeCheck AI API")

class QueryRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat(request: QueryRequest):
    try:
        # Initialize state
        initial_state = {
            "messages": [HumanMessage(content=request.message)],
            "cultural_anchors": [],
            "qloo_correlations": [],
            "current_domain": None,
            "target_domain": None,
            "reflection_count": 0,
            "is_grounded": False
        }
        
        # In a real app, we'd use a checkpointer for memory
        # For the hackathon, we'll run it as a one-off flow
        final_state = agent_app.invoke(initial_state)
        
        # Get the last AI message
        last_msg = final_state["messages"][-1].content
        return {"response": last_msg, "grounded": final_state["is_grounded"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
