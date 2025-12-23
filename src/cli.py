import sys
import os
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.orchestrator_agent import OrchestratorAgent
from src.agents.models import Insight

def print_section_header(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def print_insight(insight: Insight, index: int):
    print(f"\n{index}. {insight.title}")
    print(f"   📊 {insight.summary}")
    print(f"   ├─ Metric: {insight.metric_basis}")
    print(f"   ├─ Period: {insight.time_range}")
    print(f"   ├─ Confidence: {insight.confidence}")
    print(f"   └─ 💡 {insight.recommendation}")

def print_dashboard(executive_insights, platform_insights):
    print_section_header("PERFORMANCE & STRATEGY INTELLIGENCE")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    print_section_header("🎯 EXECUTIVE SUMMARY - C-SUITE INSIGHTS")
    for i, insight in enumerate(executive_insights, 1):
        print_insight(insight, i)
    
    print_section_header("📱 PLATFORM DEEP DIVES")
    
    for platform, insights in platform_insights.items():
        print(f"\n{'─'*70}")
        print(f"  {platform.upper()} ANALYTICS")
        print(f"{'─'*70}")
        for i, insight in enumerate(insights, 1):
            print_insight(insight, i)

def chatbot_loop(executive_insights, platform_insights):
    """Interactive Q&A with context from all agents"""
    print_section_header("💬 INTERACTIVE ANALYST - Ask Me Anything")
    print("Questions you can ask:")
    print("  • Are we growing or declining?")
    print("  • Where is the leakage?")
    print("  • Which platform deserves attention?")
    print("  • What should we do next?")
    print("Type 'exit' to quit\n")
    
    # Combine all insights for context
    all_insights = executive_insights + [i for insights in platform_insights.values() for i in insights]
    
    while True:
        query = input("\nYou: ").strip().lower()
        if query == 'exit':
            break
            
        # Simple keyword matching
        if "grow" in query or "declin" in query:
            relevant = [i for i in all_insights if "Growth" in i.title or "Trend" in i.title]
            if relevant:
                print(f"\nAnalyst: {relevant[0].summary}")
                print(f"Evidence: {relevant[0].evidence}")
            else:
                print("\nAnalyst: Unable to find growth trend data.")
                
        elif "leak" in query or "losing" in query or "bounce" in query:
            relevant = [i for i in all_insights if "Leakage" in i.title or "Quality" in i.title]
            if relevant:
                print(f"\nAnalyst: {relevant[0].summary}")
            else:
                print("\nAnalyst: No leakage analysis available.")
                
        elif "platform" in query or "attention" in query or "priorit" in query:
            relevant = [i for i in all_insights if "Prioritization" in i.title or "Platform" in i.title]
            if relevant:
                print(f"\nAnalyst: {relevant[0].summary}")
                print(f"Recommendation: {relevant[0].recommendation}")
            else:
                print("\nAnalyst: Platform comparison unavailable.")
                
        elif "next" in query or "strategy" in query or "recommend" in query:
            relevant = [i for i in all_insights if "Strategic" in i.title or "Recommendation" in i.title]
            if relevant:
                print(f"\nAnalyst: {relevant[0].summary}")
            else:
                print("\nAnalyst: Strategic recommendations pending.")
                
        elif "linkedin" in query:
            if 'LinkedIn' in platform_insights:
                print(f"\nAnalyst: LinkedIn insights:")
                for insight in platform_insights['LinkedIn']:
                    print(f"  • {insight.title}: {insight.summary}")
            else:
                print("\nAnalyst: LinkedIn data unavailable.")
                
        elif "instagram" in query:
            if 'Instagram' in platform_insights:
                print(f"\nAnalyst: Instagram insights:")
                for insight in platform_insights['Instagram']:
                    print(f"  • {insight.title}: {insight.summary}")
            else:
                print("\nAnalyst: Instagram data unavailable.")
                
        elif "website" in query:
            if 'Website' in platform_insights:
                print(f"\nAnalyst: Website insights:")
                for insight in platform_insights['Website']:
                    print(f"  • {insight.title}: {insight.summary}")
            else:
                print("\nAnalyst: Website data unavailable.")
        else:
            print("\nAnalyst: Try asking about growth, leakage, platforms, or strategy.")

def main():

    # Get the base directory of the project
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Print the header
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║    PERFORMANCE & STRATEGY INTELLIGENCE AGENT                       ║")
    print("║    Multi-Platform Analytics for C-Suite Decision Making            ║")
    print("╚════════════════════════════════════════════════════════════════════╝\n")
    
    # Use OrchestratorAgent for parallel execution and better error handling
    print("🚀 Starting agent orchestration...")
    print("   (Platform agents will run in parallel for faster execution)\n")
    
    orchestrator = OrchestratorAgent(base_dir)
    result = orchestrator.execute_all()
    
    # Extract results
    store = result['store']
    linkedin_insights = result.get('linkedin', [])
    instagram_insights = result.get('instagram', [])
    website_insights = result.get('website', [])
    executive_insights = result.get('executive', [])
    
    # Print execution summary
    exec_summary = result.get('execution_summary', {})
    if exec_summary:
        print("\n📊 Execution Summary:")
        if 'ingestion' in exec_summary:
            ing = exec_summary['ingestion']
            status_icon = "✓" if ing['status'] == 'success' else "✗"
            print(f"  {status_icon} Ingestion: {ing['status']} ({ing.get('execution_time', 0):.2f}s)")
        
        if 'platform_agents' in exec_summary:
            print("  Platform Agents (executed in parallel):")
            for platform, status_info in exec_summary['platform_agents'].items():
                status_icon = "✓" if status_info['status'] == 'success' else "✗"
                print(f"    {status_icon} {platform.capitalize()}: {status_info['status']} ({status_info.get('execution_time', 0):.2f}s)")
                if status_info.get('error'):
                    print(f"      Error: {status_info['error']}")
        
        if 'strategy' in exec_summary:
            strat = exec_summary['strategy']
            status_icon = "✓" if strat['status'] == 'success' else "✗"
            print(f"  {status_icon} Strategy: {strat['status']} ({strat.get('execution_time', 0):.2f}s)")
    
    print(f"\n  ✓ LinkedIn Analysis: {len(linkedin_insights)} insights")
    print(f"  ✓ Instagram Analysis: {len(instagram_insights)} insights")
    print(f"  ✓ Website Analysis: {len(website_insights)} insights")
    print(f"  ✓ Executive Summary: {len(executive_insights)} strategic insights\n")
    
    # Build platform_insights dict for dashboard
    platform_insights = {
        'LinkedIn': linkedin_insights,
        'Instagram': instagram_insights,
        'Website': website_insights
    }
    
    # 4. Display Dashboard
    print_dashboard(executive_insights, platform_insights)
    
    # 5. Interactive Chatbot
    chatbot_loop(executive_insights, platform_insights)

if __name__ == "__main__":
    main()
