import os
import numpy as np
from dotenv import load_dotenv
import litellm
from .models import DataStore, Insight
from .linkedin_agent import LinkedInAnalyticsAgent
from .instagram_agent import InstagramAnalyticsAgent
from .website_agent import WebsiteAnalyticsAgent

load_dotenv()
litellm.use_litellm_proxy = True
API_BASE = os.getenv("LITELLM_PROXY_API_BASE")
API_KEY = os.getenv("LITELLM_PROXY_GEMINI_API_KEY")

class StrategyAgent:
    """Meta-agent that synthesizes cross-platform insights for C-suite"""
    
    def __init__(self, store: DataStore, platform_insights: dict):
        self.store = store
        self.platform_insights = platform_insights  # {platform: [insights]}
        
    def generate_executive_summary(self) -> list[Insight]:
        """Answer the 4 core C-suite questions"""
        insights = []
        
        # 1. Are we growing or declining?
        growth_insight = self._analyze_growth_trend()
        if growth_insight:
            insights.append(growth_insight)
            
        # 2. Where is the leakage?
        leakage_insight = self._identify_leakage()
        if leakage_insight:
            insights.append(leakage_insight)
            
        # 3. Which platforms deserve attention?
        priority_insight = self._prioritize_platforms()
        if priority_insight:
            insights.append(priority_insight)
            
        # 4. What strategic levers should we pull?
        strategy_insight= self._recommend_strategy()
        if strategy_insight:
            insights.append(strategy_insight)
            
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
                    {"role": "system", "content": "You are a C-suite strategy advisor. Provide executive-level insights with clear recommendations."},
                    {"role": "user", "content": f"{context}\n\n{prompt}"}
                ],
                max_tokens=300
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Analysis unavailable: {str(e)[:100]}"
    
    def _analyze_growth_trend(self) -> Insight:
        """Cross-platform growth analysis"""
        # Calculate recent growth for each platform
        linkedin_growth = self._calculate_platform_growth(self.store.linkedin_metrics, 'impressions')
        instagram_growth = self._calculate_platform_growth(self.store.instagram_metrics, 'impressions')
        website_growth = self._calculate_platform_growth(self.store.website_metrics, 'page_views')
        
        context = f"LinkedIn: {linkedin_growth:+.1f}% | Instagram: {instagram_growth:+.1f}% | Website: {website_growth:+.1f}%"
        summary = self._call_llm("Are we growing or declining overall? What's the trend?", context)
        
        return Insight(
            title="📈 Growth Trend Analysis",
            summary=summary,
            metric_basis=f"30-day growth rates across platforms",
            time_range="Last 30 days",
            confidence="High",
            evidence=["LinkedIn, Instagram, Website metrics"],
            recommendation="Focus resources on highest-growth channel."
        )
    
    def _identify_leakage(self) -> Insight:
        """Identify where we're losing audience/engagement"""
        # Check engagement rates and bounce rates
        linkedin_eng = np.mean([m.engagement_rate for m in self.store.linkedin_metrics[-30:]]) if self.store.linkedin_metrics else 0
        instagram_eng = np.mean([m.engagement_rate for m in self.store.instagram_metrics[-30:]]) if self.store.instagram_metrics else 0
        website_bounce = np.mean([m.bounce_rate for m in self.store.website_metrics[-30:]]) if self.store.website_metrics else 0
        
        context = f"LinkedIn engagement: {linkedin_eng:.1%}, Instagram engagement: {instagram_eng:.1%}, Website bounce: {website_bounce:.1%}"
        summary = self._call_llm("Where are we losing engagement? Identify the leakage points.", context)
        
        return Insight(
            title="⚠️ Leakage Analysis",
            summary=summary,
            metric_basis=f"Engagement & bounce metrics",
            time_range="Last 30 days",
            confidence="High",
            evidence=["Cross-platform engagement comparison"],
            recommendation="Address highest-leakage channel first."
        )
    
    def _prioritize_platforms(self) -> Insight:
        """Recommend resource allocation across platforms"""
        # Score each platform based on growth + engagement
        scores = {
            'LinkedIn': self._platform_score(self.store.linkedin_metrics, 'linkedin'),
            'Instagram': self._platform_score(self.store.instagram_metrics, 'instagram'),
            'Website': self._platform_score(self.store.website_metrics, 'website')
        }
        
        sorted_platforms = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        context = f"Platform scores: {sorted_platforms[0][0]} ({sorted_platforms[0][1]:.2f}), {sorted_platforms[1][0]} ({sorted_platforms[1][1]:.2f}), {sorted_platforms[2][0]} ({sorted_platforms[2][1]:.2f})"
        summary = self._call_llm("Which platform deserves the most attention and resources?", context)
        
        return Insight(
            title="🎯 Platform Prioritization",
            summary=summary,
            metric_basis=f"Top: {sorted_platforms[0][0]}",
            time_range="Based on recent performance",
            confidence="Medium",
            evidence=["Composite score of growth + engagement"],
            recommendation=f"Allocate 50% resources to {sorted_platforms[0][0]}."
        )
    
    def _recommend_strategy(self) -> Insight:
        """Strategic recommendations"""
        # Synthesize all platform insights
        all_recommendations = []
        for platform, insights_list in self.platform_insights.items():
            for insight in insights_list:
                all_recommendations.append(f"{platform}: {insight.recommendation}")
        
        context = "Platform recommendations: " + " | ".join(all_recommendations[:5])
        summary = self._call_llm("What strategic levers should we pull next quarter?", context)
        
        return Insight(
            title="🚀 Strategic Recommendations",
            summary=summary,
            metric_basis="Multi-platform analysis",
            time_range="Next Quarter",
            confidence="Medium",
            evidence=["Synthesis of all platform agents"],
            recommendation="Execute top 3 priority actions from platform insights."
        )
    
    def _calculate_platform_growth(self, metrics, field):
        """Calculate growth rate for a platform"""
        if len(metrics) < 60:
            return 0.0
            
        sorted_m = sorted(metrics, key=lambda x: x.date)
        recent_30 = sorted_m[-30:]
        prev_30 = sorted_m[-60:-30]
        
        recent_avg = np.mean([getattr(m, field) for m in recent_30])
        prev_avg = np.mean([getattr(m, field) for m in prev_30])
        
        return ((recent_avg - prev_avg) / prev_avg * 100) if prev_avg > 0 else 0.0
    
    def _platform_score(self, metrics, platform_type):
        """Calculate composite score for platform prioritization"""
        if not metrics or len(metrics) < 30:
            return 0.0
            
        recent = metrics[-30:]
        
        if platform_type == 'linkedin':
            avg_engagement = np.mean([m.engagement_rate for m in recent])
            growth = self._calculate_platform_growth(metrics, 'impressions')
            return avg_engagement * 10 + (growth / 10)
            
        elif platform_type == 'instagram':
            avg_engagement = np.mean([m.engagement_rate for m in recent])
            growth = self._calculate_platform_growth(metrics, 'impressions')
            return avg_engagement * 10 + (growth / 10)
            
        elif platform_type == 'website':
            avg_bounce = np.mean([m.bounce_rate for m in recent])
            growth = self._calculate_platform_growth(metrics, 'page_views')
            return (1 - avg_bounce) * 5 + (growth / 10)
            
        return 0.0
