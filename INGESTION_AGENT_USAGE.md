# IngestionAgent Usage in Application

## Where IngestionAgent is Called

### 1. **Streamlit Dashboard** (`streamlit_integration.py`)

**Location:** `streamlit_integration.py` → `load_agent_data()`

```python
# Line 26-27
ingestion = IngestionAgent(base_dir)
store = ingestion.load_data()
```

**Flow:**
```
demo_app.py
  └─> init_agents() [cached]
      └─> agent_integration.load_agent_data()
          └─> IngestionAgent(base_dir).load_data()
              └─> Returns: DataStore
```

**Usage in Dashboard:**
- **KPI Metrics:** `get_kpi_metrics_from_agent()` extracts metrics from `store.linkedin_metrics`, `store.instagram_metrics`, `store.website_metrics`
- **Sidebar Display:** Shows record counts for each platform
- **Insights:** Platform agents use the store to generate insights

---

### 2. **CLI Application** (`src/cli.py`)

**Location:** `src/cli.py` → `main()`

```python
# Line 132-133
ingestion = IngestionAgent(base_dir)
store = ingestion.load_data()
```

**Flow:**
```
python src/cli.py
  └─> main()
      └─> IngestionAgent(base_dir).load_data()
          └─> Returns: DataStore
      └─> Pass store to platform agents
      └─> Display insights in terminal
```

---

### 3. **Test Script** (`test_ingestion.py`)

**Location:** Standalone test file

```python
# Line 21-22
agent = IngestionAgent(str(project_root))
data = agent.load_data()
```

**Purpose:** Testing and debugging ingestion process

---

## Current Results Extracted from IngestionAgent

### Return Value: `DataStore` Object

```python
DataStore(
    linkedin_metrics: List[DailyMetric],      # Currently: ~365 records
    instagram_metrics: List[InstagramMetric],  # Currently: ~13 records
    website_metrics: List[WebsiteMetric],      # Currently: ~365 records
    competitors: List[str]                      # Currently: Not loaded (commented out)
)
```

---

## Detailed Data Extraction

### 1. **LinkedIn Metrics** (`store.linkedin_metrics`)

**Source Files:**
- `src/data/linkedin/shorthills-ai_content_1766385907708 1.csv` ✅ Processed
- `src/data/linkedin/shorthills-ai_followers_1766385928211 1.csv` ⏭️ Skipped (not in data model)
- `src/data/linkedin/shorthills-ai_visitors_1766385917155 1.csv` ⏭️ Skipped (not in data model)

**Current Result:**
- **~365 DailyMetric records**
- **Date Range:** 2024-12-21 to 2025-12-20
- **Fields Extracted:**
  ```python
  DailyMetric(
      date: date,                    # e.g., 2024-12-21
      platform: "linkedin",
      impressions: int,              # e.g., 593
      clicks: int,                   # e.g., 163
      reactions: int,                # e.g., 3
      engagement_rate: float         # e.g., 0.2799 (27.99%)
  )
  ```

**How It's Used:**
- **KPI Calculation:** Average engagement rate, reach growth, daily impressions
- **Trend Analysis:** Compare last 30 days vs previous 30 days
- **LinkedIn Agent:** Generates insights about engagement trends and posting cadence

---

### 2. **Instagram Metrics** (`store.instagram_metrics`)

**Source Files:**
- `src/data/instagram/posts.json` ✅ Processed
- `src/data/instagram/audience_insights.json` ⏭️ Skipped (aggregate data)
- `src/data/instagram/content_interactions.json` ⏭️ Skipped (aggregate data)
- `src/data/instagram/live_videos.json` ⏭️ Skipped (different structure)
- `src/data/instagram/profiles_reached.json` ⏭️ Skipped (aggregate data)

**Current Result:**
- **~13 InstagramMetric records**
- **Date Range:** 2025-09-19 to 2025-11-27
- **Fields Extracted:**
  ```python
  InstagramMetric(
      date: date,                    # e.g., 2025-11-27
      platform: "instagram",
      impressions: int,              # e.g., 60
      likes: int,                    # e.g., 3
      comments: int,                 # e.g., 0
      shares: int,                   # e.g., 0
      engagement_rate: float         # e.g., 0.05 (5.00%)
  )
  ```

**How It's Used:**
- **KPI Calculation:** Average engagement rate, reach growth, daily impressions
- **Trend Analysis:** Compare last 30 days vs previous 30 days
- **Instagram Agent:** Generates insights about reach vs engagement and format performance

---

### 3. **Website Metrics** (`store.website_metrics`)

**Source Files:**
- `src/data/website/blog_table_api_2024-12-23-2025-12-23 1.csv` ✅ Processed (daily blog metrics)
- `src/data/website/Traffic report_2024-12-23-2025-12-23 1.csv` ✅ Processed (aggregate traffic)
- `src/data/website/Traffic report_2024-12-23-2025-12-23 (1) 1.csv` ✅ Processed
- `src/data/website/report-name_2024-12-23_2025-12-22 1.csv` ✅ Processed (sessions)
- `src/data/website/report-name_2024-12-23_2025-12-22 (1) 1.csv` ⚠️ May be processed or skipped

**Current Result:**
- **~365 WebsiteMetric records**
- **Date Range:** 2024-12-23 to 2025-12-22
- **Fields Extracted:**
  ```python
  WebsiteMetric(
      date: date,                    # e.g., 2025-12-21
      platform: "website",
      page_views: int,               # e.g., 13
      unique_visitors: int,           # e.g., 10
      bounce_rate: float              # e.g., 0.50 (50.00%)
  )
  ```

**How It's Used:**
- **KPI Calculation:** Average bounce rate, page views growth, unique visitors
- **Trend Analysis:** Compare last 30 days vs previous 30 days
- **Website Agent:** Generates insights about traffic quality and conversion funnel

---

## Data Flow Through Application

### Streamlit Dashboard Flow:

```
1. User opens demo_app.py
   │
2. init_agents() [cached] called
   │
3. agent_integration.load_agent_data()
   │
4. IngestionAgent.load_data()
   │   ├─> Discovers all CSV/JSON files
   │   ├─> Uses LLM to understand schemas
   │   ├─> Extracts metrics from files
   │   └─> Returns: DataStore
   │
5. Platform Agents initialized with store
   │   ├─> LinkedInAnalyticsAgent(store)
   │   ├─> InstagramAnalyticsAgent(store)
   │   └─> WebsiteAnalyticsAgent(store)
   │
6. Platform Agents generate insights
   │
7. StrategyAgent synthesizes executive insights
   │
8. Return to demo_app.py:
   {
       'store': DataStore,           # Raw metrics
       'linkedin': [Insight, ...],   # LinkedIn insights
       'instagram': [Insight, ...],  # Instagram insights
       'website': [Insight, ...],    # Website insights
       'executive': [Insight, ...]   # C-suite insights
   }
   │
9. Dashboard uses data:
   ├─> Sidebar: Shows record counts from store
   ├─> KPI Cards: Calculated from store.metrics
   ├─> Insights: Displayed from platform insights
   └─> Charts: Generated from store.metrics
```

---

## Current Extraction Statistics

Based on test runs:

| Platform | Records | Date Range | Source Files Processed |
|----------|---------|------------|----------------------|
| **LinkedIn** | ~365 | 2024-12-21 to 2025-12-20 | 1 of 3 (content file only) |
| **Instagram** | ~13 | 2025-09-19 to 2025-11-27 | 1 of 5 (posts.json only) |
| **Website** | ~365 | 2024-12-23 to 2025-12-22 | 4-5 of 5 (multiple files aggregated) |

**Total:** ~743 metric records across all platforms

---

## How Results Are Used in UI

### 1. **Sidebar Display** (`demo_app.py` lines 248-256)

```python
if agent_data and agent_data.get('store'):
    store = agent_data['store']
    n_li = len(store.linkedin_metrics)    # Shows: "● LinkedIn Agent (365 records)"
    n_ig = len(store.instagram_metrics)   # Shows: "● Instagram Agent (13 records)"
    n_web = len(store.website_metrics)    # Shows: "● Website Agent (365 records)"
```

### 2. **KPI Cards** (`streamlit_integration.py` lines 56-151)

**LinkedIn/Instagram KPIs:**
- Avg Engagement Rate (calculated from `engagement_rate` field)
- Reach Growth (calculated from `impressions` field)
- Avg Daily Impressions (calculated from `impressions` field)

**Website KPIs:**
- Avg Bounce Rate (calculated from `bounce_rate` field)
- Page Views Growth (calculated from `page_views` field)
- Unique Visitors (calculated from `unique_visitors` field)

### 3. **Platform Agents** (Pass store to agents)

```python
linkedin_agent = LinkedInAnalyticsAgent(store)      # Uses store.linkedin_metrics
instagram_agent = InstagramAnalyticsAgent(store)   # Uses store.instagram_metrics
website_agent = WebsiteAnalyticsAgent(store)       # Uses store.website_metrics
```

### 4. **Strategy Agent** (Cross-platform analysis)

```python
strategy_agent = StrategyAgent(store, platform_insights)
# Uses all three metric lists for cross-platform analysis
```

---

## Key Points

✅ **IngestionAgent is the single source of truth** for raw data  
✅ **DataStore is passed to all analytics agents** for processing  
✅ **Metrics are type-safe** (Pydantic models ensure data quality)  
✅ **Dynamic file discovery** means new files are automatically processed  
✅ **LLM-powered schema discovery** adapts to different file structures  
✅ **Fallback mechanisms** ensure data loads even if LLM fails  

---

## Summary

**IngestionAgent is called in:**
1. `streamlit_integration.py` → `load_agent_data()` (for Streamlit dashboard)
2. `src/cli.py` → `main()` (for CLI application)
3. `test_ingestion.py` (for testing)

**Current results:**
- **365 LinkedIn records** (daily content metrics)
- **13 Instagram records** (post-level metrics)
- **365 Website records** (daily traffic metrics)

**These results are used for:**
- KPI calculations in dashboard
- Platform-specific insights generation
- Cross-platform strategy analysis
- Data visualization and charts
