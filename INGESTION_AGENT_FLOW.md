# IngestionAgent Flow Documentation

## Overview
The `IngestionAgent` is an **AI-powered data ingestion system** that uses LLMs to intelligently discover file schemas and extract metrics from multiple data sources. It processes LinkedIn, Website, and Instagram data files dynamically without hardcoded file paths or column names.

---

## High-Level Architecture

```
IngestionAgent
├── Initialization (data_dir)
├── load_data()
│   ├── _load_linkedin_data()    → DailyMetric[]
│   ├── _load_website_data()     → WebsiteMetric[]
│   └── _load_instagram_data()    → InstagramMetric[]
└── Returns: DataStore
```

---

## Detailed Flow

### 1. Initialization

```python
agent = IngestionAgent(data_dir: str)
```

**What happens:**
- Stores the project root directory path
- Creates an empty `DataStore()` object to hold all metrics
- Loads environment variables for LLM API (LITELLM_PROXY_API_BASE, LITELLM_PROXY_GEMINI_API_KEY)

---

### 2. Main Entry Point: `load_data()`

**Flow:**
```
load_data()
  ├─> _load_linkedin_data()
  ├─> _load_website_data()
  └─> _load_instagram_data()
  
Returns: DataStore (populated with all metrics)
```

**Process:**
1. Sequentially loads data from each platform
2. Each platform loader discovers files dynamically
3. Uses LLM for schema discovery (with fallbacks)
4. Extracts and transforms data into typed metric objects
5. Returns populated `DataStore`

---

## 3. LinkedIn Data Loading Flow

### `_load_linkedin_data()`

```
1. Discover Files
   └─> glob.glob("src/data/linkedin/*.csv")
   └─> Found: 3 CSV files (content, followers, visitors)

2. For Each CSV File:
   ├─> Read sample (first 5 rows)
   ├─> Extract column names
   │
   ├─> LLM Schema Discovery
   │   └─> _discover_csv_schema(filepath, columns, "linkedin")
   │       ├─> Build context with file info + sample data
   │       ├─> Call LLM via _call_llm()
   │       └─> Parse JSON response
   │
   ├─> Process File
   │   ├─> If LLM succeeded:
   │   │   └─> _process_linkedin_csv(csv_path, schema_info)
   │   │       ├─> Read full CSV
   │   │       ├─> Map columns using LLM-discovered mappings
   │   │       ├─> Parse dates (with format hints from LLM)
   │   │       ├─> Extract metrics (impressions, clicks, reactions, engagement_rate)
   │   │       └─> Create DailyMetric objects → append to store.linkedin_metrics
   │   │
   │   └─> If LLM failed or file_type != "content":
   │       └─> _process_linkedin_csv_heuristic(csv_path, columns)
   │           ├─> Infer file type from filename
   │           ├─> If "content" → process with hardcoded mappings
   │           └─> If "followers"/"visitors" → skip (not in data model)
   │
   └─> Continue to next file

3. Summary
   └─> Print total LinkedIn records loaded
```

**LLM Schema Discovery for LinkedIn:**
- **Input:** File path, column names, sample data (3 rows)
- **Prompt:** Asks LLM to map columns to DailyMetric fields:
  - `date` → date column
  - `impressions` → impressions column
  - `clicks` → clicks column
  - `reactions` → reactions column
  - `engagement_rate` → engagement rate column
- **Output:** JSON with `file_type`, `date_column`, `date_format`, `mappings`, `extraction_strategy`
- **File Types Handled:**
  - `"content"` → Processed (matches DailyMetric)
  - `"followers"` → Skipped
  - `"visitors"` → Skipped
  - `"other"` → Skipped

---

## 4. Website Data Loading Flow

### `_load_website_data()`

```
1. Discover Files
   └─> glob.glob("src/data/website/*.csv")
   └─> Found: 5 CSV files (blog, traffic reports, sessions, etc.)

2. Initialize Aggregation Dictionary
   └─> daily_metrics = {}  # date -> aggregated metrics

3. For Each CSV File:
   ├─> Read sample (first 5 rows)
   ├─> Extract column names
   │
   ├─> LLM Schema Discovery
   │   └─> _discover_website_csv_schema(filepath, columns)
   │       ├─> Build context with file info + sample data
   │       ├─> Call LLM via _call_llm()
   │       └─> Parse JSON response
   │
   ├─> Process File
   │   ├─> If LLM succeeded:
   │   │   └─> _process_website_csv(csv_path, schema_info, daily_metrics)
   │   │       ├─> Check aggregation_level:
   │   │       │   ├─> "daily" → Extract daily metrics, aggregate by date
   │   │       │   └─> "aggregate" → Distribute totals across date range
   │   │       ├─> Map columns (page_views, unique_visitors, bounce_rate)
   │   │       └─> Update daily_metrics dictionary
   │   │
   │   └─> If LLM failed:
   │       └─> _process_website_csv_heuristic(csv_path, columns, daily_metrics)
   │           ├─> Infer from filename:
   │           │   ├─> "blog"/"post" → daily blog metrics
   │           │   ├─> "traffic" → aggregate traffic report
   │           │   └─> "report"/"session" → time series sessions
   │           └─> Process accordingly
   │
   └─> Continue to next file

4. Convert Aggregated Data
   └─> For each date in daily_metrics:
       └─> Create WebsiteMetric object
           └─> Append to store.website_metrics

5. Summary
   └─> Print total Website records loaded
```

**LLM Schema Discovery for Website:**
- **Input:** File path, column names, sample data
- **Prompt:** Asks LLM to map columns to WebsiteMetric fields:
  - `date` → date column
  - `page_views` → page views column
  - `unique_visitors` → unique visitors column
  - `bounce_rate` → bounce rate column
- **Output:** JSON with `file_type`, `date_column`, `aggregation_level`, `mappings`
- **Aggregation Levels:**
  - `"daily"` → Time-series data, extract per day
  - `"aggregate"` → Total metrics, distribute across date range
  - `"country"` → Geographic data (currently skipped)

---

## 5. Instagram Data Loading Flow

### `_load_instagram_data()`

```
1. Discover Files
   └─> glob.glob("src/data/instagram/*.json")
   └─> Found: 5 JSON files (posts, audience, interactions, live_videos, profiles_reached)

2. For Each JSON File:
   ├─> Load JSON file
   ├─> Extract top-level keys
   │
   ├─> LLM Schema Discovery
   │   └─> _discover_instagram_json_schema(filepath, data)
   │       ├─> Extract sample entry structure
   │       ├─> Build context with file structure
   │       ├─> Call LLM via _call_llm()
   │       └─> Parse JSON response
   │
   ├─> Process File
   │   ├─> If LLM succeeded:
   │   │   └─> _process_instagram_json(data, schema_info)
   │   │       ├─> Get data_key (e.g., "organic_insights_posts")
   │   │       ├─> Extract entries from data[data_key]
   │   │       ├─> For each entry:
   │   │       │   ├─> Extract timestamp using timestamp_path
   │   │       │   ├─> Extract metrics using metric_paths (dot notation)
   │   │       │   ├─> Calculate engagement_rate
   │   │       │   └─> Create InstagramMetric object
   │   │       └─> Append to store.instagram_metrics
   │   │
   │   └─> If LLM failed:
   │       └─> _process_instagram_json_heuristic(data, filename)
   │           ├─> If "posts" in filename:
   │           │   └─> Use hardcoded paths for posts.json structure
   │           └─> Otherwise → skip (aggregate data, not daily metrics)
   │
   └─> Continue to next file

3. Summary
   └─> Print total Instagram records loaded
```

**LLM Schema Discovery for Instagram:**
- **Input:** File path, JSON data structure, sample entry
- **Prompt:** Asks LLM to identify:
  - `data_key` → Top-level key containing data array
  - `timestamp_path` → Dot-notation path to timestamp (e.g., "string_map_data.Creation timestamp.timestamp")
  - `metric_paths` → Dot-notation paths to metrics (impressions, likes, comments, shares)
- **Output:** JSON with `file_type`, `data_key`, `timestamp_path`, `metric_paths`, `extraction_strategy`
- **File Types:**
  - `"posts"` → Processed (daily post metrics)
  - `"audience"` → Skipped (aggregate data)
  - `"interactions"` → Skipped (aggregate data)
  - `"live_videos"` → Skipped (different structure)
  - `"profiles_reached"` → Skipped (aggregate data)

---

## 6. LLM Integration Details

### `_call_llm(prompt, context)`

**Purpose:** Centralized LLM calling with error handling and JSON parsing

**Flow:**
```
1. Check API Configuration
   └─> If API_BASE or API_KEY missing → return None

2. Call LiteLLM API
   ├─> Model: "hackathon-gemini-2.5-pro"
   ├─> System prompt: "You are a data schema expert..."
   ├─> User prompt: context + prompt
   ├─> max_tokens: 2000
   └─> response_format: {"type": "json_object"}

3. Handle Response
   ├─> Check for None/empty response
   ├─> Extract content from response.choices[0].message.content
   ├─> Check finish_reason:
   │   ├─> "length" → Truncated, try to complete JSON
   │   └─> "stop" → Complete response
   │
   ├─> Parse JSON
   │   ├─> Try json.loads()
   │   ├─> If fails → Try to fix (remove trailing commas, extract JSON from text)
   │   └─> Return parsed dict or None
   │
   └─> Print debug info (full response, finish reason, parse status)

4. Error Handling
   └─> If any exception → Print error, return None
```

**JSON Completion for Truncated Responses:**
- `_complete_truncated_json()` method:
  - Counts open/close braces and brackets
  - Removes incomplete string values
  - Closes open structures
  - Attempts to create valid JSON

---

## 7. Helper Methods

### `_parse_date(date_str, format_hint)`
- **Purpose:** Robust date parsing with multiple format attempts
- **Flow:**
  1. Try format_hint first (if provided)
  2. Try common formats: `%d/%m/%Y`, `%m/%d/%Y`, `%Y-%m-%d`, etc.
  3. Try pandas with `dayfirst=True` for ambiguous formats
  4. Return `date` object or `None`

### `_get_nested_value(obj, path, default)`
- **Purpose:** Extract nested JSON values using dot notation
- **Example:** `"string_map_data.Impressions.value"` → extracts nested value
- **Flow:**
  1. Split path by "."
  2. Traverse object using keys
  3. Handle lists with numeric indices
  4. Return value or default

---

## 8. Fallback Mechanisms

### When LLM Fails:
1. **LinkedIn:**
   - Uses filename patterns: "content" → process, "followers"/"visitors" → skip
   - Hardcoded column mappings for content files

2. **Website:**
   - Uses filename patterns: "blog" → daily, "traffic" → aggregate, "report" → sessions
   - Hardcoded column mappings based on file type

3. **Instagram:**
   - Uses filename patterns: "posts" → process with hardcoded paths
   - Other files → skip (aggregate data)

### When File Doesn't Match Data Model:
- LLM returns `file_type: "other"` or specific type (e.g., "followers")
- Processing logic skips these files with clear messages
- System continues processing other files

---

## 9. Data Transformation Pipeline

### Input → Output Flow:

**LinkedIn CSV:**
```
CSV Row → Parse Date → Extract Metrics → DailyMetric → DataStore.linkedin_metrics
```

**Website CSV:**
```
CSV Row → Parse Date → Extract Metrics → Aggregate by Date → WebsiteMetric → DataStore.website_metrics
```

**Instagram JSON:**
```
JSON Entry → Extract Timestamp → Extract Metrics (nested paths) → InstagramMetric → DataStore.instagram_metrics
```

---

## 10. Error Handling & Resilience

### Multi-Layer Error Handling:
1. **File Level:** Try/except around each file processing
2. **Row Level:** Try/except around each row/entry processing
3. **LLM Level:** Try/except with fallback to heuristics
4. **Parsing Level:** Multiple format attempts with graceful failures

### Graceful Degradation:
- LLM unavailable → Uses heuristics
- LLM returns None → Uses heuristics
- LLM returns invalid JSON → Tries to fix, then uses heuristics
- File doesn't match model → Skips with clear message
- Individual row fails → Logs error, continues processing

---

## 11. Output: DataStore

**Final Result:**
```python
DataStore(
    linkedin_metrics: List[DailyMetric],      # Daily content performance
    instagram_metrics: List[InstagramMetric],  # Daily post performance
    website_metrics: List[WebsiteMetric],     # Daily traffic metrics
    competitors: List[str]                     # Competitor list (optional)
)
```

**Each Metric Object Contains:**
- `date`: Date of the metric
- `platform`: Platform identifier
- Platform-specific fields (impressions, clicks, engagement_rate, etc.)

---

## 12. Key Features

✅ **Dynamic File Discovery** - No hardcoded file paths  
✅ **AI-Powered Schema Discovery** - LLM understands file structures  
✅ **Intelligent Column Mapping** - Automatically maps columns to data model  
✅ **Robust Error Handling** - Multiple fallback mechanisms  
✅ **Type-Safe Data Models** - Pydantic models ensure data quality  
✅ **Multi-Format Support** - Handles CSV and JSON files  
✅ **Date Parsing Flexibility** - Handles multiple date formats  
✅ **Aggregation Support** - Handles both daily and aggregate data  
✅ **Nested JSON Extraction** - Uses dot-notation paths for complex structures  
✅ **Debug Visibility** - Prints LLM responses and processing status  

---

## Example Execution Flow

```
1. Initialize: IngestionAgent("/path/to/project")
2. Call: agent.load_data()

3. LinkedIn:
   - Discover 3 CSV files
   - Process content file → 365 DailyMetric records
   - Skip followers/visitors files

4. Website:
   - Discover 5 CSV files
   - Process blog file → daily metrics
   - Process traffic reports → aggregate metrics
   - Aggregate all → 365 WebsiteMetric records

5. Instagram:
   - Discover 5 JSON files
   - Process posts.json → 13 InstagramMetric records
   - Skip other files (aggregate data)

6. Return: DataStore with 365 + 365 + 13 = 743 total metric records
```

---

## Summary

The `IngestionAgent` is a **true AI agent** that:
- Uses LLMs to understand data schemas intelligently
- Adapts to different file structures without hardcoding
- Provides robust fallbacks when AI is unavailable
- Handles multiple data formats and structures
- Transforms raw data into typed, validated metric objects
- Provides clear visibility into its decision-making process

This makes it flexible, maintainable, and capable of handling new data sources without code changes.
