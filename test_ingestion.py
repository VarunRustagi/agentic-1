#!/usr/bin/env python3
"""Simple test script to run ingestion and see the results"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.agents.ingestion import IngestionAgent

def main():
    print("="*70)
    print("  INGESTION AGENT TEST")
    print("="*70)
    print()
    
    # Initialize agent with project root
    agent = IngestionAgent(str(project_root))
    
    # Load all data
    print("Starting data ingestion...\n")
    data = agent.load_data()
    
    # Print summary
    print(f"\n{'='*70}")
    print("DATA INGESTION SUMMARY")
    print(f"{'='*70}")
    print(f"  LinkedIn records:  {len(data.linkedin_metrics)}")
    print(f"  Instagram records: {len(data.instagram_metrics)}")
    print(f"  Website records:   {len(data.website_metrics)}")
    print(f"{'='*70}\n")
    
    # Show sample records
    if data.linkedin_metrics:
        print("📊 Sample LinkedIn Record:")
        sample = data.linkedin_metrics[0]
        print(f"   Date: {sample.date}")
        print(f"   Impressions: {sample.impressions:,}")
        print(f"   Clicks: {sample.clicks:,}")
        print(f"   Reactions: {sample.reactions:,}")
        print(f"   Engagement Rate: {sample.engagement_rate:.2%}")
        print()
    
    if data.instagram_metrics:
        print("📸 Sample Instagram Record:")
        sample = data.instagram_metrics[0]
        print(f"   Date: {sample.date}")
        print(f"   Impressions: {sample.impressions:,}")
        print(f"   Likes: {sample.likes:,}")
        print(f"   Comments: {sample.comments:,}")
        print(f"   Shares: {sample.shares:,}")
        print(f"   Engagement Rate: {sample.engagement_rate:.2%}")
        print()
    
    if data.website_metrics:
        print("🌐 Sample Website Record:")
        sample = data.website_metrics[0]
        print(f"   Date: {sample.date}")
        print(f"   Page Views: {sample.page_views:,}")
        print(f"   Unique Visitors: {sample.unique_visitors:,}")
        print(f"   Bounce Rate: {sample.bounce_rate:.2%}")
        print()
    
    # Show date ranges
    if data.linkedin_metrics:
        dates = sorted([m.date for m in data.linkedin_metrics])
        print(f"📅 LinkedIn Date Range: {dates[0]} to {dates[-1]}")
    
    if data.instagram_metrics:
        dates = sorted([m.date for m in data.instagram_metrics])
        print(f"📅 Instagram Date Range: {dates[0]} to {dates[-1]}")
    
    if data.website_metrics:
        dates = sorted([m.date for m in data.website_metrics])
        print(f"📅 Website Date Range: {dates[0]} to {dates[-1]}")
    
    print(f"\n{'='*70}")
    print("✅ Ingestion complete!")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()
