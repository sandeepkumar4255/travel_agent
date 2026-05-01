from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict
from agent import travel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI Travel Assistant API")

# ======================
# 🌐 CORS (for frontend)
# ======================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================
# 📥 INPUT MODEL
# ======================
class Query(BaseModel):
    source: str
    destination: str

    # ignore extra fields if frontend sends anything extra
    model_config = ConfigDict(extra="ignore")


# ======================
# 🏠 HOME
# ======================
@app.get("/")
def home():
    return {"message": "AI Travel Assistant Running 🚀"}


# ======================
# 🚀 MAIN API
# ======================
@app.post("/chat")
def chat(query: Query):
    try:
        result = travel(query.source, query.destination)

        return {
            "status": "success",
            "response": result
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )