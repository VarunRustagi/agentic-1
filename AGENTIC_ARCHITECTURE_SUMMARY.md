# Agentic Architecture - Quick Reference

## Agent Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERFACE                            │
│              (Streamlit Dashboard)                            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              INTEGRATION LAYER                              │
│         streamlit_integration.py                            │
│  • load_agent_data()                                        │
│  • get_kpi_metrics_from_agent()                             │
│  • generate_*_report()                                      │
│  • ask_insight_room()                                       │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  INGESTION   │   │   ANALYTICS  │   │    REPORTS   │
│    AGENT     │   │   AGENTS     │   │    AGENTS    │
│              │   │              │   │              │
│ • Schema     │   │ • LinkedIn   │   │ • LinkedIn  │
│   Discovery  │   │ • Instagram  │   │ • Instagram  │
│ • Data       │   │ • Website    │   │ • Website    │
│   Loading    │   │              │   │              │
│ • Transform  │   │ → Insights   │   │ → Reports   │
└──────────────┘   └──────────────┘   └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │   STRATEGY   │
                    │    AGENT     │
                    │              │
                    │ → Executive  │
                    │   Insights   │
                    └──────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │   Q&A AGENT  │
                    │              │
                    │ → Answers    │
                    └──────────────┘
```

## Agent Types

| Agent | Purpose | Input | Output | LLM Usage |
|-------|---------|-------|--------|-----------|
| **IngestionAgent** | Data loading | Raw files | DataStore | Schema discovery |
| **LinkedInAnalyticsAgent** | LinkedIn analysis | DataStore | List[Insight] | Pattern recognition |
| **InstagramAnalyticsAgent** | Instagram analysis | DataStore | List[Insight] | Pattern recognition |
| **WebsiteAnalyticsAgent** | Website analysis | DataStore | List[Insight] | Pattern recognition |
| **StrategyAgent** | Cross-platform strategy | DataStore + Insights | List[Insight] | Strategic synthesis |
| **LinkedInReportAgent** | LinkedIn reports | Selected files | Report dict | Data analysis |
| **InstagramReportAgent** | Instagram reports | Selected files | Report dict | Data analysis |
| **WebsiteReportAgent** | Website reports | Selected files | Report dict | Data analysis |
| **Q&A Agent** | Interactive Q&A | Question + Data | Answer text | Question answering |

## Data Flow

```
Raw Files (CSV/JSON)
    ↓
IngestionAgent (LLM Schema Discovery)
    ↓
DataStore (Typed Metrics)
    ↓
    ├─→ Platform Analytics Agents → Platform Insights
    │                                    ↓
    └─→ Strategy Agent ←─────────────────┘
                            ↓
                    Executive Insights
                            ↓
                    UI Display
```

## LLM Integration Points

1. **Schema Discovery** (Ingestion)
   - Understands file structures
   - Maps columns to data models
   - Detects date formats

2. **Pattern Recognition** (Analytics)
   - Identifies trends
   - Finds correlations
   - Generates insights

3. **Strategic Synthesis** (Strategy)
   - Cross-platform analysis
   - Executive recommendations
   - Priority identification

4. **Report Generation** (Reports)
   - Comprehensive analysis
   - Trend identification
   - Actionable recommendations

5. **Question Answering** (Q&A)
   - Natural language understanding
   - Context-aware responses
   - Data synthesis

## Key Features

✅ **AI-Powered**: LLMs provide intelligence at every layer  
✅ **Dynamic**: No hardcoded schemas or file paths  
✅ **Extensible**: Easy to add new agents or capabilities  
✅ **Type-Safe**: Pydantic models ensure data integrity  
✅ **On-Demand**: Reports and Q&A generated when needed  
✅ **Comprehensive**: Handles mapped and unmapped data  
