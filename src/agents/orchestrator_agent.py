"""
Orchestrator Agent
Manages agent execution order, dependencies, parallelization, and error handling
"""

import os
from typing import Dict, Any, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from enum import Enum

from .ingestion import IngestionAgent
from .linkedin_agent import LinkedInAnalyticsAgent
from .instagram_agent import InstagramAnalyticsAgent
from .website_agent import WebsiteAnalyticsAgent
from .strategy_agent import StrategyAgent
from .models import DataStore


class AgentStatus(Enum):
    """Status of agent execution"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class AgentResult:
    """Result of agent execution"""
    agent_name: str
    status: AgentStatus
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0


class OrchestratorAgent:
    """
    Orchestrates multi-agent execution with dependency management,
    parallelization, and error handling.
    """
    
    def __init__(self, data_dir: str, status_writer=None):
        self.data_dir = data_dir
        self.results: Dict[str, AgentResult] = {}
        self.store: Optional[DataStore] = None
        self.status_writer = status_writer  # Optional status writer for real-time updates
    
    def _log(self, message: str):
        """Log message to both console and status writer if available"""
        print(message)
        if self.status_writer:
            self.status_writer.write(message)
        
    def execute_all(self) -> Dict[str, Any]:
        """
        Execute all agents in the correct order with parallelization where possible.
        
        Returns:
            Dict with agent results and aggregated data
        """
        import time
        
        # Phase 1: Ingestion (must run first, sequential)
        ingestion_result = self._execute_ingestion()
        if ingestion_result.status == AgentStatus.FAILED:
            return self._build_error_response("Ingestion failed - cannot proceed")
        
        # Phase 2: Platform Analytics Agents (can run in parallel)
        platform_results = self._execute_platform_agents_parallel()
        self._log("  ✓ Platform analytics agents completed")
        
        # Phase 3: Strategy Agent (depends on platform agents)
        strategy_result = self._execute_strategy_agent(platform_results)
        if strategy_result.status == AgentStatus.SUCCESS:
            self._log(f"  ✓ Strategy agent completed ({len(strategy_result.result)} insights)")
        elif strategy_result.status == AgentStatus.SKIPPED:
            self._log("  ⚠ Strategy agent skipped (no platform insights)")
        else:
            self._log(f"  ✗ Strategy agent failed: {strategy_result.error[:100]}")
        
        # Build final response
        self._log("  ✅ All agents completed successfully")
        return self._build_success_response(platform_results, strategy_result)
    
    def _execute_ingestion(self) -> AgentResult:
        """Execute IngestionAgent in parallel for all platforms"""
        import time
        start_time = time.time()
        
        try:
            # Create separate agents for each platform (parallel execution)
            def load_linkedin():
                try:
                    agent = IngestionAgent(self.data_dir, status_writer=self.status_writer)
                    return ("linkedin", agent.load_linkedin_only(), None)
                except Exception as e:
                    return ("linkedin", None, str(e))
            
            def load_website():
                try:
                    agent = IngestionAgent(self.data_dir, status_writer=self.status_writer)
                    return ("website", agent.load_website_only(), None)
                except Exception as e:
                    return ("website", None, str(e))
            
            def load_instagram():
                try:
                    agent = IngestionAgent(self.data_dir, status_writer=self.status_writer)
                    return ("instagram", agent.load_instagram_only(), None)
                except Exception as e:
                    return ("instagram", None, str(e))
            
            # Execute all three in parallel
            platform_stores = {}
            errors = {}
            
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = {
                    executor.submit(load_linkedin): "linkedin",
                    executor.submit(load_website): "website",
                    executor.submit(load_instagram): "instagram"
                }
                
                for future in as_completed(futures):
                    try:
                        platform, store, error = future.result()
                        if error:
                            errors[platform] = error
                            self._log(f"  ✗ {platform.capitalize()} ingestion failed: {error}")
                        else:
                            platform_stores[platform] = store
                            self._log(f"  ✓ {platform.capitalize()} ingestion completed")
                    except Exception as e:
                        platform = futures[future]
                        errors[platform] = str(e)
                        self._log(f"  ✗ {platform.capitalize()} ingestion failed: {str(e)}")
            
            # Merge all stores into one
            self.store = self._merge_stores(platform_stores)
            
            # Check if we have at least one successful platform
            if not platform_stores:
                execution_time = time.time() - start_time
                result = AgentResult(
                    agent_name="IngestionAgent",
                    status=AgentStatus.FAILED,
                    error=f"All platform ingestion failed. Errors: {errors}",
                    execution_time=execution_time
                )
                self.results["ingestion"] = result
                return result
            
            # Log partial success if some platforms failed
            if errors:
                self._log(f"  ⚠ Partial ingestion: {len(platform_stores)}/{3} platforms succeeded")
            
            execution_time = time.time() - start_time
            result = AgentResult(
                agent_name="IngestionAgent",
                status=AgentStatus.SUCCESS,
                result=self.store,
                execution_time=execution_time
            )
            self.results["ingestion"] = result
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            result = AgentResult(
                agent_name="IngestionAgent",
                status=AgentStatus.FAILED,
                error=str(e),
                execution_time=execution_time
            )
            self.results["ingestion"] = result
            return result
    
    def _merge_stores(self, platform_stores: Dict[str, DataStore]) -> DataStore:
        """Merge multiple DataStore objects into one"""
        merged = DataStore()
        
        for platform, store in platform_stores.items():
            if store is None:
                continue
            
            # Merge LinkedIn data
            if platform == "linkedin":
                merged.linkedin_metrics.extend(store.linkedin_metrics)
                merged.linkedin_followers.extend(store.linkedin_followers)
                merged.linkedin_visitors.extend(store.linkedin_visitors)
            
            # Merge Instagram data
            elif platform == "instagram":
                merged.instagram_metrics.extend(store.instagram_metrics)
                merged.instagram_audience_insights.extend(store.instagram_audience_insights)
                merged.instagram_content_interactions.extend(store.instagram_content_interactions)
                merged.instagram_live_videos.extend(store.instagram_live_videos)
                merged.instagram_profiles_reached.extend(store.instagram_profiles_reached)
            
            # Merge Website data
            elif platform == "website":
                merged.website_metrics.extend(store.website_metrics)
            
            # Merge competitors (from any store)
            if store.competitors:
                merged.competitors.extend(store.competitors)
        
        return merged
    
    def _execute_platform_agents_parallel(self) -> Dict[str, AgentResult]:
        """Execute platform analytics agents in parallel"""
        if not self.store:
            print("  ⚠ No store available, skipping platform agents")
            return {}
        
        self._log("  📊 Running platform analytics agents (in parallel)...")
        platform_results = {}
        
        def run_linkedin():
            try:
                import time
                self._log("    → Starting LinkedIn analytics...")
                start = time.time()
                agent = LinkedInAnalyticsAgent(self.store, status_writer=self.status_writer)
                insights = agent.analyze()
                self._log(f"    ✓ LinkedIn analytics completed ({len(insights)} insights)")
                return ("linkedin", AgentResult(
                    agent_name="LinkedInAnalyticsAgent",
                    status=AgentStatus.SUCCESS,
                    result=insights,
                    execution_time=time.time() - start
                ))
            except Exception as e:
                import time
                self._log(f"    ✗ LinkedIn analytics failed: {str(e)[:100]}")
                return ("linkedin", AgentResult(
                    agent_name="LinkedInAnalyticsAgent",
                    status=AgentStatus.FAILED,
                    error=str(e),
                    execution_time=0.0
                ))
        
        def run_instagram():
            try:
                import time
                self._log("    → Starting Instagram analytics...")
                start = time.time()
                agent = InstagramAnalyticsAgent(self.store, status_writer=self.status_writer)
                insights = agent.analyze()
                self._log(f"    ✓ Instagram analytics completed ({len(insights)} insights)")
                return ("instagram", AgentResult(
                    agent_name="InstagramAnalyticsAgent",
                    status=AgentStatus.SUCCESS,
                    result=insights,
                    execution_time=time.time() - start
                ))
            except Exception as e:
                import time
                self._log(f"    ✗ Instagram analytics failed: {str(e)[:100]}")
                return ("instagram", AgentResult(
                    agent_name="InstagramAnalyticsAgent",
                    status=AgentStatus.FAILED,
                    error=str(e),
                    execution_time=0.0
                ))
        
        def run_website():
            try:
                import time
                self._log("    → Starting Website analytics...")
                start = time.time()
                agent = WebsiteAnalyticsAgent(self.store, status_writer=self.status_writer)
                insights = agent.analyze()
                self._log(f"    ✓ Website analytics completed ({len(insights)} insights)")
                return ("website", AgentResult(
                    agent_name="WebsiteAnalyticsAgent",
                    status=AgentStatus.SUCCESS,
                    result=insights,
                    execution_time=time.time() - start
                ))
            except Exception as e:
                import time
                self._log(f"    ✗ Website analytics failed: {str(e)[:100]}")
                return ("website", AgentResult(
                    agent_name="WebsiteAnalyticsAgent",
                    status=AgentStatus.FAILED,
                    error=str(e),
                    execution_time=0.0
                ))
        
        # Execute in parallel
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(run_linkedin): "linkedin",
                executor.submit(run_instagram): "instagram",
                executor.submit(run_website): "website"
            }
            
            for future in as_completed(futures):
                try:
                    platform_key, result = future.result()
                    platform_results[platform_key] = result
                    if result.status == AgentStatus.SUCCESS:
                        print(f"    ✓ {platform_key.capitalize()} agent completed successfully")
                    else:
                        print(f"    ✗ {platform_key.capitalize()} agent failed: {result.error[:100] if result.error else 'Unknown error'}")
                    self.results[platform_key] = result
                except Exception as e:
                    platform_key = futures[future]
                    result = AgentResult(
                        agent_name=f"{platform_key.capitalize()}AnalyticsAgent",
                        status=AgentStatus.FAILED,
                        error=str(e),
                        execution_time=0.0
                    )
                    platform_results[platform_key] = result
                    self.results[platform_key] = result
        
        return platform_results
    
    def _execute_strategy_agent(self, platform_results: Dict[str, AgentResult]) -> AgentResult:
        """Execute StrategyAgent (only if we have some platform insights)"""
        import time
        start_time = time.time()

        self._log("  🎯 Running strategy agent...")
        
        # Check if we have at least one successful platform agent
        successful_platforms = {
            k: r.result for k, r in platform_results.items()
            if r.status == AgentStatus.SUCCESS and r.result
        }
        
        if not successful_platforms:
            result = AgentResult(
                agent_name="StrategyAgent",
                status=AgentStatus.SKIPPED,
                error="No platform insights available",
                execution_time=time.time() - start_time
            )
            self.results["strategy"] = result
            return result
        
        try:
            # Build platform insights dict (use empty list for failed agents)
            platform_insights = {
                'LinkedIn': platform_results.get('linkedin', AgentResult("", AgentStatus.FAILED)).result or [],
                'Instagram': platform_results.get('instagram', AgentResult("", AgentStatus.FAILED)).result or [],
                'Website': platform_results.get('website', AgentResult("", AgentStatus.FAILED)).result or []
            }
            
            strategy_agent = StrategyAgent(self.store, platform_insights, status_writer=self.status_writer)
            self._log("    → Generating executive summary...")
            executive_insights = strategy_agent.generate_executive_summary()
            self._log(f"    ✓ Executive summary generated ({len(executive_insights)} insights)")
            
            execution_time = time.time() - start_time
            result = AgentResult(
                agent_name="StrategyAgent",
                status=AgentStatus.SUCCESS,
                result=executive_insights,
                execution_time=execution_time
            )
            self.results["strategy"] = result
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            result = AgentResult(
                agent_name="StrategyAgent",
                status=AgentStatus.FAILED,
                error=str(e),
                execution_time=execution_time
            )
            self.results["strategy"] = result
            return result
    
    def _build_success_response(self, platform_results: Dict[str, AgentResult], 
                                strategy_result: AgentResult) -> Dict[str, Any]:
        """Build final response with all results"""
        # Extract insights (use empty list if agent failed)
        linkedin_insights = platform_results.get('linkedin', AgentResult("", AgentStatus.FAILED)).result or []
        instagram_insights = platform_results.get('instagram', AgentResult("", AgentStatus.FAILED)).result or []
        website_insights = platform_results.get('website', AgentResult("", AgentStatus.FAILED)).result or []
        executive_insights = strategy_result.result or [] if strategy_result.status == AgentStatus.SUCCESS else []
        
        # Build execution summary
        ingestion_result = self.results.get("ingestion", AgentResult("", AgentStatus.PENDING))
        # Get token usage summary
        try:
            from .token_tracker import get_tracker
            token_summary = get_tracker().get_summary()
            token_usage = {
                "total_calls": token_summary.total_calls,
                "total_tokens": token_summary.total_tokens,
                "total_prompt_tokens": token_summary.total_prompt_tokens,
                "total_completion_tokens": token_summary.total_completion_tokens,
                "total_cost": token_summary.total_cost,
                "by_agent": {
                    agent: {
                        "calls": token_summary.calls_by_agent.get(agent, 0),
                        "tokens": token_summary.tokens_by_agent.get(agent, 0),
                        "cost": token_summary.cost_by_agent.get(agent, 0.0)
                    }
                    for agent in set(token_summary.calls_by_agent.keys())
                }
            }
        except Exception as e:
            print(f"⚠️ Could not get token usage summary: {e}")
            token_usage = {}
        
        execution_summary = {
            "ingestion": {
                "status": ingestion_result.status.value,
                "execution_time": ingestion_result.execution_time,
                "parallel": True,  # Indicate parallel execution
                "platforms": {
                    "linkedin": "loaded" if self.store and self.store.linkedin_metrics else "failed",
                    "instagram": "loaded" if self.store and self.store.instagram_metrics else "failed",
                    "website": "loaded" if self.store and self.store.website_metrics else "failed"
                }
            },
            "platform_agents": {
                k: {
                    "status": r.status.value,
                    "execution_time": r.execution_time,
                    "error": r.error if r.status == AgentStatus.FAILED else None
                }
                for k, r in platform_results.items()
            },
            "strategy": {
                "status": strategy_result.status.value,
                "execution_time": strategy_result.execution_time,
                "error": strategy_result.error if strategy_result.status == AgentStatus.FAILED else None
            },
            "token_usage": token_usage  # Add token usage to execution summary
        }
        
        return {
            'store': self.store,
            'linkedin': linkedin_insights,
            'instagram': instagram_insights,
            'website': website_insights,
            'executive': executive_insights,
            'execution_summary': execution_summary  # New: execution metadata
        }
    
    def _build_error_response(self, error_message: str) -> Dict[str, Any]:
        """Build error response"""
        return {
            'store': None,
            'linkedin': [],
            'instagram': [],
            'website': [],
            'executive': [],
            'execution_summary': {
                "error": error_message,
                "ingestion": {
                    "status": "failed",
                    "execution_time": 0.0
                }
            }
        }
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get summary of agent execution status"""
        return {
            agent_name: {
                "status": result.status.value,
                "execution_time": result.execution_time,
                "error": result.error if result.status == AgentStatus.FAILED else None
            }
            for agent_name, result in self.results.items()
        }
