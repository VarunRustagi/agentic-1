"""
Token and Cost Tracking for LLM Calls
Tracks token usage and calculates costs across all agentic calls
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import threading
import litellm

@dataclass
class LLMCallMetrics:
    """Metrics for a single LLM call"""
    agent_name: str
    call_type: str  # e.g., "schema_discovery", "insight_generation", "strategy"
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    model: str = ""

@dataclass
class TokenUsageSummary:
    """Summary of token usage across all agents"""
    total_calls: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    calls_by_agent: Dict[str, int] = field(default_factory=dict)
    tokens_by_agent: Dict[str, int] = field(default_factory=dict)
    cost_by_agent: Dict[str, float] = field(default_factory=dict)

class TokenTracker:
    """
    Thread-safe token and cost tracker for LLM calls
    Uses LiteLLM's built-in cost calculation for accuracy
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        self._calls: List[LLMCallMetrics] = []
    
    def record_call(self, agent_name: str, call_type: str, response, model: str = "hackathon-gemini-2.5-pro"):
        """
        Record token usage from an LLM response
        
        Args:
            agent_name: Name of the agent making the call
            call_type: Type of call (e.g., "schema_discovery", "insight_generation")
            response: LiteLLM response object
            model: Model name used
        """
        try:
            # Extract usage information from response
            usage = getattr(response, 'usage', None)
            if not usage:
                return
            
            prompt_tokens = getattr(usage, 'prompt_tokens', 0) or 0
            completion_tokens = getattr(usage, 'completion_tokens', 0) or 0
            total_tokens = getattr(usage, 'total_tokens', 0) or (prompt_tokens + completion_tokens)
            
            # Use LiteLLM's built-in cost calculation for accuracy
            try:
                cost = litellm.completion_cost(completion_response=response, model=model)
            except Exception:
                # Fallback to manual calculation if LiteLLM cost calculation fails
                # Default pricing estimates (adjust based on your actual pricing)
                pricing = {
                    "input": 0.50 / 1_000_000,   # $0.50 per 1M input tokens
                    "output": 1.50 / 1_000_000,  # $1.50 per 1M output tokens
                }
                cost = (prompt_tokens * pricing["input"]) + (completion_tokens * pricing["output"])
            
            # Create metrics
            metrics = LLMCallMetrics(
                agent_name=agent_name,
                call_type=call_type,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost=cost,
                model=model
            )
            
            # Thread-safe append
            with self._lock:
                self._calls.append(metrics)
                
        except Exception as e:
            print(f"⚠️ Error recording token usage: {e}")
    
    def get_summary(self) -> TokenUsageSummary:
        """Get summary of all token usage"""
        with self._lock:
            if not self._calls:
                return TokenUsageSummary()
            
            summary = TokenUsageSummary()
            summary.total_calls = len(self._calls)
            
            for call in self._calls:
                summary.total_prompt_tokens += call.prompt_tokens
                summary.total_completion_tokens += call.completion_tokens
                summary.total_tokens += call.total_tokens
                summary.total_cost += call.cost
                
                # Aggregate by agent
                if call.agent_name not in summary.calls_by_agent:
                    summary.calls_by_agent[call.agent_name] = 0
                    summary.tokens_by_agent[call.agent_name] = 0
                    summary.cost_by_agent[call.agent_name] = 0.0
                
                summary.calls_by_agent[call.agent_name] += 1
                summary.tokens_by_agent[call.agent_name] += call.total_tokens
                summary.cost_by_agent[call.agent_name] += call.cost
            
            return summary
    
    def get_calls_by_agent(self, agent_name: str) -> List[LLMCallMetrics]:
        """Get all calls for a specific agent"""
        with self._lock:
            return [call for call in self._calls if call.agent_name == agent_name]
    
    def get_detailed_breakdown(self) -> List[Dict]:
        """Get detailed breakdown of all calls"""
        with self._lock:
            return [
                {
                    "agent": call.agent_name,
                    "type": call.call_type,
                    "model": call.model,
                    "prompt_tokens": call.prompt_tokens,
                    "completion_tokens": call.completion_tokens,
                    "total_tokens": call.total_tokens,
                    "cost": call.cost,
                    "timestamp": call.timestamp.isoformat()
                }
                for call in self._calls
            ]
    
    def reset(self):
        """Reset all tracking data"""
        with self._lock:
            self._calls.clear()
    
    def export_to_dict(self) -> Dict:
        """Export tracking data as dictionary"""
        summary = self.get_summary()
        return {
            "summary": {
                "total_calls": summary.total_calls,
                "total_prompt_tokens": summary.total_prompt_tokens,
                "total_completion_tokens": summary.total_completion_tokens,
                "total_tokens": summary.total_tokens,
                "total_cost": summary.total_cost,
                "calls_by_agent": summary.calls_by_agent,
                "tokens_by_agent": summary.tokens_by_agent,
                "cost_by_agent": summary.cost_by_agent,
            },
            "detailed_calls": self.get_detailed_breakdown()
        }

# Global tracker instance
_global_tracker = TokenTracker()

def get_tracker() -> TokenTracker:
    """Get the global token tracker instance"""
    return _global_tracker

def record_llm_call(agent_name: str, call_type: str, response, model: str = "hackathon-gemini-2.5-pro"):
    """Convenience function to record an LLM call"""
    _global_tracker.record_call(agent_name, call_type, response, model)
