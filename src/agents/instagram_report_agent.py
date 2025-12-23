"""
Instagram Report Generation Agent
Generates comprehensive reports from Instagram JSON files using LLM analysis
"""

import os
import json
import glob
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import litellm

load_dotenv()
litellm.use_litellm_proxy = True
API_BASE = os.getenv("LITELLM_PROXY_API_BASE")
API_KEY = os.getenv("LITELLM_PROXY_GEMINI_API_KEY")


class InstagramReportAgent:
    """Generates comprehensive reports from Instagram data files using LLM analysis"""
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.instagram_dir = f"{data_dir}/src/data/instagram"
        
    def generate_report(self, files: List[str] = None, report_type: str = "comprehensive") -> Dict[str, Any]:
        """
        Generate report from specified Instagram files
        
        Args:
            files: List of file types to include ['posts', 'audience_insights', 'content_interactions', 'live_videos', 'profiles_reached']
                  If None, includes all available files
            report_type: 'comprehensive', 'trends', 'correlations', 'executive'
        
        Returns:
            Dict with report sections and analysis
        """
        if files is None:
            files = ['posts', 'audience_insights', 'content_interactions', 'live_videos', 'profiles_reached']
        
        # Load all requested files
        data = self._load_files(files)
        
        if not data:
            return {
                'error': 'No data files found or loaded',
                'files_requested': files
            }
        
        # Use LLM to analyze
        analysis = self._llm_analyze(data, files, report_type)
        
        # Generate formatted report
        report = {
            'files_analyzed': files,
            'report_type': report_type,
            'generated_at': datetime.now().isoformat(),
            'data_summary': self._generate_data_summary(data),
            'analysis': analysis,
            'recommendations': self._extract_recommendations(analysis)
        }
        
        return report
    
    def _load_files(self, files: List[str]) -> Dict[str, Dict]:
        """Load requested JSON files"""
        data = {}
        
        # Map file types to filenames
        file_mapping = {
            'posts': 'posts.json',
            'audience_insights': 'audience_insights.json',
            'content_interactions': 'content_interactions.json',
            'live_videos': 'live_videos.json',
            'profiles_reached': 'profiles_reached.json'
        }
        
        for file_type in files:
            filename = file_mapping.get(file_type)
            if not filename:
                continue
            
            json_path = f"{self.instagram_dir}/{filename}"
            if os.path.exists(json_path):
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        data[file_type] = json.load(f)
                    print(f"  ✓ Loaded {file_type} file")
                except Exception as e:
                    print(f"  ✗ Error loading {file_type}: {e}")
        
        return data
    
    def _generate_data_summary(self, data: Dict[str, Dict]) -> Dict[str, Any]:
        """Generate summary statistics for loaded data"""
        summary = {}
        
        for file_type, json_data in data.items():
            summary[file_type] = {
                'file_type': file_type,
                'top_level_keys': list(json_data.keys()),
                'sample_size': self._get_sample_size(json_data, file_type),
                'date_range': self._get_date_range(json_data, file_type)
            }
        
        return summary
    
    def _get_sample_size(self, json_data: Dict, file_type: str) -> int:
        """Get sample size from JSON data"""
        # Try to find array data
        for key, value in json_data.items():
            if isinstance(value, list):
                return len(value)
            elif isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, list):
                        return len(sub_value)
        return 0
    
    def _get_date_range(self, json_data: Dict, file_type: str) -> Dict[str, str]:
        """Extract date range from JSON data if available"""
        # Try to find date information in the JSON structure
        try:
            if file_type == 'posts':
                posts = json_data.get('organic_insights_posts', [])
                if posts:
                    timestamps = []
                    for post in posts:
                        timestamp = post.get('string_map_data', {}).get('Creation timestamp', {}).get('timestamp', 0)
                        if timestamp:
                            timestamps.append(timestamp)
                    if timestamps:
                        from datetime import datetime
                        dates = [datetime.fromtimestamp(ts).date() for ts in timestamps if ts > 0]
                        if dates:
                            return {
                                'start': min(dates).strftime('%Y-%m-%d'),
                                'end': max(dates).strftime('%Y-%m-%d'),
                                'count': len(dates)
                            }
        except:
            pass
        
        return {'start': 'Unknown', 'end': 'Unknown', 'count': 0}
    
    def _llm_analyze(self, data: Dict[str, Dict], files: List[str], report_type: str) -> str:
        """Use LLM to analyze trends and patterns across files"""
        if not API_BASE or not API_KEY:
            return "LLM unavailable. Cannot generate analysis."
        
        # Prepare data context for LLM
        data_context = self._prepare_data_context(data, files)
        
        # Build prompt based on report type
        if report_type == "comprehensive":
            prompt = self._build_comprehensive_prompt(data_context, files)
        elif report_type == "trends":
            prompt = self._build_trends_prompt(data_context, files)
        elif report_type == "correlations":
            prompt = self._build_correlations_prompt(data_context, files)
        elif report_type == "executive":
            prompt = self._build_executive_prompt(data_context, files)
        else:
            prompt = self._build_comprehensive_prompt(data_context, files)
        
        try:
            response = litellm.completion(
                model="hackathon-gemini-2.5-pro",
                api_base=API_BASE,
                api_key=API_KEY,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an Instagram analytics expert. Analyze data and provide comprehensive, actionable insights with specific recommendations. Use markdown formatting for better readability."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=4000
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Analysis error: {str(e)[:200]}"
    
    def _prepare_data_context(self, data: Dict[str, Dict], files: List[str]) -> str:
        """Prepare data context for LLM analysis"""
        context_parts = []
        
        for file_type, json_data in data.items():
            # Get summary statistics
            summary = self._get_file_summary(json_data, file_type)
            context_parts.append(f"\n## {file_type.upper()} File Data:\n{summary}")
        
        return "\n".join(context_parts)
    
    def _get_file_summary(self, json_data: Dict, file_type: str) -> str:
        """Generate summary statistics for a file"""
        summary_lines = [
            f"- File type: {file_type}",
            f"- Top-level keys: {', '.join(list(json_data.keys())[:5])}",
        ]
        
        # Get sample data
        sample_data = self._extract_sample_data(json_data, file_type)
        if sample_data:
            summary_lines.append(f"\n### Sample Data:")
            summary_lines.append(json.dumps(sample_data, default=str, indent=2)[:1000])  # Limit size
        
        return "\n".join(summary_lines)
    
    def _extract_sample_data(self, json_data: Dict, file_type: str) -> Optional[Dict]:
        """Extract sample data from JSON structure"""
        try:
            # Try to find the main data array
            for key, value in json_data.items():
                if isinstance(value, list) and len(value) > 0:
                    # Return first item as sample
                    return {key: value[0] if len(value) > 0 else None}
                elif isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, list) and len(sub_value) > 0:
                            return {f"{key}.{sub_key}": sub_value[0]}
        except:
            pass
        return None
    
    def _build_comprehensive_prompt(self, data_context: str, files: List[str]) -> str:
        """Build prompt for comprehensive report"""
        return f"""Analyze these Instagram data files and generate a comprehensive report.

Files analyzed: {', '.join(files)}

{data_context}

Please provide a comprehensive analysis including:

1. **Executive Summary**
   - Key findings across all files
   - Overall performance trends

2. **Trend Analysis**
   - Trends within each file over time
   - Growth patterns and changes
   - Peak and low periods

3. **Cross-File Correlations** (if multiple files)
   - Relationships between metrics across files
   - How post performance affects audience growth
   - Causal patterns and timing

4. **Pattern Recognition**
   - Content type performance (posts, reels, stories)
   - Engagement patterns
   - Audience behavior insights
   - Anomalies and outliers

5. **Key Insights**
   - What's working well
   - Areas of concern
   - Opportunities for improvement

6. **Actionable Recommendations**
   - Specific actions to take
   - Prioritized by impact

Format the response in clear markdown with headers and bullet points."""
    
    def _build_trends_prompt(self, data_context: str, files: List[str]) -> str:
        """Build prompt for trends-focused report"""
        return f"""Analyze trends in these Instagram data files.

Files analyzed: {', '.join(files)}

{data_context}

Focus on:
- Time-series trends for each metric
- Growth rates and acceleration/deceleration
- Period-over-period comparisons
- Best and worst performing periods
- Trend predictions based on current patterns

Provide specific numbers and percentages where possible."""
    
    def _build_correlations_prompt(self, data_context: str, files: List[str]) -> str:
        """Build prompt for correlations-focused report"""
        return f"""Analyze correlations between these Instagram data files.

Files analyzed: {', '.join(files)}

{data_context}

Identify:
- How post engagement (posts file) correlates with audience growth (audience_insights file)
- How content interactions relate to profiles reached
- Timing relationships (e.g., does engagement spike precede audience growth?)
- Causal patterns and lead/lag indicators
- Which metrics drive other metrics

Provide specific correlation insights with timing details."""
    
    def _build_executive_prompt(self, data_context: str, files: List[str]) -> str:
        """Build prompt for executive summary report"""
        return f"""Generate an executive summary for Instagram performance.

Files analyzed: {', '.join(files)}

{data_context}

Provide a concise executive summary (2-3 paragraphs) covering:
- Overall performance status
- Key metrics and trends
- Top 3 strategic recommendations
- Risk areas to monitor

Keep it high-level and actionable for C-suite decision making."""
    
    def _extract_recommendations(self, analysis: str) -> List[str]:
        """Extract recommendations from LLM analysis"""
        recommendations = []
        
        lines = analysis.split('\n')
        in_recommendations = False
        
        for line in lines:
            if 'recommendation' in line.lower() or 'action' in line.lower():
                if '#' in line:
                    in_recommendations = True
                    continue
            
            if in_recommendations:
                if line.startswith('#') and 'recommendation' not in line.lower():
                    break
                
                if line.strip().startswith(('-', '*', '•', '1.', '2.', '3.')):
                    rec = line.strip().lstrip('-*•1234567890. ').strip()
                    if rec and len(rec) > 10:
                        recommendations.append(rec)
        
        if not recommendations:
            sentences = analysis.split('.')
            for sentence in sentences[-10:]:
                if any(word in sentence.lower() for word in ['should', 'recommend', 'suggest', 'focus', 'increase', 'improve', 'optimize']):
                    rec = sentence.strip()
                    if len(rec) > 20:
                        recommendations.append(rec)
        
        return recommendations[:5]
