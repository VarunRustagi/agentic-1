import os
import numpy as np
import re
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
    
    def __init__(self, store: DataStore, platform_insights: dict, status_writer=None):
        self.store = store
        self.platform_insights = platform_insights  # {platform: [insights]}
        self.status_writer = status_writer
        
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
    
    def _sanitize_html(self, text: str) -> str:
        """Remove all HTML tags from LLM response"""
        if not text:
            return ""
        
        text = str(text)
        # Remove all HTML tags (including multiline tags)
        text = re.sub(r'<[^>]*>', '', text, flags=re.DOTALL)
        # Remove any stray closing tags or fragments
        text = re.sub(r'</[^>]*>', '', text)
        # Remove incomplete opening tags at end
        text = re.sub(r'<[^>]*$', '', text)
        # Clean up extra whitespace/newlines left by removed tags
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _call_llm(self, prompt: str, context: str) -> str:
        """Helper to call LLM via LiteLLM directly"""
        if not API_BASE or not API_KEY:
            return "LLM unavailable."
            
        try:
            response = litellm.completion(
                model="hackathon-gemini-2.5-pro",
                api_base=API_BASE,
                api_key=API_KEY,
                messages=[
                    {"role": "system", "content": "You are a strategic marketing analyst. Provide executive-level insights. Do NOT use HTML tags, markdown formatting, or any markup. Use plain text only."},
                    {"role": "user", "content": f"{context}\n\n{prompt}"}
                ],
                max_tokens=500
            )
            
            # Track token usage
            try:
                from .token_tracker import record_llm_call
                record_llm_call("StrategyAgent", "strategy_generation", response, "hackathon-gemini-2.5-pro")
            except Exception as e:
                print(f"    ⚠ Could not track token usage: {e}")
            
            # Handle None response
            if not response or not response.choices or len(response.choices) == 0:
                return "LLM returned empty response."
            
            content = response.choices[0].message.content
            if content is None:
                return "LLM returned None content."
            
            # Sanitize HTML from LLM response before returning
            content = content.strip() if content else "LLM returned empty content."
            return self._sanitize_html(content)
        except Exception as e:
            return f"Analysis error: {str(e)[:100]}"
    
    def _analyze_growth_trend(self) -> Insight:
        """Analyze comprehensive growth across all platforms"""
        # Calculate growth rates
        li_growth = self._calculate_platform_growth(self.store.linkedin_metrics, 'impressions')
        ig_growth = self._calculate_platform_growth(self.store.instagram_metrics, 'impressions')
        web_growth = self._calculate_platform_growth(self.store.website_metrics, 'page_views')
        
        # Structured fact-based prompt with guardrails
        context = f"""Facts:
- LinkedIn 30-day growth: {li_growth:+.1f}%
- Instagram 30-day growth: {ig_growth:+.1f}%
- Website traffic 30-day growth: {web_growth:+.1f}%
- Overall Trend: {'Accelerating' if (li_growth+ig_growth+web_growth) > 10 else 'Stable' if (li_growth+ig_growth+web_growth) > -10 else 'Declining'}

Task:
Synthesize these growth metrics into a single executive trend statement using ONLY these numbers. Do not speculate on external causes."""
        
        summary = self._call_llm("Analyze this cross-platform growth data.", context)
        
        return Insight(
            title="📈 Growth Trend Analysis",
            summary=summary,
            metric_basis=f"LI: {li_growth:+.1f}%, IG: {ig_growth:+.1f}%, Web: {web_growth:+.1f}%",
            time_range="Last 30 days vs Previous 30 days",
            confidence="High",
            evidence=["Aggregated platform growth rates"],
            recommendation="Invest in highest-growth channel to maximize momentum."
        )
    
    def _identify_leakage(self) -> Insight:
        """Identify where we are losing engagement"""
        li_eng = np.mean([m.engagement_rate for m in self.store.linkedin_metrics[-30:]]) if self.store.linkedin_metrics else 0
        ig_eng = np.mean([m.engagement_rate for m in self.store.instagram_metrics[-30:]]) if self.store.instagram_metrics else 0
        web_bounce = np.mean([m.bounce_rate for m in self.store.website_metrics[-30:]]) if self.store.website_metrics else 0
        
        # Structured fact-based prompt with guardrails
        context = f"""Facts:
- LinkedIn engagement rate: {li_eng:.2%}
- Instagram engagement rate: {ig_eng:.2%}
- Website bounce rate: {web_bounce:.1%} (High bounce = leakage)
- Primary leakage point: {'Website' if web_bounce > 0.6 else 'LinkedIn' if li_eng < 0.02 else 'Instagram' if ig_eng < 0.05 else 'None'}

Task:
Identify the most critical engagement drop-off point based ONLY on these metrics. Explain the business impact without generic advice."""
        
        summary = self._call_llm("Analyze engagement leakage points.", context)
        
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
        top_platform = sorted_platforms[0][0]
        
        # Structured fact-based prompt with guardrails
        context = f"""Facts:
- Platform Performance Scores (0-10 scale):
  - {sorted_platforms[0][0]}: {sorted_platforms[0][1]:.2f} (Top Performer)
  - {sorted_platforms[1][0]}: {sorted_platforms[1][1]:.2f}
  - {sorted_platforms[2][0]}: {sorted_platforms[2][1]:.2f}

Task:
Recommend resource allocation prioritizing the top performing platform. Base the justification ONLY on the calculated scores provided."""
        
        summary = self._call_llm("Recommend platform prioritization.", context)
        
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
        
        rec_text = " | ".join(all_recommendations[:5])
        
        # Structured fact-based prompt with guardrails
        context = f"""Facts - Platform-level Recommendations:
{rec_text}

Rules:
1. Use ONLY the provided platform recommendations.
2. Do NOT introduce external benchmarks or general knowledge.
3. Synthesize these into a cohesive C-suite strategy.

Task:
Create a unified strategic plan for the next quarter based on the specific platform needs identified above."""
        
        summary = self._call_llm("Synthesize strategic plan.", context)
        
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
