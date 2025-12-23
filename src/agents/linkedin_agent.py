import os
import numpy as np
import re
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
    
    def __init__(self, store: DataStore, status_writer=None):
        self.metrics = store.linkedin_metrics
        self.status_writer = status_writer
        
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
                    {"role": "system", "content": "You are a LinkedIn marketing analyst. Provide concise, strategic insights. Do NOT use HTML tags, markdown formatting, or any markup. Use plain text only."},
                    {"role": "user", "content": f"{context}\n\n{prompt}"}
                ],
                max_tokens=500,
                timeout=30  # 30 second timeout
            )
            
            # Track token usage
            try:
                from .token_tracker import record_llm_call
                record_llm_call("LinkedInAnalyticsAgent", "insight_generation", response, "hackathon-gemini-2.5-pro")
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
            
            # Sanitize HTML from LLM response before returning
            content = content.strip() if content else "LLM returned empty content."
            return self._sanitize_html(content)
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
        
        # Structured fact-based prompt
        context = f"""Facts:
- Engagement rate (last 30 days): {recent_efficiency:.2%}
- Previous 30-day engagement rate: {prev_efficiency:.2%}
- Change: {change_pct:+.1f}%
- Trend: {'Improving' if change_pct > 0 else 'Declining' if change_pct < 0 else 'Stable'}

Task:
Explain the implications of this engagement trend and provide 1-2 actionable recommendations based ONLY on these facts. Be concise and specific."""
        
        summary = self._call_llm("Analyze this data.", context)
        
        # Provide fallback if LLM failed
        if not summary or summary.startswith("Analysis error") or summary.startswith("LLM"):
            summary = f"Engagement efficiency is {recent_efficiency:.2%} (reactions per impression). {'Improving' if change_pct > 0 else 'Declining' if change_pct < 0 else 'Stable'} trend ({change_pct:+.1f}% change). Focus on content quality and optimal posting times."
        
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
        
        # Calculate variance in activity levels
        impressions_variance = np.std([imp for imp, _ in weekly_buckets])
        avg_impressions = np.mean([imp for imp, _ in weekly_buckets])
        variance_pct = (impressions_variance / avg_impressions * 100) if avg_impressions > 0 else 0
        
        # Structured fact-based prompt
        context = f"""Facts:
- Weeks analyzed: {len(weekly_buckets)}
- Average weekly impressions: {avg_impressions:,.0f}
- Posting consistency variance: {variance_pct:.1f}%
- Consistency level: {'Low (High variance)' if variance_pct > 30 else 'Moderate' if variance_pct > 15 else 'High (Consistent)'}

Task:
Explain what this posting cadence pattern means for engagement performance and recommend optimal posting frequency based ONLY on these facts. Be specific."""
        
        summary = self._call_llm("Analyze this data.", context)
        
        # Provide fallback if LLM failed
        if not summary or summary.startswith("Analysis error") or summary.startswith("LLM"):
            consistency_level = 'Low (High variance)' if variance_pct > 30 else 'Moderate' if variance_pct > 15 else 'High (Consistent)'
            summary = f"Posting cadence shows {consistency_level.lower()} consistency ({variance_pct:.1f}% variance). Average weekly impressions: {avg_impressions:,.0f}. Consistent posting frequency typically improves engagement."
        
        return Insight(
            title="LinkedIn: Posting Cadence Analysis",
            summary=summary,
            metric_basis=f"{len(weekly_buckets)} weeks analyzed",
            time_range="Last quarter",
            confidence="Medium",
            evidence=[f"Weekly engagement aggregation"],
            recommendation="Test 3-4 posts per week vs. daily posting."
        )

