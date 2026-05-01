from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agent import travel, get_response
from fastapi.middleware.cors import CORSMiddleware
import re

app = FastAPI(title="AI Travel Assistant API")

# Allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Flexible input model
class Query(BaseModel):
    source: str = None
    destination: str = None

@app.get("/")
def home():
    return {"message": "AI Travel Assistant Running 🚀"}

@app.post("/chat")
def chat(query: Query):

    # ✅ Case 1: structured input
    if query.source and query.destination:
        return {"response": travel(query.source, query.destination)}

    # ✅ Case 2: text input
    if query.message:
        match = re.search(r"from (.+?) to (.+)", query.message.lower())
        if match:
            src, dest = match.groups()
            return {"response": travel(src.strip(), dest.strip())}
        else:
            return {"response": get_response(query.message)}

    # ❌ Invalid input
    raise HTTPException(
        status_code=400,
        detail="Provide either 'message' OR 'source' and 'destination'"
    )