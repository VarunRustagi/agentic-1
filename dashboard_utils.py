import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# --- Constants ---
COLORS = {
    "primary": "#2563EB",
    "success": "#10B981",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "neutral": "#64748B"
}

# --- Data Generation Functions ---

def get_kpi_metrics(platform="LinkedIn"):
    """Generates the top-row KPI cards data."""
    if platform == "Instagram":
        val_eng, val_trend, val_grow, val_visit = "5.2%", "+1.1%", "+3,400", "12.1k"
    elif platform == "Website":
        val_eng, val_trend, val_grow, val_visit = "2.1%", "-0.4%", "+500", "45.2k"
    else: # LinkedIn
        val_eng, val_trend, val_grow, val_visit = "4.8%", "+0.6%", "+1,250", "8.5k"

    return [
        {
            "label": "Avg Engagement Rate",
            "value": val_eng,
            "trend": val_trend,
            "trend_direction": "up" if "+" in val_trend else "down",
            "helper": "vs last 30 days"
        },
        {
            "label": "Engagement Trend",
            "value": "Rising",
            "trend": "Consistent",
            "trend_direction": "neutral",
            "helper": "last 3 months"
        },
        {
            "label": "Follower Growth",
            "value": val_grow,
            "trend": "+12%",
            "trend_direction": "up",
            "helper": "new followers"
        },
        {
            "label": "Profile Visitors",
            "value": val_visit,
            "trend": "+5%",
            "trend_direction": "up",
            "helper": "unique visits"
        },
        {
            "label": "Posting Consistency",
            "value": "4.2/wk",
            "trend": "-0.2",
            "trend_direction": "down",
            "helper": "posts per week"
        }
    ]

def get_engagement_trend_data(months=6, platform="LinkedIn"):
    """Generates monthly engagement trend data for the main chart."""
    dates = pd.date_range(end=datetime.today(), periods=months, freq='ME')
    
    base = 3000
    if platform == "Instagram": base = 5000
    if platform == "Website": base = 10000

    data = {
        "Month": [d.strftime("%b") for d in dates],
        "Engagement Index": [int(base + x*400 + random.randrange(-500, 500)) for x in range(months)]
    }
    return pd.DataFrame(data)

def get_supporting_charts_data():
    """Generates data for the small right-side charts."""
    # Follower Growth (last 6 months small sparkline equivalent)
    dates = pd.date_range(end=datetime.today(), periods=6, freq='ME')
    df_followers = pd.DataFrame({
        "Month": [d.strftime("%b") for d in dates],
        "Growth": [150, 180, 160, 210, 240, 250]
    })
    
    # Visitor Activity (by day of week, maybe?)
    df_visitors = pd.DataFrame({
        "Day": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "Visits": [800, 950, 1100, 1050, 900, 400, 350]
    })
    
    return df_followers, df_visitors

def get_insights(platform="LinkedIn"):
    """Returns top 3 insights with 'Senior Data Product' quality."""
    
    prefix = f"[{platform}] "
    
    return [
        {
            "title": prefix + "Video content drives 2.5x more engagement",
            "description": "Short-form video posts (<60s) are significantly outperforming static images and text-only posts across all demographics.",
            "confidence": "High",
            "type": "opportunity" 
        },
        {
            "title": prefix + "Competitor 'TechFlow' gaining traction",
            "description": "TechFlow's recent 'AI Ethics' campaign has overlapped with a 15% dip in your share of voice for similar keywords.",
            "confidence": "Medium",
            "type": "warning"
        },
        {
            "title": prefix + "CTO personas engagement is peaking",
            "description": "Interaction from users with 'CTO' or 'VP Engineering' titles has increased by 40% in the last quarter.",
            "confidence": "High",
            "type": "trend"
        }
    ]

def get_recommendations(platform="LinkedIn"):
    """Returns 3 actionable recommendations."""
    return [
        {
            "action": f"Pivot to {platform} Video-First Strategy",
            "description": "Allocate 40% of the content budget to short-form video production for next month to capitalize on the current trend.",
            "confidence": "High"
        },
        {
            "action": "Counter-Campaign on AI Ethics",
            "description": "Publish a whitepaper or thought-leadership series on 'Responsible AI' to reclaim share of voice from TechFlow.",
            "confidence": "Medium"
        },
        {
            "action": "Target Executive Personas",
            "description": "Refine paid ad targeting to specifically focus on the CTO/VP audience segment that is currently highly engaged.",
            "confidence": "High"
        }
    ]

def get_report_summary():
    """Generates a text summary for the executive report."""
    return (
        "## 📑 Executive Summary Report\n\n"
        "**Date:** " + datetime.today().strftime('%Y-%m-%d') + "\n\n"
        "### 1. Overall Performance\n"
        "Across all tracked channels (LinkedIn, Instagram, Website), The Insight Room has seen a **steady increase** in engagement "
        "and visitor traffic. The **Video-First** content strategy is yielding significant results, particularly on Instagram and LinkedIn, "
        "where engagement rates have outperformed benchmarks by **15-20%**.\n\n"
        "### 2. Channel Highlights\n"
        "- **LinkedIn:** Strong growth in the CTO/VP segment. Recommendation: Double down on thought leadership.\n"
        "- **Instagram:** High traction on Reels. Recommendation: Increase posting frequency to daily.\n"
        "- **Website:** Traffic up 12% MoM, largely driven by organic search. Recommendation: optimize landing pages for conversion.\n\n"
        "### 3. Competitive Landscape\n"
        "Competitor 'TechFlow' is aggressively targeting our core keywords. "
        "We recommend an immediate counter-campaign focusing on 'Responsible AI' to maintain market leadership.\n\n"
        "### 4. Next Steps\n"
        "1. Approve the Q3 Video Budget.\n"
        "2. Launch the 'AI Ethics' whitepaper series.\n"
        "3. Review the paid ad strategy for the Executive Persona segment."
    )
