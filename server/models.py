from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    filters: Optional[Dict[str, Any]] = None
    top_k: int = Field(default=20, ge=1, le=50)

class ChartDataPoint(BaseModel):
    name: str
    value: int
    percentage: float

class SneakPeekData(BaseModel):
    most_popular: Optional[List[ChartDataPoint]] = None
    top_behaviors: Optional[List[ChartDataPoint]] = None
    shopping_intent: Optional[List[ChartDataPoint]] = None
    purchase_drivers: Optional[List[ChartDataPoint]] = None

class StatsResponse(BaseModel):
    total_items: int
    source_counts: Dict[str, int]
    last_updated: Optional[str] = None
    volume_funnel: Optional[Dict[str, Any]] = None
    emergent_themes: Optional[List[Dict[str, Any]]] = None
    sneak_peek: Optional[SneakPeekData] = None

class SummaryRequest(BaseModel):
    questions: str | List[int] = "all" # or specific indices

class SummaryResponse(BaseModel):
    answers: List[Dict[str, Any]]
    emergent_themes: List[Dict[str, Any]]
    volume_funnel: Dict[str, Any]

class IngestRequest(BaseModel):
    mode: str = Field(default="demo", pattern="^(demo|full)$")

class IngestStatusResponse(BaseModel):
    is_ingesting: bool
    mode: Optional[str] = None
    status: str
    progress: int
    total_steps: int
    last_error: Optional[str] = None
    logs: Optional[List[str]] = None
