import os
import numpy as np
from datetime import timedelta
from dotenv import load_dotenv
import litellm
from .models import DataStore, InstagramMetric, Insight

load_dotenv()
litellm.use_litellm_proxy = True
API_BASE = os.getenv("LITELLM_PROXY_API_BASE")
API_KEY = os.getenv("LITELLM_PROXY_GEMINI_API_KEY")

class InstagramAnalyticsAgent:
    """Specialized agent for Instagram performance analysis"""
    
    def __init__(self, store: DataStore):
        self.metrics = store.instagram_metrics
        
    def analyze(self) -> list[Insight]:
        """Generate Instagram-specific insights"""
        insights = []
        
        # 1. Reach vs Engagement Patterns
        reach_insight = self._analyze_reach_vs_engagement()
        if reach_insight:
            insights.append(reach_insight)
            
        # 2. Format Performance (will be in synthetic data)
        format_insight = self._analyze_format_performance()
        if format_insight:
            insights.append(format_insight)
            
        return insights
    
    def _call_llm(self, prompt: str, context: str) -> str:
        """Helper to call LLM via LiteLLM directly"""
        if not API_BASE or not API_KEY:
            return "LLM unavailable."
            
        try:
            response = litellm.completion(
                model="hackathon-gemini-2.5-flash",
                api_base=API_BASE,
                api_key=API_KEY,
                messages=[
                    {"role": "system", "content": "You are an Instagram marketing analyst. Provide concise, actionable insights."},
                    {"role": "user", "content": f"{context}\n\n{prompt}"}
                ],
                max_tokens=150
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Analysis error: {str(e)[:100]}"
    
    def _analyze_reach_vs_engagement(self) -> Insight:
        """Analyze if we're reaching new audiences or just engaging existing"""
        if len(self.metrics) < 30:
            return None
            
        sorted_metrics = sorted(self.metrics, key=lambda x: x.date)
        recent_30 = sorted_metrics[-30:]
        
        # High reach + low engagement = discovery mode
        # Low reach + high engagement = retention mode
        avg_reach = np.mean([m.impressions for m in recent_30])
        avg_engagement = np.mean([m.engagement_rate for m in recent_30])
        
        reach_growth = (recent_30[-1].impressions - recent_30[0].impressions) / recent_30[0].impressions * 100
        
        context = f"Avg reach: {avg_reach:.0f} impressions. Avg engagement rate: {avg_engagement:.2%}. Reach growth: {reach_growth:+.1f}%."
        summary = self._call_llm("Are we in discovery or retention mode on Instagram?", context)
        
        return Insight(
            title="Instagram: Discovery vs. Retention",
            summary=summary,
            metric_basis=f"Engagement rate: {avg_engagement:.2%}",
            time_range=f"{recent_30[0].date} to {recent_30[-1].date}",
            confidence="High",
            evidence=["Instagram metrics, last 30 days"],
            recommendation="Balance viral content with community engagement."
        )
    
    def _analyze_format_performance(self) -> Insight:
        """Analyze Reels vs Posts performance"""
        if len(self.metrics) < 20:
            return None
            
        # Since we're generating synthetic data, we can infer format from engagement patterns
        # High engagement days = likely Reels
        sorted_metrics = sorted(self.metrics, key=lambda x: x.date)
        
        high_engagement_days = [m for m in sorted_metrics if m.engagement_rate > 0.10]
        low_engagement_days = [m for m in sorted_metrics if m.engagement_rate <= 0.10]
        
        high_avg = np.mean([m.engagement_rate for m in high_engagement_days]) if high_engagement_days else 0
        low_avg = np.mean([m.engagement_rate for m in low_engagement_days]) if low_engagement_days else 0
        
        context = f"High-performing content (likely Reels): {high_avg:.2%} avg engagement ({len(high_engagement_days)} days). Lower-performing: {low_avg:.2%} ({len(low_engagement_days)} days)."
        summary = self._call_llm("Which Instagram format should we prioritize?", context)
        
        return Insight(
            title="Instagram: Format Strategy",
            summary=summary,
            metric_basis=f"Reels: ~{high_avg:.2%} engagement",
            time_range="Last 60 days",
            confidence="Medium",
            evidence=["Format inference from engagement patterns"],
            recommendation="Increase Reels production to 60%+ of content mix."
        )
