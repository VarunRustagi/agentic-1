"""
Streamlit Integration Layer
Connects multi-agent system to Streamlit dashboard
Agent logic takes precedence - this file adapts agent outputs to UI
"""

import sys
import os
from typing import List
sys.path.insert(0, os.path.dirname(__file__))

from src.agents.ingestion import IngestionAgent
from src.agents.linkedin_agent import LinkedInAnalyticsAgent
from src.agents.instagram_agent import InstagramAnalyticsAgent
from src.agents.website_agent import WebsiteAnalyticsAgent
from src.agents.strategy_agent import StrategyAgent
from src.agents.linkedin_report_agent import LinkedInReportAgent
from src.agents.instagram_report_agent import InstagramReportAgent
from src.agents.website_report_agent import WebsiteReportAgent
import numpy as np
import pandas as pd

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
    print("Store: ", store)
    # Get platform-specific metrics
    if platform_key == 'linkedin':
        metrics = store.linkedin_metrics
    elif platform_key == 'instagram':
        metrics = store.instagram_metrics
    elif platform_key == 'website':
        metrics = store.website_metrics
    else:
        return []
    
    if not metrics or len(metrics) == 0 or len(metrics) < 30:
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
    
    Returns:
        pd.DataFrame with 'Month' and 'Engagement Index' columns, or None if insufficient data
    """
    if not agent_data or 'store' not in agent_data:
        return None
    
    platform_key = platform_name.lower()
    store = agent_data['store']
    
    # Get platform-specific metrics
    if platform_key == 'linkedin':
        metrics = store.linkedin_metrics
        metric_field = 'engagement_rate'
    elif platform_key == 'instagram':
        metrics = store.instagram_metrics
        metric_field = 'engagement_rate'
    elif platform_key == 'website':
        metrics = store.website_metrics
        # For website, use inverse of bounce rate as engagement proxy
        metric_field = 'bounce_rate'
    else:
        return None
    
    if not metrics or len(metrics) < 7:
        return None
    
    # Sort by date
    sorted_metrics = sorted(metrics, key=lambda x: x.date)
    
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
        recent_li = sorted(store.linkedin_metrics, key=lambda x: x.date)[-30:]
        avg_eng = sum(m.engagement_rate for m in recent_li) / len(recent_li) if recent_li else 0
        context_parts.append(f"LinkedIn Metrics: {len(store.linkedin_metrics)} records. Recent avg engagement: {avg_eng:.2%}")
    
    if store.linkedin_followers:
        context_parts.append(f"LinkedIn Followers: {len(store.linkedin_followers)} records")
    
    if store.linkedin_visitors:
        context_parts.append(f"LinkedIn Visitors: {len(store.linkedin_visitors)} records")
    
    # Instagram data summary
    if store.instagram_metrics:
        recent_ig = sorted(store.instagram_metrics, key=lambda x: x.date)[-30:]
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
        recent_web = sorted(store.website_metrics, key=lambda x: x.date)[-30:]
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
            max_tokens=2000
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating response: {str(e)[:200]}"

def get_supporting_charts_data_from_agent(agent_data):
    """
    Extract real supporting chart data from agent store.
    
    Returns:
        Tuple of (df_followers, df_visitors) DataFrames, or None if insufficient data
    """
    if not agent_data or 'store' not in agent_data:
        return None, None
    
    store = agent_data['store']
    
    # Follower Growth - use LinkedIn impressions as proxy (or actual follower data if available)
    linkedin_metrics = store.linkedin_metrics
    if linkedin_metrics and len(linkedin_metrics) >= 6:
        sorted_li = sorted(linkedin_metrics, key=lambda x: x.date)
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
    website_metrics = store.website_metrics
    if website_metrics and len(website_metrics) >= 7:
        sorted_web = sorted(website_metrics, key=lambda x: x.date)
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
