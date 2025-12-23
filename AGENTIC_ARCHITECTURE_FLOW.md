# Agentic Architecture Flow

## Overview
This document describes the complete agentic architecture of "The Insight Room" - a multi-agent system for marketing analytics that uses LLMs to intelligently process, analyze, and generate insights from multi-platform data.

---

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         THE INSIGHT ROOM                                 │
│                    Multi-Agent Analytics System                          │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                           DATA LAYER                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │
│  │  LinkedIn    │  │  Instagram   │  │   Website    │                 │
│  │  CSV Files   │  │  JSON Files  │  │  CSV Files   │                 │
│  │              │  │              │  │              │                 │
│  │ • content    │  │ • posts      │  │ • blog       │                 │
│  │ • followers  │  │ • audience   │  │ • traffic    │                 │
│  │ • visitors   │  │ • interactions│  │ • sessions   │                 │
│  │              │  │ • live_videos│  │              │                 │
│  │              │  │ • profiles   │  │              │                 │
│  └──────────────┘  └──────────────┘  └──────────────┘                 │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR AGENT (Layer 0)                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  OrchestratorAgent                                               │  │
│  │  • Dependency Management                                         │  │
│  │  • Parallel Execution                                            │  │
│  │  • Error Handling & Resilience                                   │  │
│  │  • Execution State Tracking                                      │  │
│  │                                                                  │  │
│  │  Methods:                                                       │  │
│  │  ├─ execute_all()              → Main orchestration entry point  │  │
│  │  ├─ _execute_ingestion()      → Phase 1: Sequential            │  │
│  │  ├─ _execute_platform_agents_parallel() → Phase 2: Parallel    │  │
│  │  └─ _execute_strategy_agent() → Phase 3: Sequential             │  │
│  │                                                                  │  │
│  │  Features:                                                      │  │
│  │  • ThreadPoolExecutor for parallel platform agent execution     │  │
│  │  • Graceful degradation (partial results on failures)          │  │
│  │  • Execution time tracking per agent                            │  │
│  │  • Status tracking (SUCCESS, FAILED, SKIPPED)                  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                              │                                           │
│                              ▼                                           │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    INGESTION AGENT (Layer 1)                    │  │
│  │  ┌────────────────────────────────────────────────────────────┐  │  │
│  │  │  IngestionAgent                                           │  │  │
│  │  │  • LLM-Powered Schema Discovery                          │  │  │
│  │  │  • Dynamic File Processing                                │  │  │
│  │  │  • Data Transformation & Validation                      │  │  │
│  │  │                                                           │  │  │
│  │  │  Methods:                                                │  │  │
│  │  │  ├─ load_data()                                         │  │  │
│  │  │  ├─ _load_linkedin_data()    → Uses LLM to map CSV cols  │  │  │
│  │  │  ├─ _load_instagram_data()   → Uses LLM to parse JSON    │  │  │
│  │  │  └─ _load_website_data()     → Uses LLM to map CSV cols  │  │  │
│  │  │                                                           │  │  │
│  │  │  LLM Functions:                                           │  │  │
│  │  │  ├─ _discover_csv_schema()   → Schema discovery         │  │  │
│  │  │  ├─ _discover_instagram_json_schema() → JSON analysis    │  │  │
│  │  │  └─ _call_llm()              → LiteLLM proxy calls      │  │  │
│  │  └────────────────────────────────────────────────────────────┘  │  │
│  │                              │                                     │  │
│  │                              ▼                                     │  │
│  │  ┌────────────────────────────────────────────────────────────┐  │  │
│  │  │  DataStore (Pydantic Models)                               │  │  │
│  │  │  ├─ linkedin_metrics: List[DailyMetric]                   │  │  │
│  │  │  ├─ instagram_metrics: List[InstagramMetric]              │  │  │
│  │  │  ├─ website_metrics: List[WebsiteMetric]                 │  │  │
│  │  │  ├─ linkedin_followers: List[LinkedInFollowersMetric]    │  │  │
│  │  │  ├─ linkedin_visitors: List[LinkedInVisitorsMetric]       │  │  │
│  │  │  ├─ instagram_audience_insights: List[...]              │  │  │
│  │  │  ├─ instagram_content_interactions: List[...]           │  │  │
│  │  │  ├─ instagram_live_videos: List[InstagramLiveVideo]     │  │  │
│  │  │  └─ instagram_profiles_reached: List[...]              │  │  │
│  │  └────────────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              PLATFORM ANALYTICS AGENTS (Layer 2)                        │
│                    (Executed in PARALLEL by Orchestrator)               │
│                                                                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐      │
│  │ LinkedInAnalytics│  │InstagramAnalytics│  │WebsiteAnalytics  │      │
│  │     Agent        │  │     Agent        │  │     Agent        │      │
│  ├──────────────────┤  ├──────────────────┤  ├──────────────────┤      │
│  │ Input: DataStore │  │ Input: DataStore  │  │ Input: DataStore │      │
│  │                  │  │                  │  │                  │      │
│  │ analyze() →      │  │ analyze() →      │  │ analyze() →      │      │
│  │ List[Insight]    │  │ List[Insight]    │  │ List[Insight]    │      │
│  │                  │  │                  │  │                  │      │
│  │ Methods:         │  │ Methods:         │  │ Methods:         │      │
│  │ • Engagement     │  │ • Reach vs      │  │ • Traffic        │      │
│  │   Trends         │  │   Engagement    │  │   Quality        │      │
│  │ • Posting        │  │ • Format        │  │ • Conversion     │      │
│  │   Cadence        │  │   Performance   │  │   Funnel        │      │
│  │                  │  │                  │  │                  │      │
│  │ Uses LLM for:    │  │ Uses LLM for:    │  │ Uses LLM for:    │      │
│  │ • Pattern        │  │ • Pattern        │  │ • Pattern        │      │
│  │   Recognition    │  │   Recognition    │  │   Recognition    │      │
│  │ • Insight        │  │ • Insight        │  │ • Insight        │      │
│  │   Generation     │  │   Generation     │  │   Generation     │      │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘      │
│         │                      │                      │                   │
│         └──────────────────────┼──────────────────────┘                 │
│                                  ▼                                         │
│                    ┌─────────────────────────────┐                        │
│                    │  Platform Insights Dict    │                        │
│                    │  {                         │                        │
│                    │    'LinkedIn': [Insight],  │                        │
│                    │    'Instagram': [Insight],  │                        │
│                    │    'Website': [Insight]    │                        │
│                    │  }                         │                        │
│                    └─────────────────────────────┘                        │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              STRATEGY AGENT (Layer 3 - Meta-Agent)                       │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  StrategyAgent                                                   │  │
│  │  • Cross-Platform Synthesis                                      │  │
│  │  • Executive-Level Insights                                     │  │
│  │  • Strategic Recommendations                                     │  │
│  │                                                                  │  │
│  │  Input:                                                          │  │
│  │  ├─ DataStore (all metrics)                                     │  │
│  │  └─ Platform Insights Dict                                       │  │
│  │                                                                  │  │
│  │  generate_executive_summary() → List[Insight]                   │  │
│  │                                                                  │  │
│  │  Core Questions Answered:                                       │  │
│  │  1. Are we growing or declining?                                │  │
│  │     → _analyze_growth_trend()                                   │  │
│  │  2. Where is the leakage?                                       │  │
│  │     → _identify_leakage()                                       │  │
│  │  3. Which platforms deserve attention?                          │  │
│  │     → _prioritize_platforms()                                   │  │
│  │  4. What strategic levers should we pull?                      │  │
│  │     → _recommend_strategy()                                     │  │
│  │                                                                  │  │
│  │  Uses LLM for:                                                   │  │
│  │  • Cross-platform correlation analysis                          │  │
│  │  • Strategic synthesis                                           │  │
│  │  • Executive-level recommendations                              │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              REPORT GENERATION AGENTS (Layer 4 - On-Demand)               │
│                                                                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐    │
│  │LinkedInReport    │  │InstagramReport    │  │WebsiteReport     │    │
│  │    Agent         │  │    Agent         │  │    Agent         │    │
│  ├──────────────────┤  ├──────────────────┤  ├──────────────────┤    │
│  │ Input:           │  │ Input:           │  │ Input:           │    │
│  │ • File selection │  │ • File selection │  │ • File selection │    │
│  │ • Report type    │  │ • Report type    │  │ • Report type    │    │
│  │                  │  │                  │  │                  │    │
│  │ generate_report()│  │ generate_report()│  │ generate_report()│    │
│  │ → Dict with:     │  │ → Dict with:     │  │ → Dict with:     │    │
│  │ • Analysis       │  │ • Analysis       │  │ • Analysis       │    │
│  │ • Trends         │  │ • Trends         │  │ • Trends         │    │
│  │ • Recommendations│  │ • Recommendations│  │ • Recommendations│    │
│  │                  │  │                  │  │                  │    │
│  │ Report Types:    │  │ Report Types:    │  │ Report Types:    │    │
│  │ • comprehensive  │  │ • comprehensive  │  │ • comprehensive  │    │
│  │ • trends         │  │ • trends         │  │ • trends         │    │
│  │ • correlations   │  │ • correlations   │  │ • correlations   │    │
│  │ • executive      │  │ • executive      │  │ • executive      │    │
│  │                  │  │                  │  │                  │    │
│  │ Uses LLM for:    │  │ Uses LLM for:    │  │ Uses LLM for:    │    │
│  │ • Data analysis  │  │ • JSON analysis  │  │ • CSV analysis   │    │
│  │ • Pattern finding│  │ • Pattern finding│  │ • Pattern finding│    │
│  │ • Report writing │  │ • Report writing │  │ • Report writing │    │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              Q&A AGENT (Layer 5 - Interactive)                           │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  Ask The Insight Room                                             │  │
│  │  • Natural Language Interface                                     │  │
│  │  • Context-Aware Responses                                        │  │
│  │  • Access to All Ingested Data                                    │  │
│  │                                                                  │  │
│  │  Input:                                                           │  │
│  │  • User question (natural language)                               │  │
│  │  • Full agent_data (store + insights)                            │  │
│  │                                                                  │  │
│  │  ask_insight_room() → str (LLM response)                        │  │
│  │                                                                  │  │
│  │  Context Provided:                                               │  │
│  │  • All platform metrics summaries                                │  │
│  │  • Unmapped data file counts                                      │  │
│  │  • Available insights                                             │  │
│  │  • Executive insights                                             │  │
│  │                                                                  │  │
│  │  Uses LLM for:                                                    │  │
│  │  • Question understanding                                         │  │
│  │  • Data retrieval and synthesis                                   │  │
│  │  • Natural language response generation                           │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              INTEGRATION LAYER                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  streamlit_integration.py                                        │  │
│  │                                                                  │  │
│  │  Functions:                                                      │  │
│  │  ├─ load_agent_data()              → Orchestrates all agents    │  │
│  │  ├─ get_kpi_metrics_from_agent()    → Transforms to UI format    │  │
│  │  ├─ get_insights_from_agent()       → Transforms to UI format    │  │
│  │  ├─ get_recommendations_from_agent()→ Transforms to UI format    │  │
│  │  ├─ generate_linkedin_report()      → Report generation          │  │
│  │  ├─ generate_instagram_report()    → Report generation          │  │
│  │  ├─ generate_website_report()      → Report generation          │  │
│  │  ├─ ask_insight_room()             → Q&A interface              │  │
│  │  ├─ get_engagement_trend_data_from_agent() → Chart data        │  │
│  │  └─ get_supporting_charts_data_from_agent() → Chart data        │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    UI LAYER (Streamlit)                                  │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  demo_app.py                                                     │  │
│  │                                                                  │  │
│  │  Tabs:                                                           │  │
│  │  ├─ Dashboard                                                    │  │
│  │  │  ├─ LinkedIn Tab                                             │  │
│  │  │  ├─ Instagram Tab                                            │  │
│  │  │  └─ Website Tab                                               │  │
│  │  │                                                               │  │
│  │  ├─ Reports                                                      │  │
│  │  │  ├─ LinkedIn Reports Tab                                     │  │
│  │  │  ├─ Instagram Reports Tab                                    │  │
│  │  │  └─ Website Reports Tab                                       │  │
│  │  │                                                               │  │
│  │  └─ Marketing                                                    │  │
│  │     └─ Cross-platform overview                                  │  │
│  │                                                                  │  │
│  │  Features:                                                       │  │
│  │  • KPI Cards (real agent data)                                  │  │
│  │  • Charts (real agent data)                                     │  │
│  │  • Insights Display                                             │  │
│  │  • Recommendations Display                                       │  │
│  │  • Report Generation UI                                          │  │
│  │  • Ask The Insight Room Chat                                     │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Agent Flow Sequence

### 1. Orchestrated Agent Execution Flow

```
User Action: Click "Load Data" Button
    │
    ▼
┌─────────────────────────────────────┐
│  OrchestratorAgent.execute_all()     │
│                                      │
│  Phase 1: Ingestion (Sequential)     │
│  ┌────────────────────────────────┐ │
│  │ _execute_ingestion()           │ │
│  │  └─> IngestionAgent.load_data()│ │
│  │      ├─ _load_linkedin_data()  │ │
│  │      ├─ _load_instagram_data()  │ │
│  │      └─ _load_website_data()   │ │
│  │                                 │ │
│  │  Returns: DataStore             │ │
│  │  Status: SUCCESS or FAILED     │ │
│  └────────────────────────────────┘ │
│         │                            │
│         ▼ (if SUCCESS)               │
│  Phase 2: Platform Agents (PARALLEL)│
│  ┌────────────────────────────────┐ │
│  │ ThreadPoolExecutor (3 workers) │ │
│  │                                 │ │
│  │ Thread 1: LinkedInAnalytics    │ │
│  │ Thread 2: InstagramAnalytics    │ │
│  │ Thread 3: WebsiteAnalytics     │ │
│  │                                 │ │
│  │ All execute simultaneously     │ │
│  │ Wait for all to complete       │ │
│  │                                 │ │
│  │ Returns: Dict of results       │ │
│  │ Status: Per-agent tracking     │ │
│  └────────────────────────────────┘ │
│         │                            │
│         ▼ (if at least 1 SUCCESS)   │
│  Phase 3: Strategy (Sequential)     │
│  ┌────────────────────────────────┐ │
│  │ _execute_strategy_agent()      │ │
│  │  └─> StrategyAgent.generate_  │ │
│  │      executive_summary()       │ │
│  │                                 │ │
│  │  Returns: Executive Insights  │ │
│  │  Status: SUCCESS, FAILED, or   │ │
│  │          SKIPPED (if no data)  │ │
│  └────────────────────────────────┘ │
│                                      │
│  Returns: {                          │
│    'store': DataStore,              │
│    'linkedin': [Insight],           │
│    'instagram': [Insight],          │
│    'website': [Insight],           │
│    'executive': [Insight],          │
│    'execution_summary': {...}       │
│  }                                   │
└─────────────────────────────────────┘
```

### 2. Analytics Flow

```
DataStore (from Ingestion)
    │
    ├─────────────────────────────────┐
    │                                 │
    ▼                                 ▼
┌──────────────┐              ┌──────────────┐
│ LinkedIn     │              │ Instagram    │
│ Analytics    │              │ Analytics    │
│ Agent        │              │ Agent        │
│              │              │              │
│ analyze()    │              │ analyze()    │
│ ├─ Engagement│              │ ├─ Reach vs  │
│ │  Trends    │              │ │  Engagement│
│ └─ Posting   │              │ └─ Format    │
│    Cadence   │              │    Performance│
│              │              │              │
│ → List[Insight]             │ → List[Insight]
└──────────────┘              └──────────────┘
    │                                 │
    └─────────────────┬──────────────┘
                      ▼
            ┌─────────────────────┐
            │ Platform Insights   │
            │ {                   │
            │   'LinkedIn': [...], │
            │   'Instagram': [...],│
            │   'Website': [...]   │
            │ }                    │
            └─────────────────────┘
                      │
                      ▼
            ┌─────────────────────┐
            │ StrategyAgent        │
            │                     │
            │ generate_executive_ │
            │ summary()           │
            │                     │
            │ ├─ Growth Analysis  │
            │ ├─ Leakage ID      │
            │ ├─ Platform Priority│
            │ └─ Strategy Recs   │
            │                     │
            │ → List[Insight]     │
            └─────────────────────┘
```

### 3. Report Generation Flow (On-Demand)

```
User Action: Select files + report type → Click "Generate Report"
    │
    ▼
┌─────────────────────────────────────┐
│  ReportAgent (LinkedIn/Instagram/   │
│              Website)                │
│                                      │
│  generate_report(files, type)       │
│                                      │
│  1. _load_files()                   │
│     ├─ Load selected CSV/JSON files │
│     └─ Return: Dict[str, DataFrame] │
│                                      │
│  2. _generate_data_summary()        │
│     └─ Calculate stats, date ranges │
│                                      │
│  3. _llm_analyze()                  │
│     ├─ _prepare_data_context()      │
│     │  └─ Summarize loaded data     │
│     ├─ _build_*_prompt()            │
│     │  └─ Based on report_type:     │
│     │     • comprehensive           │
│     │     • trends                  │
│     │     • correlations            │
│     │     • executive               │
│     ├─ LLM Call (Gemini 2.5 Pro)    │
│     └─ Returns: Analysis text       │
│                                      │
│  4. _extract_recommendations()       │
│     └─ Parse LLM response for       │
│        actionable items              │
│                                      │
│  Returns: {                          │
│    'files_analyzed': [...],         │
│    'report_type': str,              │
│    'generated_at': str,             │
│    'data_summary': dict,            │
│    'analysis': str,                 │
│    'recommendations': [...]         │
│  }                                   │
└─────────────────────────────────────┘
```

### 4. Q&A Flow (Interactive)

```
User Action: Type question in chat input
    │
    ▼
┌─────────────────────────────────────┐
│  ask_insight_room(question,          │
│                  agent_data)        │
│                                      │
│  1. Validate agent_data exists      │
│                                      │
│  2. Prepare context:                 │
│     ├─ Summarize all metrics         │
│     ├─ Count unmapped data files     │
│     ├─ List available insights       │
│     └─ Include executive insights    │
│                                      │
│  3. Build prompt:                    │
│     ├─ System: "You are an AI       │
│     │          analyst..."          │
│     └─ User: Question + context      │
│                                      │
│  4. LLM Call (Gemini 2.5 Pro)       │
│     └─ Returns: Natural language    │
│        response                      │
│                                      │
│  Returns: str (formatted response)   │
└─────────────────────────────────────┘
```

---

## Agent Responsibilities

### IngestionAgent
- **Purpose**: AI-powered data ingestion with schema discovery
- **Key Feature**: Uses LLMs to understand file structures dynamically
- **Output**: Populated `DataStore` with typed metrics
- **LLM Usage**: Schema discovery, column mapping, date format detection

### Platform Analytics Agents
- **LinkedInAnalyticsAgent**: Engagement trends, posting cadence analysis
- **InstagramAnalyticsAgent**: Reach vs engagement, format performance
- **WebsiteAnalyticsAgent**: Traffic quality, conversion funnel analysis
- **Output**: Platform-specific `Insight` objects
- **LLM Usage**: Pattern recognition, insight generation

### StrategyAgent
- **Purpose**: Cross-platform strategic synthesis
- **Key Feature**: Answers 4 core C-suite questions
- **Input**: DataStore + Platform Insights
- **Output**: Executive-level `Insight` objects
- **LLM Usage**: Cross-platform correlation, strategic synthesis

### Report Agents
- **LinkedInReportAgent**: Detailed LinkedIn analysis reports
- **InstagramReportAgent**: Detailed Instagram analysis reports
- **WebsiteReportAgent**: Detailed Website analysis reports
- **Output**: Comprehensive report dictionaries with analysis
- **LLM Usage**: Data analysis, pattern finding, report writing

### Q&A Agent (Ask The Insight Room)
- **Purpose**: Natural language interface to all data
- **Key Feature**: Context-aware responses using all ingested data
- **Input**: User question + full agent_data
- **Output**: Natural language responses
- **LLM Usage**: Question understanding, data synthesis, response generation

---

## Data Models

### Core Metrics
- **DailyMetric**: LinkedIn daily engagement metrics
- **InstagramMetric**: Instagram post-level metrics
- **WebsiteMetric**: Website daily traffic metrics

### Unmapped Data Models
- **LinkedInFollowersMetric**: Follower growth data
- **LinkedInVisitorsMetric**: Page visitor data
- **InstagramAudienceInsight**: Raw audience insights JSON
- **InstagramContentInteraction**: Raw interactions JSON
- **InstagramLiveVideo**: Raw live videos JSON
- **InstagramProfilesReached**: Raw profiles reached JSON

### Insight Model
- **Insight**: Structured insight with title, summary, confidence, evidence, recommendations

### DataStore
- Central repository for all metrics and unmapped data
- Single source of truth for all agents

---

## LLM Integration

### LLM Provider
- **LiteLLM Proxy**: Unified interface to multiple LLM providers
- **Model**: Gemini 2.5 Pro / Gemini 2.5 Flash
- **Configuration**: Via environment variables
  - `LITELLM_PROXY_API_BASE`
  - `LITELLM_PROXY_GEMINI_API_KEY`

### LLM Usage Patterns

1. **Schema Discovery** (IngestionAgent)
   - Input: File sample + column names
   - Output: JSON schema mapping
   - Purpose: Understand file structure

2. **Pattern Recognition** (Analytics Agents)
   - Input: Metrics data + context
   - Output: Insight objects
   - Purpose: Identify trends and patterns

3. **Strategic Synthesis** (StrategyAgent)
   - Input: Cross-platform data + insights
   - Output: Executive insights
   - Purpose: High-level strategic analysis

4. **Report Generation** (Report Agents)
   - Input: Selected files + data summary
   - Output: Comprehensive analysis text
   - Purpose: Detailed platform analysis

5. **Q&A** (Ask The Insight Room)
   - Input: User question + full data context
   - Output: Natural language response
   - Purpose: Interactive data exploration

---

## Key Design Principles

### 1. Separation of Concerns
- Each agent has a single, well-defined responsibility
- Clear boundaries between data ingestion, analysis, and presentation

### 2. LLM-Powered Intelligence
- LLMs used for understanding, not just processing
- Dynamic schema discovery eliminates hardcoding
- Natural language interfaces for complex queries

### 3. Data Model Flexibility
- Typed models for structured data (Pydantic)
- Raw data storage for unmapped files
- All data accessible to LLMs

### 4. On-Demand Processing
- Report generation only when requested
- Lazy data loading in UI
- Efficient resource usage

### 5. Extensibility
- Easy to add new platforms
- Easy to add new report types
- Easy to add new analysis capabilities

---

## Integration Points

### Streamlit Integration Layer
- **Purpose**: Bridge between agents and UI
- **Functions**: Data transformation, format adaptation
- **No Business Logic**: Pure adapter pattern

### UI Layer
- **Purpose**: User interaction and visualization
- **Features**: Dashboard, Reports, Q&A
- **Data Source**: Always from agents (no synthetic data in production)

---

## Error Handling & Fallbacks

### IngestionAgent
- **LLM Failure**: Falls back to heuristic processing
- **File Errors**: Skips problematic files, continues processing
- **Schema Mismatch**: Stores as unmapped data for LLM access

### Analytics Agents
- **Insufficient Data**: Returns empty insights list
- **LLM Failure**: Returns None for specific insights
- **Calculation Errors**: Graceful degradation

### Report Agents
- **File Not Found**: Returns error in report dict
- **LLM Failure**: Returns error message
- **Empty Data**: Handles gracefully with appropriate messages

### Q&A Agent
- **No Data Loaded**: Clear message to user
- **LLM Failure**: Error message returned
- **Invalid Question**: LLM handles gracefully

---

## Performance Considerations

### Data Ingestion
- Processes files sequentially
- LLM calls batched per file
- Caches schema discoveries (implicitly via processing)

### Analytics
- Runs once per data load
- Results cached in session state
- Platform agents run in parallel (can be optimized)

### Reports
- Generated on-demand
- No caching (fresh analysis each time)
- Can be optimized with caching if needed

### Q&A
- Each question triggers LLM call
- Context prepared fresh each time
- Can be optimized with conversation history

---

## Future Enhancements

### Potential Additions
1. **Caching Layer**: Cache LLM responses for common queries
2. **Agent Orchestration**: Parallel agent execution
3. **Streaming Responses**: Real-time LLM response streaming
4. **Multi-Turn Conversations**: Enhanced Q&A with context
5. **Custom Agent Creation**: User-defined analysis agents
6. **Data Export**: Export insights and reports in various formats
7. **Scheduled Reports**: Automated report generation
8. **Alert System**: Threshold-based alerts and notifications

---

## Summary

This agentic architecture provides:

✅ **Intelligent Data Ingestion**: LLM-powered schema discovery  
✅ **Platform-Specific Analysis**: Specialized agents for each platform  
✅ **Cross-Platform Strategy**: Meta-agent for executive insights  
✅ **On-Demand Reporting**: Detailed analysis reports  
✅ **Interactive Q&A**: Natural language data exploration  
✅ **Extensible Design**: Easy to add new capabilities  
✅ **Type Safety**: Pydantic models ensure data integrity  
✅ **LLM Integration**: Unified LiteLLM proxy interface  

The system is designed to be **intelligent**, **flexible**, and **user-friendly**, with LLMs providing the "intelligence" layer that makes the system truly agentic.
