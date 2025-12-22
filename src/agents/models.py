from datetime import date
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

from datetime import date
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class Platform(BaseModel):
    name: Literal["linkedin", "instagram", "website"]

class DailyMetric(BaseModel):
    date: date
    platform: Literal["linkedin"] = "linkedin"
    impressions: int = 0
    clicks: int = 0
    reactions: int = 0
    engagement_rate: float = 0.0
    
class InstagramMetric(BaseModel):
    date: date
    platform: Literal["instagram"] = "instagram"
    impressions: int
    likes: int
    comments: int
    shares: int
    engagement_rate: float
    
class WebsiteMetric(BaseModel):
    date: date
    platform: Literal["website"] = "website"
    page_views: int
    unique_visitors: int
    bounce_rate: float

class PostMetric(BaseModel):
    post_id: str
    date: date
    format: Literal["reel", "carousel", "post", "article", "video"]
    caption: str
    likes: int
    comments: int
    saves: int
    shares: int
    reach: int
    engagement_rate: float
    
class Insight(BaseModel):
    title: str
    summary: str
    metric_basis: str
    time_range: str
    confidence: Literal["High", "Medium", "Low"]
    evidence: List[str] # e.g. "Row 5-10 in Daily Metrics"
    recommendation: str

class DataStore(BaseModel):
    linkedin_metrics: List[DailyMetric] = []
    instagram_metrics: List[InstagramMetric] = []
    website_metrics: List[WebsiteMetric] = []
    competitors: List[str] = []

# ---- ADK Helper ----
import os
import litellm
from dotenv import load_dotenv
from google.adk.models.lite_llm import LiteLlm
from google.adk.agents import Agent

def get_llm_model():
    """Configure and return the LiteLLM model wrapper"""
    load_dotenv()
    
    # Enable proxy mode per user instructions
    litellm.use_litellm_proxy = True
    
    # Configure model
    return LiteLlm(
        model="hackathon-gemini-2.5-flash",
        api_base=os.getenv("LITELLM_PROXY_API_BASE"),
        api_key=os.getenv("LITELLM_PROXY_GEMINI_API_KEY")
    )

def create_adk_agent(name: str, instruction: str):
    """Create a configured ADK agent"""
    model = get_llm_model()
    return Agent(
        name=name,
        model=model,
        instruction=instruction
    )
