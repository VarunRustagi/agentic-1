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
    
    def __init__(self, store: DataStore, status_writer=None):
        self.metrics = store.instagram_metrics
        self.status_writer = status_writer
        
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
                    {"role": "system", "content": "You are an Instagram marketing analyst. Provide concise, actionable insights."},
                    {"role": "user", "content": f"{context}\n\n{prompt}"}
                ],
                max_tokens=500,
                timeout=30  # 30 second timeout
            )
            
            # Track token usage
            try:
                from .token_tracker import record_llm_call
                record_llm_call("InstagramAnalyticsAgent", "insight_generation", response, "hackathon-gemini-2.5-pro")
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
    
    def _analyze_reach_vs_engagement(self) -> Insight:
        """Analyze if we're reaching new audiences or just engaging existing"""
        total_posts = len(self.metrics)
        if total_posts < 5:  # Need minimum data
            return None
            
        sorted_metrics = sorted(self.metrics, key=lambda x: x.date)
        
        # High reach + low engagement = discovery mode
        # Low reach + high engagement = retention mode
        avg_reach = np.mean([m.impressions for m in sorted_metrics])
        avg_engagement = np.mean([m.engagement_rate for m in sorted_metrics])
        
        reach_growth = (sorted_metrics[-1].impressions - sorted_metrics[0].impressions) / sorted_metrics[0].impressions * 100 if sorted_metrics[0].impressions > 0 else 0
        
        # Structured fact-based prompt
        context = f"""Facts:
- Total posts analyzed: {total_posts}
- Average reach: {avg_reach:.0f} impressions/post
- Average engagement rate: {avg_engagement:.2%}
- Reach trend: {reach_growth:+.1f}%
- Sample size: {'Limited' if total_posts < 20 else 'Sufficient'}

Task:
Explain what this reach vs engagement pattern indicates about audience growth strategy. Base recommendations ONLY on these facts. If sample size is limited, acknowledge uncertainty."""
        
        summary = self._call_llm("Analyze this data.", context)
        
        # Provide fallback if LLM failed
        if not summary or summary.startswith("Analysis error") or summary.startswith("LLM"):
            mode = "discovery mode" if avg_reach > 1000 and avg_engagement < 0.05 else "retention mode" if avg_reach < 500 and avg_engagement > 0.08 else "balanced"
            summary = f"Average reach: {avg_reach:.0f} impressions/post, engagement rate: {avg_engagement:.2%}. Pattern indicates {mode}. {'Focus on expanding reach' if mode == 'retention mode' else 'Strengthen engagement' if mode == 'discovery mode' else 'Maintain balance'}."
        
        # Sample-size-based confidence adjustment
        confidence = "Medium" if total_posts < 20 else "High"
        
        return Insight(
            title="Instagram: Discovery vs. Retention",
            summary=summary,
            metric_basis=f"Engagement rate: {avg_engagement:.2%} ({total_posts} posts)",
            time_range=f"{sorted_metrics[0].date} to {sorted_metrics[-1].date}",
            confidence=confidence,
            evidence=[f"Instagram metrics, {total_posts} posts analyzed"],
            recommendation="Balance viral content with community engagement."
        )
    
    def _analyze_format_performance(self) -> Insight:
        """Analyze Reels vs Posts performance"""
        total_posts = len(self.metrics)
        if total_posts < 5:
            return None
            
        # Infer format from engagement patterns (high engagement likely = Reels)
        sorted_metrics = sorted(self.metrics, key=lambda x: x.date)
        
        high_engagement = [m for m in sorted_metrics if m.engagement_rate > 0.10]
        low_engagement = [m for m in sorted_metrics if m.engagement_rate <= 0.10]
        
        high_avg = np.mean([m.engagement_rate for m in high_engagement]) if high_engagement else 0
        low_avg = np.mean([m.engagement_rate for m in low_engagement]) if low_engagement else 0
        
        # Structured fact-based prompt
        context = f"""Facts:
- Total posts analyzed: {total_posts}
- High-engagement posts: {len(high_engagement)} (avg {high_avg:.2%})
- Lower-engagement posts: {len(low_engagement)} (avg {low_avg:.2%})
- Performance gap: {(high_avg - low_avg):.2%}
- Sample size: {'Limited (< 20 posts)' if total_posts < 20 else 'Sufficient'}

Task:
Recommend content format strategy based ONLY on this engagement data. If sample size is limited, explicitly state the constraint."""
        
        summary = self._call_llm("Analyze this data.", context)
        
        # Provide fallback if LLM failed
        if not summary or summary.startswith("Analysis error") or summary.startswith("LLM"):
            summary = f"High-engagement posts ({len(high_engagement)} posts, avg {high_avg:.2%}) significantly outperform low-engagement posts (avg {low_avg:.2%}). {'Focus on replicating high-engagement content formats' if high_engagement else 'Test different content formats to find what resonates'}."
        
        # Sample-size-based confidence
        confidence = "Low" if total_posts < 10 else "Medium" if total_posts < 20 else "High"
        
        return Insight(
            title="Instagram: Format Strategy",
            summary=summary,
            metric_basis=f"High-engagement: {high_avg:.2%} ({len(high_engagement)} posts)",
            time_range=f"{sorted_metrics[0].date} to {sorted_metrics[-1].date}",
            confidence=confidence,
            evidence=[f"Format inference from {total_posts} posts"],
            recommendation="Increase Reels production to 60%+ of content mix."
        )
