import os
import numpy as np
from datetime import timedelta
from dotenv import load_dotenv
import litellm
from .models import DataStore, WebsiteMetric, Insight

load_dotenv()
litellm.use_litellm_proxy = True
API_BASE = os.getenv("LITELLM_PROXY_API_BASE")
API_KEY = os.getenv("LITELLM_PROXY_GEMINI_API_KEY")

class WebsiteAnalyticsAgent:
    """Specialized agent for Website performance analysis"""
    
    def __init__(self, store: DataStore, status_writer=None):
        self.metrics = store.website_metrics
        self.status_writer = status_writer
        
    def analyze(self) -> list[Insight]:
        """Generate Website-specific insights"""
        insights = []
        
        # 1. Traffic Quality (bounce rate analysis)
        traffic_insight = self._analyze_traffic_quality()
        if traffic_insight:
            insights.append(traffic_insight)
            
        # 2. Conversion Funnel (visitor retention)
        funnel_insight = self._analyze_conversion_funnel()
        if funnel_insight:
            insights.append(funnel_insight)
            
        return insights
    
    def _call_llm(self, prompt: str, context: str) -> str:
        """Helper to call LLM via LiteLLM directly"""
        if not API_BASE or not API_KEY:
            print("    ⚠ LLM API not configured, using fallback")
            return "LLM unavailable."
            
        try:
            msg = "    🔄 Calling LLM for analysis..."
            print(msg)
            if self.status_writer:
                self.status_writer.write(msg)
            response = litellm.completion(
                model="hackathon-gemini-2.5-pro",
                api_base=API_BASE,
                api_key=API_KEY,
                messages=[
                    {"role": "system", "content": "You are a website analytics specialist. Provide data-driven recommendations."},
                    {"role": "user", "content": f"{context}\n\n{prompt}"}
                ],
                max_tokens=500,
                timeout=30  # 30 second timeout
            )
            
            # Track token usage
            try:
                from .token_tracker import record_llm_call
                record_llm_call("WebsiteAnalyticsAgent", "insight_generation", response, "hackathon-gemini-2.5-pro")
            except Exception as e:
                print(f"    ⚠ Could not track token usage: {e}")
            
            msg = "    ✓ LLM response received"
            print(msg)
            if self.status_writer:
                self.status_writer.write(msg)
            # Handle None response
            if not response or not response.choices or len(response.choices) == 0:
                return "LLM returned empty response."
            
            content = response.choices[0].message.content
            if content is None:
                return "LLM returned None content."
            
            return content.strip() if content else "LLM returned empty content."
        except Exception as e:
            return f"Analysis error: {str(e)[:100]}"
    
    def _analyze_traffic_quality(self) -> Insight:
        """Analyze bounce rate and traffic quality"""
        if len(self.metrics) < 30:
            return None
            
        sorted_metrics = sorted(self.metrics, key=lambda x: x.date)
        recent_30 = sorted_metrics[-30:]
        
        avg_bounce_rate = np.mean([m.bounce_rate for m in recent_30])
        avg_page_views = np.mean([m.page_views for m in recent_30])
        
        # Quality score: lower bounce + higher views = better quality
        quality_score = (1 - avg_bounce_rate) * (avg_page_views / 1000)
        
        # Structured fact-based prompt
        context = f"""Facts:
- Average bounce rate (last 30 days): {avg_bounce_rate:.1%}
- Average daily page views: {avg_page_views:.0f}
- Traffic quality score: {quality_score:.2f}
- Quality level: {'Poor' if avg_bounce_rate > 0.7 else 'Fair' if avg_bounce_rate > 0.5 else 'Good'}

Task:
Explain what this bounce rate and traffic volume indicate about visitor intent and landing page effectiveness. Provide 1-2 specific recommendations based ONLY on these facts."""
        
        summary = self._call_llm("Analyze this data.", context)
        
        # Provide fallback if LLM failed
        if not summary or summary.startswith("Analysis error") or summary.startswith("LLM"):
            quality_level = 'Poor' if avg_bounce_rate > 0.7 else 'Fair' if avg_bounce_rate > 0.5 else 'Good'
            summary = f"Bounce rate: {avg_bounce_rate:.1%} ({quality_level.lower()} quality). Average daily page views: {avg_page_views:.0f}. {'High bounce suggests poor landing page relevance or slow load times' if avg_bounce_rate > 0.6 else 'Good engagement indicates effective content and navigation'}."
        
        return Insight(
            title="Website: Traffic Quality",
            summary=summary,
            metric_basis=f"Bounce rate: {avg_bounce_rate:.1%}",
            time_range=f"{recent_30[0].date} to {recent_30[-1].date}",
            confidence="High",
            evidence=["Website metrics, last 30 days"],
            recommendation="Improve landing page relevance and load time."
        )
    
    def _analyze_conversion_funnel(self) -> Insight:
        """Analyze visitor-to-engagement conversion"""
        if len(self.metrics) < 14:
            return None
            
        sorted_metrics = sorted(self.metrics, key=lambda x: x.date)
        recent = sorted_metrics[-14:]
        
        # Calculate visitor retention (pages per visitor)
        avg_pages_per_visitor = np.mean([
            m.page_views / m.unique_visitors if m.unique_visitors > 0 else 0
            for m in recent
        ])
        
        engagement_level = 'Strong' if avg_pages_per_visitor > 2.5 else 'Moderate' if avg_pages_per_visitor > 1.5 else 'Weak'
        
        # Structured fact-based prompt
        context = f"""Facts:
- Pages per visitor (last 14 days): {avg_pages_per_visitor:.2f}
- Engagement depth: {engagement_level}
- Baseline expectation: 2-3 pages/visitor for good engagement

Task:
Explain what this visitor behavior pattern indicates about site navigation and content relevance. Recommend specific improvements based ONLY on this metric."""
        
        summary = self._call_llm("Analyze this data.", context)
        
        # Provide fallback if LLM failed
        if not summary or summary.startswith("Analysis error") or summary.startswith("LLM"):
            summary = f"Visitor engagement depth: {avg_pages_per_visitor:.2f} pages per visitor ({engagement_level.lower()} engagement). {'Strong engagement indicates effective navigation' if engagement_level == 'Strong' else 'Improve internal linking and content relevance to increase pages per visit'}."
        
        return Insight(
            title="Website: Visitor Engagement",
            summary=summary,
            metric_basis=f"{avg_pages_per_visitor:.2f} pages/visitor",
            time_range="Last 2 weeks",
            confidence="Medium",
            evidence=["Page view to visitor ratio"],
            recommendation="Add internal linking and CTAs to boost depth."
        )
