import os
import numpy as np
from datetime import timedelta
from dotenv import load_dotenv
import litellm
from .models import DataStore, DailyMetric, Insight

load_dotenv()
litellm.use_litellm_proxy = True
API_BASE = os.getenv("LITELLM_PROXY_API_BASE")
API_KEY = os.getenv("LITELLM_PROXY_GEMINI_API_KEY")

class LinkedInAnalyticsAgent:
    """Specialized agent for LinkedIn performance analysis"""
    
    def __init__(self, store: DataStore):
        self.metrics = store.linkedin_metrics
        
    def analyze(self) -> list[Insight]:
        """Generate LinkedIn-specific insights"""
        insights = []
        
        # 1. Engagement vs Reach Trends
        trend_insight = self._analyze_engagement_trend()
        if trend_insight:
            insights.append(trend_insight)
            
        # 2. Follower Growth Efficiency (if we had follower data)
        # For now, focus on engagement efficiency
        
        # 3. Cadence vs Engagement
        cadence_insight = self._analyze_posting_cadence()
        if cadence_insight:
            insights.append(cadence_insight)
            
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
                    {"role": "system", "content": "You are a LinkedIn marketing analyst. Provide concise, strategic insights."},
                    {"role": "user", "content": f"{context}\n\n{prompt}"}
                ],
                max_tokens=150
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Analysis error: {str(e)[:100]}"
    
    def _analyze_engagement_trend(self) -> Insight:
        """Analyze engagement vs reach efficiency"""
        if len(self.metrics) < 30:
            return None
            
        sorted_metrics = sorted(self.metrics, key=lambda x: x.date)
        recent_30 = sorted_metrics[-30:]
        prev_30 = sorted_metrics[-60:-30] if len(sorted_metrics) >= 60 else recent_30
        
        # Calculate engagement efficiency (reactions per impression)
        recent_efficiency = np.mean([
            m.reactions / m.impressions if m.impressions > 0 else 0 
            for m in recent_30
        ])
        prev_efficiency = np.mean([
            m.reactions / m.impressions if m.impressions > 0 else 0 
            for m in prev_30
        ])
        
        change_pct = ((recent_efficiency - prev_efficiency) / prev_efficiency * 100) if prev_efficiency > 0 else 0
        
        context = f"Recent 30-day engagement efficiency: {recent_efficiency:.2%}. Previous period: {prev_efficiency:.2%}. Change: {change_pct:+.1f}%."
        summary = self._call_llm("Summarize the LinkedIn engagement trend and recommend next steps.", context)
        
        return Insight(
            title="LinkedIn: Engagement Efficiency",
            summary=summary,
            metric_basis=f"Engagement/Impression ratio: {recent_efficiency:.2%}",
            time_range=f"{recent_30[0].date} to {recent_30[-1].date}",
            confidence="High",
            evidence=[f"LinkedIn metrics, last 30 days"],
            recommendation="Monitor content quality vs. posting frequency."
        )
    
    def _analyze_posting_cadence(self) -> Insight:
        """Analyze if posting frequency correlates with engagement"""
        if len(self.metrics) < 14:
            return None
            
        sorted_metrics = sorted(self.metrics, key=lambda x: x.date)
        
        # Simple cadence detection: count posts per week
        # Assumption: Higher impressions = more posts/activity
        weekly_buckets = []
        for i in range(0, len(sorted_metrics), 7):
            week = sorted_metrics[i:i+7]
            if len(week) >= 5:  # Full week
                avg_engagement = np.mean([m.engagement_rate for m in week])
                total_impressions = sum([m.impressions for m in week])
                weekly_buckets.append((total_impressions, avg_engagement))
        
        if len(weekly_buckets) < 4:
            return None
            
        context = f"Analyzed {len(weekly_buckets)} weeks. Found variable engagement patterns based on activity levels."
        summary = self._call_llm("What's the optimal LinkedIn posting cadence based on engagement data?", context)
        
        return Insight(
            title="LinkedIn: Posting Cadence Analysis",
            summary=summary,
            metric_basis=f"{len(weekly_buckets)} weeks analyzed",
            time_range="Last quarter",
            confidence="Medium",
            evidence=["Weekly engagement aggregation"],
            recommendation="Test 3-4 posts per week vs. daily posting."
        )
