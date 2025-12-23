"""
Streamlit Integration Layer
Connects multi-agent system to Streamlit dashboard
Agent logic takes precedence - this file adapts agent outputs to UI
"""

import sys
import os
import threading
from typing import List
import hashlib
import json
import re
sys.path.insert(0, os.path.dirname(__file__))

from src.agents.orchestrator_agent import OrchestratorAgent
from src.agents.linkedin_report_agent import LinkedInReportAgent
from src.agents.instagram_report_agent import InstagramReportAgent
from src.agents.website_report_agent import WebsiteReportAgent
import numpy as np
import pandas as pd
from dotenv import load_dotenv
import litellm

# Import streamlit for caching (only when needed)
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    # Create a dummy cache decorator for non-streamlit contexts
    def cache_data(func):
        return func
    st = type('obj', (object,), {'cache_data': lambda f: f})()

def _get_data_hash(agent_data):
    """
    Generate a hash of the data to use as cache key.
    This ensures cache invalidates when data changes.
    """
    if not agent_data or 'store' not in agent_data:
        return "no_data"
    
    store = agent_data['store']
    # Create a simple hash based on record counts and latest dates
    data_signature = {
        'li_count': len(store.linkedin_metrics),
        'ig_count': len(store.instagram_metrics),
        'web_count': len(store.website_metrics),
    }
    
    # Add latest dates for each platform to detect data updates
    if store.linkedin_metrics:
        data_signature['li_latest'] = str(max(m.date for m in store.linkedin_metrics))
    if store.instagram_metrics:
        data_signature['ig_latest'] = str(max(m.date for m in store.instagram_metrics))
    if store.website_metrics:
        data_signature['web_latest'] = str(max(m.date for m in store.website_metrics))
    
    # Create hash from signature
    sig_str = json.dumps(data_signature, sort_keys=True)
    return hashlib.md5(sig_str.encode()).hexdigest()

# Load environment variables for LLM
load_dotenv()
litellm.use_litellm_proxy = True
API_BASE = os.getenv("LITELLM_PROXY_API_BASE")
API_KEY = os.getenv("LITELLM_PROXY_GEMINI_API_KEY")

# Global flag to prevent duplicate ingestion runs
_INGESTION_LOCK = False

class StreamlitStatusWriter:
    """Writes status messages to Streamlit - accumulates messages for display"""
    def __init__(self, status_container):
        self.status_container = status_container
        self.messages = []
        self._is_main_thread = True  # Will be checked on first write
        # Write initial message
        self.write("🚀 Starting data ingestion process...")
    
    def write(self, message: str):
        """Add a message to the log and write to status container (if in main thread)"""
        self.messages.append(message)
        
        # Only try to write to Streamlit if we're in the main thread
        # Worker threads from ThreadPoolExecutor don't have Streamlit context
        current_thread = threading.current_thread()
        is_main_thread = (current_thread.name == 'MainThread' or 
                         isinstance(current_thread, threading._MainThread))
        
        if not is_main_thread:
            # In worker thread - just accumulate, don't try to write to Streamlit
            # This prevents the "missing ScriptRunContext" warning
            return
        
        # In main thread - try to write to status container
        try:
            if hasattr(self.status_container, 'write'):
                # This is a st.status() context manager - write directly
                # Note: Messages written here will appear when the context manager exits
                self.status_container.write(message)
            # Also try to write using st.write if available (for debugging)
            # This won't work during blocking calls but helps with debugging
        except (RuntimeError, AttributeError, Exception) as e:
            # If write fails (e.g., no Streamlit context), just accumulate
            # This is expected in some edge cases
            # Silently fail - messages will be shown in expander after execution
            pass
    
    def display(self):
        """Display all accumulated messages (for compatibility with st.empty())"""
        # If using st.empty(), update the container
        if hasattr(self.status_container, 'container'):
            with self.status_container.container():
                st.markdown("**Processing files and running agents...**")
                st.markdown("---")
                if self.messages:
                    message_text = "\n".join(self.messages)
                    st.text_area(
                        "Progress Log:",
                        value=message_text,
                        height=min(400, max(200, len(self.messages) * 20)),
                        disabled=True,
                        label_visibility="visible"
                    )
    
    def clear(self):
        """Clear all messages"""
        self.messages = []

def load_agent_data(status_writer=None):
    """
    Run all agents using OrchestratorAgent for parallel execution and error handling.
    This is the SINGLE SOURCE OF TRUTH - orchestration handles execution order and dependencies.
    
    Args:
        status_writer: Optional StreamlitStatusWriter to display real-time status updates
    
    Note: This function is NOT thread-safe for concurrent calls. Streamlit's single-threaded
    execution model should prevent this, but we add a guard just in case.
    """
    global _INGESTION_LOCK
    
    # Guard against concurrent calls (shouldn't happen in Streamlit, but safety first)
    if _INGESTION_LOCK:
        if status_writer:
            status_writer.write("⚠️ Ingestion already in progress, skipping duplicate call")
        else:
            print("⚠️ Ingestion already in progress, skipping duplicate call")
        return None
    
    try:
        _INGESTION_LOCK = True
        base_dir = os.path.dirname(__file__)
        
        # Reset token tracker at the start of each run
        try:
            from src.agents.token_tracker import get_tracker
            get_tracker().reset()
        except Exception as e:
            print(f"⚠️ Could not reset token tracker: {e}")
        
        # Use OrchestratorAgent to manage execution
        orchestrator = OrchestratorAgent(base_dir, status_writer=status_writer)
        result = orchestrator.execute_all()
        
        # Return in same format as before (backward compatible)
        return {
            'store': result.get('store'),
            'linkedin': result.get('linkedin', []),
            'instagram': result.get('instagram', []),
            'website': result.get('website', []),
            'executive': result.get('executive', []),
            'execution_summary': result.get('execution_summary', {})  # New: execution metadata
        }
    finally:
        _INGESTION_LOCK = False

def get_kpi_metrics_from_agent(platform_name, agent_data):
    """
    Convert agent data to KPI format for Streamlit.
    ADAPTER FUNCTION - transforms agent output to UI structure.
    Cached to avoid recalculating on every render.
    """
    data_hash = _get_data_hash(agent_data)
    return _get_kpi_metrics_with_hash(platform_name, agent_data, data_hash)

def _get_kpi_metrics_with_hash(platform_name, agent_data, data_hash):
    """Wrapper that uses hash for cache key"""
    # Use hash as cache key, but pass full agent_data to computation
    cache_key = f"kpi_{platform_name}_{data_hash}"
    
    if STREAMLIT_AVAILABLE:
        # Check if we have a cached result
        if not hasattr(st.session_state, '_kpi_cache'):
            st.session_state._kpi_cache = {}
        
        if cache_key in st.session_state._kpi_cache:
            return st.session_state._kpi_cache[cache_key]
        
        # Compute and cache
        result = _get_kpi_metrics_uncached(platform_name, agent_data)
        st.session_state._kpi_cache[cache_key] = result
        return result
    else:
        return _get_kpi_metrics_uncached(platform_name, agent_data)

def _get_sorted_metrics(store, platform_key):
    """
    Get sorted metrics for a platform. This is cached separately to avoid re-sorting.
    """
    cache_key = f"sorted_metrics_{platform_key}"
    
    if STREAMLIT_AVAILABLE:
        if not hasattr(st.session_state, '_sorted_metrics_cache'):
            st.session_state._sorted_metrics_cache = {}
        
        if cache_key in st.session_state._sorted_metrics_cache:
            return st.session_state._sorted_metrics_cache[cache_key]
        
        # Get platform-specific metrics
        if platform_key == 'linkedin':
            metrics = store.linkedin_metrics
        elif platform_key == 'instagram':
            metrics = store.instagram_metrics
        elif platform_key == 'website':
            metrics = store.website_metrics
        else:
            return []
        
        # Sort once and cache
        sorted_metrics = sorted(metrics, key=lambda x: x.date) if metrics else []
        st.session_state._sorted_metrics_cache[cache_key] = sorted_metrics
        return sorted_metrics
    else:
        # Non-streamlit context - no caching
        if platform_key == 'linkedin':
            metrics = store.linkedin_metrics
        elif platform_key == 'instagram':
            metrics = store.instagram_metrics
        elif platform_key == 'website':
            metrics = store.website_metrics
        else:
            return []
        return sorted(metrics, key=lambda x: x.date) if metrics else []

def _get_kpi_metrics_uncached(platform_name, agent_data):
    """Uncached version of KPI metrics calculation"""
    
    platform_key = platform_name.lower()
    store = agent_data['store']
    
    # Get sorted metrics (cached separately)
    sorted_metrics = _get_sorted_metrics(store, platform_key)
    
    # For Instagram, we may have fewer records (posts), so use a lower threshold
    min_records = 7 if platform_key == 'instagram' else 30
    
    if not sorted_metrics or len(sorted_metrics) == 0 or len(sorted_metrics) < min_records:
        return _fallback_kpis(platform_name)
    
    # Use available records (up to 30 for recent, or all if less)
    available_count = len(sorted_metrics)
    recent_count = min(30, available_count)
    recent_30 = sorted_metrics[-recent_count:]
    
    # Previous period: use same number of records if available, otherwise use recent period
    if available_count >= recent_count * 2:
        prev_30 = sorted_metrics[-recent_count*2:-recent_count]
    elif available_count > recent_count:
        # Use remaining records as previous period
        prev_30 = sorted_metrics[:available_count - recent_count]
    else:
        prev_30 = recent_30  # Not enough data for comparison
    
    # Get date ranges for display (both current and previous periods)
    if recent_30:
        recent_start = recent_30[0].date.strftime('%b %d, %Y')
        recent_end = recent_30[-1].date.strftime('%b %d, %Y')
        recent_range = f"{recent_start} - {recent_end}"
    else:
        recent_range = "N/A"
    
    if prev_30 and len(prev_30) > 0 and prev_30 != recent_30:
        prev_start = prev_30[0].date.strftime('%b %d, %Y')
        prev_end = prev_30[-1].date.strftime('%b %d, %Y')
        prev_range = f"{prev_start} - {prev_end}"
        comparison_text = f"Current: {recent_range} | Previous: {prev_range}"
    else:
        comparison_text = f"Period: {recent_range}"
    
    if platform_key in ['linkedin', 'instagram']:
        # Engagement rate calculation
        avg_eng_recent = np.mean([m.engagement_rate for m in recent_30])
        avg_eng_prev = np.mean([m.engagement_rate for m in prev_30]) if prev_30 != recent_30 else avg_eng_recent
        eng_change = ((avg_eng_recent - avg_eng_prev) / avg_eng_prev * 100) if avg_eng_prev > 0 else 0
        
        # Impressions/reach growth
        avg_reach_recent = np.mean([m.impressions for m in recent_30])
        avg_reach_prev = np.mean([m.impressions for m in prev_30]) if prev_30 != recent_30 else avg_reach_recent
        reach_change = ((avg_reach_recent - avg_reach_prev) / avg_reach_prev * 100) if avg_reach_prev > 0 else 0
        
        return [
            {
                "label": "Avg Engagement Rate",
                "value": f"{avg_eng_recent:.1%}",
                "trend": f"{eng_change:+.1f}%",
                "trend_direction": "up" if eng_change > 0 else "down",
                "helper": f"{comparison_text}"
            },
            {
                "label": "Reach Growth",
                "value": f"{reach_change:+.1f}%",
                "trend": f"{int(avg_reach_recent - avg_reach_prev):+,}",
                "trend_direction": "up" if reach_change > 0 else "down",
                "helper": f"impressions | {comparison_text}"
            },
            {
                "label": "Avg Daily Impressions",
                "value": f"{int(avg_reach_recent):,}",
                "trend": f"{reach_change:+.1f}%",
                "trend_direction": "up" if reach_change > 0 else "down",
                "helper": f"{comparison_text}"
            }
        ]
    
    elif platform_key == 'website':
        # Website-specific metrics
        avg_bounce_recent = np.mean([m.bounce_rate for m in recent_30])
        avg_bounce_prev = np.mean([m.bounce_rate for m in prev_30]) if prev_30 != recent_30 else avg_bounce_recent
        bounce_change = ((avg_bounce_recent - avg_bounce_prev) * 100)
        
        avg_views_recent = np.mean([m.page_views for m in recent_30])
        avg_views_prev = np.mean([m.page_views for m in prev_30]) if prev_30 != recent_30 else avg_views_recent
        views_change = ((avg_views_recent - avg_views_prev) / avg_views_prev * 100) if avg_views_prev > 0 else 0
        
        avg_visitors_recent = np.mean([m.unique_visitors for m in recent_30])
        
        return [
            {
                "label": "Avg Bounce Rate",
                "value": f"{avg_bounce_recent:.1%}",
                "trend": f"{bounce_change:+.1f}pp",
                "trend_direction": "down" if bounce_change < 0 else "up",  # Lower is better
                "helper": f"{comparison_text}"
            },
            {
                "label": "Page Views Growth",
                "value": f"{views_change:+.1f}%",
                "trend": f"{int(avg_views_recent):,}/day",
                "trend_direction": "up" if views_change > 0 else "down",
                "helper": f"{comparison_text}"
            },
            {
                "label": "Unique Visitors",
                "value": f"{int(avg_visitors_recent):,}",
                "trend": f"{views_change:+.1f}%",
                "trend_direction": "up" if views_change > 0 else "down",
                "helper": f"{comparison_text}"
            }
        ]

def _fallback_kpis(platform_name):
    """Fallback if no data available"""
    return [
        {
            "label": f"{platform_name} Metrics",
            "value": "No Data",
            "trend": "—",
            "trend_direction": "neutral",
            "helper": "upload data to view"
        }
    ]

def get_insights_from_agent(platform_name, agent_data):
    """
    Convert agent Insight objects to dashboard format.
    Pure adapter - no logic changes.
    Cached to avoid reprocessing on every render.
    """
    data_hash = _get_data_hash(agent_data)
    return _get_insights_with_hash(platform_name, agent_data, data_hash)

def _get_insights_with_hash(platform_name, agent_data, data_hash):
    """Wrapper that uses hash for cache key"""
    cache_key = f"insights_{platform_name}_{data_hash}"
    
    if STREAMLIT_AVAILABLE:
        if not hasattr(st.session_state, '_insights_cache'):
            st.session_state._insights_cache = {}
        
        if cache_key in st.session_state._insights_cache:
            return st.session_state._insights_cache[cache_key]
        
        result = _get_insights_uncached(platform_name, agent_data)
        st.session_state._insights_cache[cache_key] = result
        return result
    else:
        return _get_insights_uncached(platform_name, agent_data)

def _sanitize_html(text: str) -> str:
    """Remove all HTML tags and clean up text"""
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
    text = re.sub(r'\s+', ' ', text)  # Replace multiple whitespace with single space
    text = text.strip()
    # Escape remaining special characters (do this last to avoid double-escaping)
    text = text.replace('&amp;', '&')  # First unescape if already escaped
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    return text

def _get_insights_uncached(platform_name, agent_data):
    """Uncached version of insights transformation"""
    platform_key = platform_name.lower()
    insights = agent_data.get(platform_key, [])
    
    if not insights:
        return [
            {
                "title": f"No {platform_name} Insights Available",
                "description": "Upload data to generate insights",
                "confidence": "Low",
                "evidence": []
            }
        ]
    
    # Convert Insight objects to dashboard format
    result = []
    for insight in insights:
        # Safety checks for None values
        title = insight.title if insight.title else "Insight"
        summary = insight.summary if insight.summary else "No summary available."
        recommendation = insight.recommendation if insight.recommendation else "No recommendation available."
        
        # Remove error messages from summary if present
        if summary.startswith("Analysis error") or summary.startswith("LLM"):
            summary = "Analysis unavailable. Please check LLM configuration."
        
        # Sanitize HTML from all text fields at the source
        title = _sanitize_html(title)
        summary = _sanitize_html(summary)
        recommendation = _sanitize_html(recommendation)
        
        result.append({
            "title": title,
            "description": summary,
            "confidence": insight.confidence if insight.confidence else "Low",
            "evidence": insight.evidence if insight.evidence else [],
            "metric_basis": insight.metric_basis if insight.metric_basis else "N/A",
            "recommendation": recommendation
        })
    
    return result

def get_recommendations_from_agent(platform_name, agent_data):
    """
    Extract recommendations from agent insights.
    Cached to avoid reprocessing on every render.
    """
    data_hash = _get_data_hash(agent_data)
    return _get_recommendations_with_hash(platform_name, agent_data, data_hash)

def _get_recommendations_with_hash(platform_name, agent_data, data_hash):
    """Wrapper that uses hash for cache key"""
    cache_key = f"recommendations_{platform_name}_{data_hash}"
    
    if STREAMLIT_AVAILABLE:
        if not hasattr(st.session_state, '_recommendations_cache'):
            st.session_state._recommendations_cache = {}
        
        if cache_key in st.session_state._recommendations_cache:
            return st.session_state._recommendations_cache[cache_key]
        
        result = _get_recommendations_uncached(platform_name, agent_data)
        st.session_state._recommendations_cache[cache_key] = result
        return result
    else:
        return _get_recommendations_uncached(platform_name, agent_data)

def _get_recommendations_uncached(platform_name, agent_data):
    """Uncached version of recommendations extraction"""
    platform_key = platform_name.lower()
    insights = agent_data.get(platform_key, [])
    
    if not insights:
        return [{"action": "Upload Data", "description": "No recommendations available", "confidence": "Low"}]
    
    result = []
    for insight in insights:
        # Safety checks for None values
        recommendation = insight.recommendation if insight.recommendation else "No recommendation available."
        metric_basis = insight.metric_basis if insight.metric_basis else "N/A"
        
        # Sanitize HTML from recommendation and metric_basis
        recommendation = _sanitize_html(recommendation)
        metric_basis = _sanitize_html(metric_basis)
        
        result.append({
            "action": recommendation,
            "description": f"Based on: {metric_basis}",
            "confidence": insight.confidence if insight.confidence else "Low"
        })
    
    return result

def generate_linkedin_report(files: List[str] = None, report_type: str = "comprehensive"):
    """
    Generate LinkedIn report using LinkedInReportAgent.
    
    Args:
        files: List of file types ['content', 'followers', 'visitors'] or None for all
        report_type: 'comprehensive', 'trends', 'correlations', 'executive'
    
    Returns:
        Dict with report data
    """
    base_dir = os.path.dirname(__file__)
    report_agent = LinkedInReportAgent(base_dir)
    report = report_agent.generate_report(files=files, report_type=report_type)
    return report

def generate_instagram_report(files: List[str] = None, report_type: str = "comprehensive"):
    """
    Generate Instagram report using InstagramReportAgent.
    
    Args:
        files: List of file types ['posts', 'audience_insights', 'content_interactions', 'live_videos', 'profiles_reached'] or None for all
        report_type: 'comprehensive', 'trends', 'correlations', 'executive'
    
    Returns:
        Dict with report data
    """
    base_dir = os.path.dirname(__file__)
    report_agent = InstagramReportAgent(base_dir)
    report = report_agent.generate_report(files=files, report_type=report_type)
    return report

def generate_website_report(files: List[str] = None, report_type: str = "comprehensive"):
    """
    Generate Website report using WebsiteReportAgent.
    
    Args:
        files: List of file types ['blog', 'traffic', 'sessions', 'all'] or None for all
        report_type: 'comprehensive', 'trends', 'correlations', 'executive'
    
    Returns:
        Dict with report data
    """
    base_dir = os.path.dirname(__file__)
    report_agent = WebsiteReportAgent(base_dir)
    report = report_agent.generate_report(files=files, report_type=report_type)
    return report

def get_engagement_trend_data_from_agent(platform_name, agent_data):
    """
    Extract real engagement trend data from agent store for charts.
    Cached to avoid recalculating on every render.
    
    Returns:
        pd.DataFrame with 'Month' and 'Engagement Index' columns, or None if insufficient data
    """
    data_hash = _get_data_hash(agent_data)
    return _get_engagement_trend_with_hash(platform_name, agent_data, data_hash)

def _get_engagement_trend_with_hash(platform_name, agent_data, data_hash):
    """Wrapper that uses hash for cache key"""
    cache_key = f"engagement_trend_{platform_name}_{data_hash}"
    
    if STREAMLIT_AVAILABLE:
        if not hasattr(st.session_state, '_engagement_trend_cache'):
            st.session_state._engagement_trend_cache = {}
        
        if cache_key in st.session_state._engagement_trend_cache:
            return st.session_state._engagement_trend_cache[cache_key]
        
        result = _get_engagement_trend_uncached(platform_name, agent_data)
        st.session_state._engagement_trend_cache[cache_key] = result
        return result
    else:
        return _get_engagement_trend_uncached(platform_name, agent_data)

def _get_engagement_trend_uncached(platform_name, agent_data):
    """Uncached version of engagement trend calculation"""
    if not agent_data or 'store' not in agent_data:
        return None
    
    platform_key = platform_name.lower()
    store = agent_data['store']
    
    # Get sorted metrics (cached separately)
    sorted_metrics = _get_sorted_metrics(store, platform_key)
    
    if not sorted_metrics or len(sorted_metrics) < 7:
        return None
    
    # Determine metric field
    if platform_key == 'linkedin':
        metric_field = 'engagement_rate'
    elif platform_key == 'instagram':
        metric_field = 'engagement_rate'
    elif platform_key == 'website':
        metric_field = 'bounce_rate'  # For website, use inverse of bounce rate as engagement proxy
    else:
        return None
    
    # Group by month
    monthly_data = {}
    for metric in sorted_metrics:
        month_key = metric.date.strftime('%Y-%m')
        if month_key not in monthly_data:
            monthly_data[month_key] = []
        
        if platform_key == 'website':
            # Use (1 - bounce_rate) as engagement proxy for website
            value = 1 - getattr(metric, metric_field)
        else:
            value = getattr(metric, metric_field)
        
        monthly_data[month_key].append(value)
    
    # Calculate monthly averages and scale to index (0-10000 range)
    months = []
    engagement_values = []
    
    for month_key in sorted(monthly_data.keys())[-6:]:  # Last 6 months
        avg = np.mean(monthly_data[month_key])
        # Scale to engagement index (multiply by 10000 for readability)
        index_value = int(avg * 10000)
        # Parse month key (YYYY-MM) and format as month abbreviation
        from datetime import datetime
        month_obj = datetime.strptime(month_key, '%Y-%m')
        months.append(month_obj.strftime('%b'))
        engagement_values.append(index_value)
    
    if len(months) == 0:
        return None
    
    return pd.DataFrame({
        "Month": months,
        "Engagement Index": engagement_values
    })

def ask_insight_room(question: str, agent_data: dict) -> str:
    """
    Answer questions using LLM with access to all ingested data.
    
    Args:
        question: User's question
        agent_data: Full agent data with store and insights
    
    Returns:
        LLM-generated answer
    """
    if not API_BASE or not API_KEY:
        return "LLM unavailable. Cannot answer questions."
    
    if not agent_data or 'store' not in agent_data:
        return "Please load data first using the 'Load Data' button in the sidebar."
    
    store = agent_data['store']
    
    # Prepare comprehensive data context
    context_parts = []
    
    # LinkedIn data summary
    if store.linkedin_metrics:
        sorted_li = _get_sorted_metrics(store, 'linkedin')
        recent_li = sorted_li[-30:] if len(sorted_li) >= 30 else sorted_li
        avg_eng = sum(m.engagement_rate for m in recent_li) / len(recent_li) if recent_li else 0
        context_parts.append(f"LinkedIn Metrics: {len(store.linkedin_metrics)} records. Recent avg engagement: {avg_eng:.2%}")
    
    if store.linkedin_followers:
        context_parts.append(f"LinkedIn Followers: {len(store.linkedin_followers)} records")
    
    if store.linkedin_visitors:
        context_parts.append(f"LinkedIn Visitors: {len(store.linkedin_visitors)} records")
    
    # Instagram data summary
    if store.instagram_metrics:
        sorted_ig = _get_sorted_metrics(store, 'instagram')
        recent_ig = sorted_ig[-30:] if len(sorted_ig) >= 30 else sorted_ig
        avg_eng = sum(m.engagement_rate for m in recent_ig) / len(recent_ig) if recent_ig else 0
        context_parts.append(f"Instagram Metrics: {len(store.instagram_metrics)} records. Recent avg engagement: {avg_eng:.2%}")
    
    if store.instagram_audience_insights:
        context_parts.append(f"Instagram Audience Insights: {len(store.instagram_audience_insights)} files")
    
    if store.instagram_content_interactions:
        context_parts.append(f"Instagram Content Interactions: {len(store.instagram_content_interactions)} files")
    
    if store.instagram_live_videos:
        context_parts.append(f"Instagram Live Videos: {len(store.instagram_live_videos)} files")
    
    if store.instagram_profiles_reached:
        context_parts.append(f"Instagram Profiles Reached: {len(store.instagram_profiles_reached)} files")
    
    # Website data summary
    if store.website_metrics:
        sorted_web = _get_sorted_metrics(store, 'website')
        recent_web = sorted_web[-30:] if len(sorted_web) >= 30 else sorted_web
        avg_bounce = sum(m.bounce_rate for m in recent_web) / len(recent_web) if recent_web else 0
        context_parts.append(f"Website Metrics: {len(store.website_metrics)} records. Recent avg bounce rate: {avg_bounce:.2%}")
    
    # Add insights context
    if agent_data.get('linkedin'):
        context_parts.append(f"LinkedIn Insights: {len(agent_data['linkedin'])} insights available")
    
    if agent_data.get('instagram'):
        context_parts.append(f"Instagram Insights: {len(agent_data['instagram'])} insights available")
    
    if agent_data.get('website'):
        context_parts.append(f"Website Insights: {len(agent_data['website'])} insights available")
    
    if agent_data.get('executive'):
        context_parts.append(f"Executive Insights: {len(agent_data['executive'])} cross-platform insights available")
    
    data_summary = "\n".join(context_parts) if context_parts else "No data loaded"
    
    # Build prompt
    prompt = f"""You are an AI analyst for "The Insight Room" - a marketing analytics dashboard.

Available Data:
{data_summary}

User Question: {question}

Instructions:
- Answer based on the available data and insights
- Be specific and actionable
- Reference actual metrics when possible
- If data is insufficient, explain what additional data would help
- Use a conversational but professional tone
- Format your response in clear markdown with bullet points where helpful

Answer:"""
    
    try:
        response = litellm.completion(
            model="hackathon-gemini-2.5-pro",
            api_base=API_BASE,
            api_key=API_KEY,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful marketing analytics AI assistant. Provide clear, actionable insights based on the data available."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=8000  # Increased from 2000 to allow for complete, detailed answers
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating response: {str(e)[:200]}"

def get_supporting_charts_data_from_agent(agent_data):
    """
    Extract real supporting chart data from agent store.
    Cached to avoid recalculating on every render.
    
    Returns:
        Tuple of (df_followers, df_visitors) DataFrames, or None if insufficient data
    """
    data_hash = _get_data_hash(agent_data)
    return _get_supporting_charts_with_hash(agent_data, data_hash)

def _get_supporting_charts_with_hash(agent_data, data_hash):
    """Wrapper that uses hash for cache key"""
    cache_key = f"supporting_charts_{data_hash}"
    
    if STREAMLIT_AVAILABLE:
        if not hasattr(st.session_state, '_supporting_charts_cache'):
            st.session_state._supporting_charts_cache = {}
        
        if cache_key in st.session_state._supporting_charts_cache:
            return st.session_state._supporting_charts_cache[cache_key]
        
        result = _get_supporting_charts_uncached(agent_data)
        st.session_state._supporting_charts_cache[cache_key] = result
        return result
    else:
        return _get_supporting_charts_uncached(agent_data)

def _get_supporting_charts_uncached(agent_data):
    """Uncached version of supporting charts calculation"""
    if not agent_data or 'store' not in agent_data:
        return None, None
    
    store = agent_data['store']
    
    # Follower Growth - use LinkedIn impressions as proxy (or actual follower data if available)
    # Use cached sorted metrics
    sorted_li = _get_sorted_metrics(store, 'linkedin')
    if sorted_li and len(sorted_li) >= 6:
        # Get last 6 months of data
        monthly_impressions = {}
        for metric in sorted_li[-180:]:  # Last ~6 months
            month_key = metric.date.strftime('%Y-%m')
            if month_key not in monthly_impressions:
                monthly_impressions[month_key] = []
            monthly_impressions[month_key].append(metric.impressions)
        
        months = []
        growth_values = []
        for month_key in sorted(monthly_impressions.keys())[-6:]:
            avg_impressions = np.mean(monthly_impressions[month_key])
            # Parse month key (YYYY-MM) and format as month abbreviation
            from datetime import datetime
            month_obj = datetime.strptime(month_key, '%Y-%m')
            months.append(month_obj.strftime('%b'))
            # Normalize to growth-like values (relative to first month)
            growth_values.append(int(avg_impressions / 10))  # Scale down for chart
        
        df_followers = pd.DataFrame({
            "Month": months,
            "Growth": growth_values
        }) if months else None
    else:
        df_followers = None
    
    # Visitor Activity - use website metrics
    # Use cached sorted metrics
    sorted_web = _get_sorted_metrics(store, 'website')
    if sorted_web and len(sorted_web) >= 7:
        # Group by day of week
        weekday_visits = {0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: []}  # Mon-Sun
        
        for metric in sorted_web[-30:]:  # Last 30 days
            weekday = metric.date.weekday()
            weekday_visits[weekday].append(metric.unique_visitors)
        
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        visits = [int(np.mean(weekday_visits[i])) if weekday_visits[i] else 0 for i in range(7)]
        
        df_visitors = pd.DataFrame({
            "Day": days,
            "Visits": visits
        })
    else:
        df_visitors = None
    
    return df_followers, df_visitors
