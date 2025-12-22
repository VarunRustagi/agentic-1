from datetime import date, timedelta
from typing import List, Dict
import os
import numpy as np
import pandas as pd
from dotenv import load_dotenv
import litellm
from .models import DataStore, Insight, DailyMetric, PostMetric

# Load env and simple setup for LiteLLM
load_dotenv()
litellm.use_litellm_proxy = True 
# Check if keys are present, else might fallback or warn
API_BASE = os.getenv("LITELLM_PROXY_API_BASE")
API_KEY = os.getenv("LITELLM_PROXY_GEMINI_API_KEY")

class AnalysisAgent:
    def __init__(self, store: DataStore):
        self.store = store
        
    def generate_insights(self) -> List[Insight]:
        insights = []
        
        eng_insight = self._analyze_engagement_trend()
        if eng_insight:
            insights.append(eng_insight)
            
        fmt_insight = self._analyze_format_performance()
        if fmt_insight:
            insights.append(fmt_insight)
            
        top_post_insight = self._analyze_top_posts()
        if top_post_insight:
            insights.append(top_post_insight)
            
        return insights

    def _call_llm(self, user_prompt: str, context: str) -> str:
        """Helper to call LiteLLM for plain English synthesis."""
        if not API_BASE or not API_KEY:
             return "LLM unavailable (Missing keys)."
             
        try:
            response = litellm.completion(
                model="gemini-2.5-flash", 
                api_base=API_BASE,
                api_key=API_KEY,
                messages=[
                    {"role": "system", "content": "You are a senior marketing analyst. Generate a concise, 1-sentence strategic insight summary and a brief recommendation based on the data provided."},
                    {"role": "user", "content": f"Context: {context}\n\nTask: {user_prompt}"}
                ],
                max_tokens=150
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"LLM Error: {e}")
            return "Could not generate insight text."

    def _analyze_engagement_trend(self) -> Insight:
        if not self.store.daily_metrics:
            return None
            
        sorted_metrics = sorted(self.store.daily_metrics, key=lambda x: x.date)
        recent_30 = sorted_metrics[-30:]
        prev_30 = sorted_metrics[-60:-30]
        
        if not recent_30:
            return None
            
        avg_eng_recent = np.mean([m.engagement_rate_organic for m in recent_30])
        avg_eng_prev = np.mean([m.engagement_rate_organic for m in prev_30]) if prev_30 else avg_eng_recent
        
        change_pct = ((avg_eng_recent - avg_eng_prev) / avg_eng_prev) * 100 if avg_eng_prev > 0 else 0
        
        # LLM Synthesis
        context = f"Last 30 days Avg Engagement Rate: {avg_eng_recent:.2%}. Previous period: {avg_eng_prev:.2%}. Change: {change_pct:.1f}%."
        llm_out = self._call_llm("Summarize the engagement trend and recommend an action.", context)
        
        # Naive split for demo (Summary vs Recommendation)
        # Ideally we'd ask for JSON from LLM, but keeping it simple for now
        summary = llm_out
        recommendation = "Check recent content strategy."
        if "Recommend" in llm_out:
            parts = llm_out.split("Recommend")
            summary = parts[0].strip()
            recommendation = "Recommend" + parts[1].strip()

        return Insight(
            title="Engagement Rate Trend",
            summary=summary,
            metric_basis=f"Avg Engagement Rate: {avg_eng_recent:.2%}",
            time_range=f"{recent_30[0].date} to {recent_30[-1].date}",
            confidence="High",
            evidence=[f"Daily Metrics Rows {len(self.store.daily_metrics)-30}-{len(self.store.daily_metrics)}"],
            recommendation=recommendation
        )

    def _analyze_format_performance(self) -> Insight:
        if not self.store.posts:
            return None
            
        df = pd.DataFrame([p.dict() for p in self.store.posts])
        if df.empty:
            return None
            
        fmt_stats = df.groupby('format').agg({
            'engagement_rate': 'mean',
            'likes': 'sum',
            'post_id': 'count'
        }).reset_index()
        
        best_fmt = fmt_stats.loc[fmt_stats['engagement_rate'].idxmax()]
        
        context = f"Best format is '{best_fmt['format']}' with {best_fmt['engagement_rate']:.2%} engagement rate. It outperformed others."
        llm_out = self._call_llm("Explain which format performs best and why we should do more of it.", context)

        return Insight(
            title="Best Performing Format",
            summary=llm_out,
            metric_basis=f"Avg Eng. Rate: {best_fmt['engagement_rate']:.2%}",
            time_range="All time",
            confidence="Medium",
            evidence=[f"Aggregated data from {best_fmt['post_id']} posts."],
            recommendation=f"Increase {best_fmt['format']} production frequency."
        )

    def _analyze_top_posts(self) -> Insight:
         if not self.store.posts:
            return None
            
         sorted_posts = sorted(self.store.posts, key=lambda x: x.engagement_rate, reverse=True)
         top_3 = sorted_posts[:3]
         
         evidence = [f"Post {p.post_id} ({p.date})" for p in top_3]
         captions = " | ".join([p.caption for p in top_3])
         
         context = f"Top 3 posts captions: {captions}. They had the highest engagement rates."
         llm_out = self._call_llm("Analyze what themes are resonating based on these top captions.", context)
         
         return Insight(
            title="Top Performing Content",
            summary=llm_out,
            metric_basis=f"Top Eng. Rate: {top_3[0].engagement_rate:.2%}",
            time_range="All time",
            confidence="High",
            evidence=evidence,
            recommendation="Focus on these high-performing themes."
         )
