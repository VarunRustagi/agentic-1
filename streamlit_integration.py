"""
Streamlit Integration Layer
Connects multi-agent system to Streamlit dashboard
Agent logic takes precedence - this file adapts agent outputs to UI
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.agents.ingestion import IngestionAgent
from src.agents.linkedin_agent import LinkedInAnalyticsAgent
from src.agents.instagram_agent import InstagramAnalyticsAgent
from src.agents.website_agent import WebsiteAnalyticsAgent
from src.agents.strategy_agent import StrategyAgent
import numpy as np

def load_agent_data():
    """
    Run all agents and return structured data for Streamlit.
    This is the SINGLE SOURCE OF TRUTH - no logic changes, just data provision.
    """
    base_dir = os.path.dirname(__file__)
    
    # 1. Ingest all data
    ingestion = IngestionAgent(base_dir)
    store = ingestion.load_data()
    
    # 2. Run platform-specific agents
    linkedin_agent = LinkedInAnalyticsAgent(store)
    instagram_agent = InstagramAnalyticsAgent(store)
    website_agent = WebsiteAnalyticsAgent(store)
    
    linkedin_insights = linkedin_agent.analyze()
    instagram_insights = instagram_agent.analyze()
    website_insights = website_agent.analyze()
    
    # 3. Run strategy meta-agent
    platform_insights = {
        'LinkedIn': linkedin_insights,
        'Instagram': instagram_insights,
        'Website': website_insights
    }
    
    strategy_agent = StrategyAgent(store, platform_insights)
    executive_insights = strategy_agent.generate_executive_summary()
    
    return {
        'store': store,
        'linkedin': linkedin_insights,
        'instagram': instagram_insights,
        'website': website_insights,
        'executive': executive_insights
    }

def get_kpi_metrics_from_agent(platform_name, agent_data):
    """
    Convert agent data to KPI format for Streamlit.
    ADAPTER FUNCTION - transforms agent output to UI structure.
    """
    platform_key = platform_name.lower()
    store = agent_data['store']
    
    # Get platform-specific metrics
    if platform_key == 'linkedin':
        metrics = store.linkedin_metrics
    elif platform_key == 'instagram':
        metrics = store.instagram_metrics
    elif platform_key == 'website':
        metrics = store.website_metrics
    else:
        return []
    
    if not metrics or len(metrics) < 30:
        return _fallback_kpis(platform_name)
    
    # Calculate real metrics from agent data
    sorted_metrics = sorted(metrics, key=lambda x: x.date)
    recent_30 = sorted_metrics[-30:]
    prev_30 = sorted_metrics[-60:-30] if len(sorted_metrics) >= 60 else recent_30
    
    if platform_key in ['linkedin', 'instagram']:
        # Engagement rate calculation
        avg_eng_recent = np.mean([m.engagement_rate for m in recent_30])
        avg_eng_prev = np.mean([m.engagement_rate for m in prev_30])
        eng_change = ((avg_eng_recent - avg_eng_prev) / avg_eng_prev * 100) if avg_eng_prev > 0 else 0
        
        # Impressions/reach growth
        avg_reach_recent = np.mean([m.impressions for m in recent_30])
        avg_reach_prev = np.mean([m.impressions for m in prev_30])
        reach_change = ((avg_reach_recent - avg_reach_prev) / avg_reach_prev * 100) if avg_reach_prev > 0 else 0
        
        return [
            {
                "label": "Avg Engagement Rate",
                "value": f"{avg_eng_recent:.1%}",
                "trend": f"{eng_change:+.1f}%",
                "trend_direction": "up" if eng_change > 0 else "down",
                "helper": "vs last 30 days"
            },
            {
                "label": "Reach Growth",
                "value": f"{reach_change:+.1f}%",
                "trend": f"{int(avg_reach_recent - avg_reach_prev):+,}",
                "trend_direction": "up" if reach_change > 0 else "down",
                "helper": "impressions"
            },
            {
                "label": "Avg Daily Impressions",
                "value": f"{int(avg_reach_recent):,}",
                "trend": f"{reach_change:+.1f}%",
                "trend_direction": "up" if reach_change > 0 else "down",
                "helper": "last 30 days"
            }
        ]
    
    elif platform_key == 'website':
        # Website-specific metrics
        avg_bounce_recent = np.mean([m.bounce_rate for m in recent_30])
        avg_bounce_prev = np.mean([m.bounce_rate for m in prev_30])
        bounce_change = ((avg_bounce_recent - avg_bounce_prev) * 100)
        
        avg_views_recent = np.mean([m.page_views for m in recent_30])
        avg_views_prev = np.mean([m.page_views for m in prev_30])
        views_change = ((avg_views_recent - avg_views_prev) / avg_views_prev * 100) if avg_views_prev > 0 else 0
        
        avg_visitors_recent = np.mean([m.unique_visitors for m in recent_30])
        
        return [
            {
                "label": "Avg Bounce Rate",
                "value": f"{avg_bounce_recent:.1%}",
                "trend": f"{bounce_change:+.1f}pp",
                "trend_direction": "down" if bounce_change < 0 else "up",  # Lower is better
                "helper": "vs last 30 days"
            },
            {
                "label": "Page Views Growth",
                "value": f"{views_change:+.1f}%",
                "trend": f"{int(avg_views_recent):,}/day",
                "trend_direction": "up" if views_change > 0 else "down",
                "helper": "daily average"
            },
            {
                "label": "Unique Visitors",
                "value": f"{int(avg_visitors_recent):,}",
                "trend": f"+{views_change:.1f}%",
                "trend_direction": "up" if views_change > 0 else "down",
                "helper": "daily average"
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
    """
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
        result.append({
            "title": insight.title,
            "description": insight.summary,
            "confidence": insight.confidence,
            "evidence": insight.evidence,
            "metric_basis": insight.metric_basis,
            "recommendation": insight.recommendation
        })
    
    return result

def get_recommendations_from_agent(platform_name, agent_data):
    """
    Extract recommendations from agent insights.
    """
    platform_key = platform_name.lower()
    insights = agent_data.get(platform_key, [])
    
    if not insights:
        return [{"action": "Upload Data", "description": "No recommendations available", "confidence": "Low"}]
    
    result = []
    for insight in insights:
        result.append({
            "action": insight.recommendation,
            "description": f"Based on: {insight.metric_basis}",
            "confidence": insight.confidence
        })
    
    return result
