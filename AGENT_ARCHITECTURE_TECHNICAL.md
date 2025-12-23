# Agent Architecture - Technical Overview

## High-Level Architecture Pattern

We've implemented a **multi-agent system** using **object-oriented design** with clear separation of concerns. Each agent is a Python class with specific responsibilities, orchestrated by a central coordinator.

---

## Core Architecture Principles

### 1. **Class-Based Agent Design**

Each agent is implemented as a **Python class** following a consistent pattern:

```python
class AgentName:
    def __init__(self, dependencies):
        # Initialize with required dependencies
        self.data = dependencies
    
    def execute(self):
        # Main execution method
        # Returns structured results
        pass
    
    def _helper_method(self):
        # Private methods for internal logic
        pass
```

**Key Design Decisions:**
- **Single Responsibility**: Each agent has one clear purpose
- **Dependency Injection**: Agents receive data through constructor, not global state
- **Encapsulation**: Internal logic in private methods (`_method_name`)
- **Consistent Interface**: All agents follow similar patterns for predictability

---

## Agent Types & Structure

### 1. **Orchestrator Agent** (Coordinator Pattern)

```python
class OrchestratorAgent:
    def __init__(self, data_dir: str, status_writer=None):
        self.data_dir = data_dir
        self.results: Dict[str, AgentResult] = {}
        self.store: Optional[DataStore] = None
    
    def execute_all(self) -> Dict[str, Any]:
        # Phase 1: Ingestion
        ingestion_result = self._execute_ingestion()
        
        # Phase 2: Platform Analytics (parallel)
        platform_results = self._execute_platform_agents_parallel()
        
        # Phase 3: Strategy
        strategy_result = self._execute_strategy_agent(platform_results)
        
        return self._build_success_response(...)
```

**Pattern:** **Orchestrator/Coordinator Pattern**
- Manages execution order and dependencies
- Handles parallelization where possible
- Provides error handling and graceful degradation
- Returns structured results with execution metadata

**Key Features:**
- **Dependency Management**: Ensures ingestion completes before analytics
- **Parallel Execution**: Uses `ThreadPoolExecutor` for concurrent platform analysis
- **Error Handling**: Continues execution even if one agent fails
- **Result Tracking**: Tracks status (SUCCESS, FAILED, SKIPPED) for each agent

---

### 2. **Ingestion Agent** (Data Processing Pattern)

```python
class IngestionAgent:
    def __init__(self, data_dir: str, status_writer=None):
        self.data_dir = data_dir
        self.store = DataStore()  # Pydantic model for type safety
    
    def load_linkedin_only(self) -> DataStore:
        self._load_linkedin_data()
        return self.store
    
    def _discover_csv_schema(self, filepath, columns, platform):
        # Uses LLM to understand file structure
        # Returns schema mapping
        pass
```

**Pattern:** **Strategy Pattern + LLM Integration**
- **Dynamic Schema Discovery**: Uses LLM to understand file structures
- **Caching**: Stores schema discovery results to avoid redundant LLM calls
- **Fallback Logic**: Heuristic processing if LLM fails
- **Type Safety**: Returns Pydantic models, not raw dictionaries

**Key Features:**
- **LLM-Powered**: Uses `litellm.completion()` for schema understanding
- **File Format Agnostic**: Works with different CSV/JSON structures
- **Parallel Loading**: Separate methods for each platform (enables parallel execution)
- **Data Transformation**: Converts raw files → typed Pydantic models

---

### 3. **Platform Analytics Agents** (Analysis Pattern)

```python
class LinkedInAnalyticsAgent:
    def __init__(self, store: DataStore, status_writer=None):
        self.metrics = store.linkedin_metrics
    
    def analyze(self) -> list[Insight]:
        insights = []
        insights.append(self._analyze_engagement_trend())
        insights.append(self._analyze_posting_cadence())
        return insights
    
    def _call_llm(self, prompt: str, context: str) -> str:
        # Wrapper around LiteLLM
        response = litellm.completion(...)
        return content
```

**Pattern:** **Template Method Pattern**
- **Consistent Structure**: All platform agents follow same `analyze()` interface
- **LLM Integration**: Each agent has `_call_llm()` helper
- **Data-Driven Analysis**: Combines statistical analysis + LLM insights
- **Type-Safe Output**: Returns `List[Insight]` (Pydantic models)

**Key Features:**
- **Platform-Specific Logic**: Each agent understands its platform's metrics
- **Hybrid Analysis**: Statistical calculations + LLM-generated insights
- **Error Handling**: Fallback summaries if LLM fails
- **Timeout Protection**: 30-second timeout on LLM calls

---

### 4. **Strategy Agent** (Synthesis Pattern)

```python
class StrategyAgent:
    def __init__(self, store: DataStore, platform_insights: dict, status_writer=None):
        self.store = store
        self.platform_insights = platform_insights
    
    def generate_executive_summary(self) -> list[Insight]:
        insights = []
        insights.append(self._analyze_growth_trend())
        insights.append(self._identify_leakage())
        insights.append(self._prioritize_platforms())
        insights.append(self._recommend_strategy())
        return insights
```

**Pattern:** **Facade Pattern**
- **Cross-Platform Synthesis**: Combines insights from multiple platforms
- **Executive Focus**: Answers high-level strategic questions
- **Dependency on Platform Agents**: Requires platform insights to exist

---

## Data Models (Pydantic)

**Why Pydantic?**
- **Type Safety**: Runtime validation ensures data integrity
- **Schema Definition**: Clear contracts between agents
- **Serialization**: Easy JSON conversion for API/UI
- **Documentation**: Models serve as living documentation

```python
class DataStore(BaseModel):
    linkedin_metrics: List[DailyMetric] = []
    instagram_metrics: List[InstagramMetric] = []
    website_metrics: List[WebsiteMetric] = []
    # ... additional data types

class Insight(BaseModel):
    title: str
    summary: str
    metric_basis: str
    time_range: str
    confidence: Literal["High", "Medium", "Low"]
    evidence: List[str]
    recommendation: str
```

**Benefits:**
- **Type Checking**: IDE and runtime validation
- **Data Integrity**: Invalid data rejected at boundaries
- **Clear Contracts**: Agents know exactly what data structure to expect

---

## Execution Flow & Patterns

### 1. **Sequential Execution** (Dependencies)

```python
# Phase 1: Must complete before Phase 2
ingestion_result = self._execute_ingestion()
if ingestion_result.status == AgentStatus.FAILED:
    return self._build_error_response(...)

# Phase 2: Depends on Phase 1
platform_results = self._execute_platform_agents_parallel()
```

**Pattern:** **Pipeline Pattern**
- Clear dependency chain
- Early exit on critical failures
- State passed between phases

---

### 2. **Parallel Execution** (Performance)

```python
with ThreadPoolExecutor(max_workers=3) as executor:
    futures = {
        executor.submit(run_linkedin): "linkedin",
        executor.submit(run_instagram): "instagram",
        executor.submit(run_website): "website"
    }
    
    for future in as_completed(futures):
        platform_key, result = future.result()
        platform_results[platform_key] = result
```

**Pattern:** **Thread Pool Pattern**
- **Concurrent Execution**: Multiple agents run simultaneously
- **Resource Management**: ThreadPoolExecutor handles thread lifecycle
- **Result Aggregation**: `as_completed()` collects results as they finish

**Why This Matters:**
- **Performance**: 3x faster than sequential execution
- **Resource Efficiency**: Reuses threads, not processes
- **Non-Blocking**: One slow agent doesn't block others

---

### 3. **Error Handling** (Resilience)

```python
@dataclass
class AgentResult:
    agent_name: str
    status: AgentStatus  # SUCCESS, FAILED, SKIPPED
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time: float = 0.0
```

**Pattern:** **Result Object Pattern**
- **Structured Errors**: Errors are data, not exceptions
- **Graceful Degradation**: System continues even if one agent fails
- **Observability**: Execution time and status tracked

**Error Handling Strategy:**
- **Try-Catch at Agent Level**: Each agent catches its own exceptions
- **Status Tracking**: Failed agents marked, but execution continues
- **Partial Results**: System returns what it can, even with failures

---

## LLM Integration Pattern

### Consistent LLM Wrapper

```python
def _call_llm(self, prompt: str, context: str) -> str:
    response = litellm.completion(
        model="hackathon-gemini-2.5-pro",
        api_base=API_BASE,
        api_key=API_KEY,
        messages=[
            {"role": "system", "content": "You are a [platform] analyst..."},
            {"role": "user", "content": f"{context}\n\n{prompt}"}
        ],
        max_tokens=500,
        timeout=30
    )
    # Error handling and content extraction
    return content
```

**Pattern:** **Adapter Pattern**
- **Unified Interface**: All agents use same LLM calling pattern
- **Configuration Centralized**: API keys/env vars in one place
- **Error Handling**: Consistent fallback behavior
- **Timeout Protection**: Prevents hanging on slow LLM responses

**LLM Usage Points:**
1. **Schema Discovery** (Ingestion): Understands file structures
2. **Pattern Recognition** (Analytics): Generates insights from data
3. **Strategic Synthesis** (Strategy): Creates executive summaries

---

## Caching Strategy

### Schema Discovery Cache

```python
_SCHEMA_CACHE: Dict[str, Dict[str, Any]] = {}

def _get_file_cache_key(self, filepath: str) -> str:
    # Hash based on file path + modification time
    mtime = os.path.getmtime(filepath)
    key = f"{filepath}:{mtime}"
    return hashlib.md5(key.encode()).hexdigest()
```

**Pattern:** **Cache-Aside Pattern**
- **Key Strategy**: File path + modification time (invalidates on file change)
- **Memory Cache**: In-memory dictionary (fast, but process-scoped)
- **LLM Cost Reduction**: Avoids redundant schema discovery calls

---

## Status & Observability

### Status Writer Pattern

```python
class StreamlitStatusWriter:
    def __init__(self, status_container):
        self.status_container = status_container
        self.messages = []
    
    def write(self, message: str):
        self.messages.append(message)
```

**Pattern:** **Observer Pattern**
- **Decoupled Logging**: Agents don't know about Streamlit
- **Accumulation**: Messages collected during execution
- **Display on Demand**: UI updates when execution completes

---

## Code Organization

### File Structure

```
src/agents/
├── __init__.py              # Package initialization
├── models.py                # Pydantic data models (shared)
├── orchestrator_agent.py    # Orchestration logic
├── ingestion.py             # Data loading agent
├── linkedin_agent.py        # LinkedIn analytics
├── instagram_agent.py       # Instagram analytics
├── website_agent.py          # Website analytics
└── strategy_agent.py        # Cross-platform strategy
```

**Principles:**
- **One Agent Per File**: Clear separation
- **Shared Models**: `models.py` for common data structures
- **No Circular Dependencies**: Clear import hierarchy

---

## Key Design Patterns Summary

| Pattern | Where Used | Purpose |
|---------|-----------|---------|
| **Orchestrator** | `OrchestratorAgent` | Coordinates agent execution |
| **Strategy** | `IngestionAgent` | Dynamic schema discovery |
| **Template Method** | Platform Agents | Consistent analysis structure |
| **Facade** | `StrategyAgent` | Simplifies cross-platform synthesis |
| **Adapter** | `_call_llm()` methods | Unified LLM interface |
| **Result Object** | `AgentResult` | Structured error handling |
| **Thread Pool** | Parallel execution | Concurrent agent execution |
| **Cache-Aside** | Schema discovery | Performance optimization |
| **Observer** | Status writer | Decoupled logging |

---

## Type Safety & Validation

### Pydantic Models

```python
class DailyMetric(BaseModel):
    date: date
    platform: Literal["linkedin"] = "linkedin"
    impressions: int = 0
    clicks: int = 0
    reactions: int = 0
    engagement_rate: float = 0.0
```

**Benefits:**
- **Runtime Validation**: Invalid data rejected
- **IDE Support**: Autocomplete and type hints
- **Documentation**: Models serve as API contracts
- **Serialization**: Easy JSON conversion

---

## Error Handling Strategy

### Three-Tier Error Handling

1. **Agent Level**: Try-catch in each agent method
2. **Orchestrator Level**: Status tracking, graceful degradation
3. **UI Level**: User-friendly error messages

```python
try:
    agent = LinkedInAnalyticsAgent(self.store)
    insights = agent.analyze()
    return AgentResult(status=AgentStatus.SUCCESS, result=insights)
except Exception as e:
    return AgentResult(status=AgentStatus.FAILED, error=str(e))
```

**Philosophy:**
- **Fail Gracefully**: One failure doesn't crash the system
- **Partial Results**: Return what we can
- **Observable**: Errors logged and tracked

---

## Performance Optimizations

1. **Parallel Execution**: Platform agents run concurrently
2. **Schema Caching**: LLM schema discovery cached
3. **Lazy Loading**: Data loaded only when needed
4. **Timeout Protection**: LLM calls don't hang indefinitely

---

## Testing & Maintainability

### Design for Testability

- **Dependency Injection**: Agents receive dependencies, not global state
- **Pure Functions**: Helper methods are testable in isolation
- **Type Safety**: Pydantic catches errors early
- **Clear Interfaces**: Consistent method signatures

---

## Summary: How Agents Are Coded

**In one sentence:** We use **object-oriented Python classes** with **Pydantic models** for type safety, **orchestration patterns** for coordination, **parallel execution** for performance, and **LLM integration** for intelligence - all following **consistent design patterns** for maintainability.

**Key Technical Decisions:**
1. **Class-based architecture** (not functional)
2. **Pydantic for type safety** (not plain dicts)
3. **Orchestrator pattern** (not direct agent-to-agent calls)
4. **ThreadPoolExecutor** (not async/await)
5. **Result objects** (not exceptions for control flow)
6. **LLM adapter pattern** (consistent interface)
7. **Caching strategy** (performance optimization)
