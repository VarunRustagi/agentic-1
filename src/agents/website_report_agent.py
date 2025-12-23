"""
Website Report Generation Agent
Generates comprehensive reports from Website CSV files using LLM analysis
"""

import os
import pandas as pd
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


class WebsiteReportAgent:
    """Generates comprehensive reports from Website data files using LLM analysis"""
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.website_dir = f"{data_dir}/src/data/website"
        
    def generate_report(self, files: List[str] = None, report_type: str = "comprehensive") -> Dict[str, Any]:
        """
        Generate report from specified Website files
        
        Args:
            files: List of file types to include ['blog', 'traffic', 'sessions', 'all']
                  If None, includes all available files
            report_type: 'comprehensive', 'trends', 'correlations', 'executive'
        
        Returns:
            Dict with report sections and analysis
        """
        if files is None:
            files = ['all']  # Load all files by default
        
        # Load all requested files
        data = self._load_files(files)
        
        if not data:
            return {
                'error': 'No data files found or loaded',
                'files_requested': files
            }
        
        # Use LLM to analyze
        analysis = self._llm_analyze(data, list(data.keys()), report_type)
        
        # Generate formatted report
        report = {
            'files_analyzed': list(data.keys()),
            'report_type': report_type,
            'generated_at': datetime.now().isoformat(),
            'data_summary': self._generate_data_summary(data),
            'analysis': analysis,
            'recommendations': self._extract_recommendations(analysis)
        }
        
        return report
    
    def _load_files(self, files: List[str]) -> Dict[str, pd.DataFrame]:
        """Load requested CSV files"""
        data = {}
        
        # If 'all' is requested, load all CSV files
        if 'all' in files:
            csv_files = glob.glob(f"{self.website_dir}/*.csv")
            for csv_path in csv_files:
                filename = os.path.basename(csv_path)
                file_type = self._classify_file(filename)
                try:
                    df = pd.read_csv(csv_path)
                    data[file_type] = df
                    print(f"  ✓ Loaded {file_type} file: {len(df)} rows")
                except Exception as e:
                    print(f"  ✗ Error loading {filename}: {e}")
        else:
            # Map file types to patterns
            file_patterns = {
                'blog': '*blog*.csv',
                'traffic': '*traffic*.csv',
                'sessions': '*report*.csv'
            }
            
            for file_type in files:
                pattern = file_patterns.get(file_type)
                if not pattern:
                    continue
                
                csv_files = glob.glob(f"{self.website_dir}/{pattern}")
                for csv_path in csv_files:
                    try:
                        df = pd.read_csv(csv_path)
                        # Use filename as key to avoid duplicates
                        key = f"{file_type}_{os.path.basename(csv_path)}"
                        data[key] = df
                        print(f"  ✓ Loaded {file_type} file: {len(df)} rows")
                    except Exception as e:
                        print(f"  ✗ Error loading {file_type}: {e}")
        
        return data
    
    def _classify_file(self, filename: str) -> str:
        """Classify file type based on filename"""
        filename_lower = filename.lower()
        if 'blog' in filename_lower:
            return 'blog'
        elif 'traffic' in filename_lower:
            return 'traffic'
        elif 'report' in filename_lower or 'session' in filename_lower:
            return 'sessions'
        else:
            return 'other'
    
    def _generate_data_summary(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Generate summary statistics for loaded data"""
        summary = {}
        
        for file_type, df in data.items():
            summary[file_type] = {
                'rows': len(df),
                'columns': list(df.columns),
                'date_range': self._get_date_range(df, file_type),
                'sample_size': min(5, len(df))
            }
        
        return summary
    
    def _get_date_range(self, df: pd.DataFrame, file_type: str) -> Dict[str, str]:
        """Extract date range from dataframe"""
        date_col = None
        
        # Try to find date column
        for col in df.columns:
            if 'date' in col.lower() or 'time' in col.lower():
                date_col = col
                break
        
        if date_col:
            try:
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                dates = df[date_col].dropna()
                if len(dates) > 0:
                    return {
                        'start': dates.min().strftime('%Y-%m-%d'),
                        'end': dates.max().strftime('%Y-%m-%d'),
                        'days': len(dates.unique())
                    }
            except:
                pass
        
        return {'start': 'Unknown', 'end': 'Unknown', 'days': len(df)}
    
    def _llm_analyze(self, data: Dict[str, pd.DataFrame], files: List[str], report_type: str) -> str:
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
                        "content": "You are a website analytics expert. Analyze data and provide comprehensive, actionable insights with specific recommendations. Use markdown formatting for better readability."
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
    
    def _prepare_data_context(self, data: Dict[str, pd.DataFrame], files: List[str]) -> str:
        """Prepare data context for LLM analysis"""
        context_parts = []
        
        for file_type, df in data.items():
            # Get summary statistics
            summary = self._get_file_summary(df, file_type)
            context_parts.append(f"\n## {file_type.upper()} File Data:\n{summary}")
        
        return "\n".join(context_parts)
    
    def _get_file_summary(self, df: pd.DataFrame, file_type: str) -> str:
        """Generate summary statistics for a file"""
        summary_lines = [
            f"- Total rows: {len(df)}",
            f"- Columns: {', '.join(df.columns[:10])}" + ("..." if len(df.columns) > 10 else ""),
        ]
        
        # Get date range if available
        date_col = None
        for col in df.columns:
            if 'date' in col.lower() or 'time' in col.lower():
                date_col = col
                break
        
        if date_col:
            try:
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                dates = df[date_col].dropna()
                if len(dates) > 0:
                    summary_lines.append(f"- Date range: {dates.min().strftime('%Y-%m-%d')} to {dates.max().strftime('%Y-%m-%d')}")
            except:
                pass
        
        # Get numeric column statistics
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            summary_lines.append(f"\n### Key Metrics (last 30 rows if available):")
            for col in numeric_cols[:5]:
                try:
                    recent = df[col].tail(30)
                    if len(recent) > 0:
                        avg = recent.mean()
                        summary_lines.append(f"- {col}: Average = {avg:,.0f}")
                except:
                    pass
        
        # Sample data (first 3 rows, key columns)
        summary_lines.append(f"\n### Sample Data (first 3 rows):")
        key_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['date', 'page', 'visitor', 'view', 'session', 'bounce', 'traffic'])]
        if key_cols:
            sample_cols = key_cols[:5]
            sample = df[sample_cols].head(3).to_string()
            summary_lines.append(sample)
        else:
            sample = df.head(3).to_string()
            summary_lines.append(sample)
        
        return "\n".join(summary_lines)
    
    def _build_comprehensive_prompt(self, data_context: str, files: List[str]) -> str:
        """Build prompt for comprehensive report"""
        return f"""Analyze these website analytics data files and generate a comprehensive report.

Files analyzed: {', '.join(files)}

{data_context}

Please provide a comprehensive analysis including:

1. **Executive Summary**
   - Key findings across all files
   - Overall traffic and engagement trends

2. **Trend Analysis**
   - Trends within each file over time
   - Traffic growth patterns and changes
   - Peak and low periods

3. **Cross-File Correlations** (if multiple files)
   - Relationships between blog traffic and overall site traffic
   - How traffic reports relate to session data
   - Causal patterns and timing

4. **Pattern Recognition**
   - Weekly patterns (weekday vs weekend)
   - Seasonal trends
   - Bounce rate patterns
   - Visitor behavior insights
   - Anomalies and outliers

5. **Key Insights**
   - What's working well
   - Areas of concern (high bounce rates, low engagement)
   - Opportunities for improvement

6. **Actionable Recommendations**
   - Specific actions to take
   - Prioritized by impact

Format the response in clear markdown with headers and bullet points."""
    
    def _build_trends_prompt(self, data_context: str, files: List[str]) -> str:
        """Build prompt for trends-focused report"""
        return f"""Analyze trends in these website analytics data files.

Files analyzed: {', '.join(files)}

{data_context}

Focus on:
- Time-series trends for each metric
- Traffic growth rates and acceleration/deceleration
- Period-over-period comparisons
- Best and worst performing periods
- Bounce rate trends
- Visitor retention patterns
- Trend predictions based on current patterns

Provide specific numbers and percentages where possible."""
    
    def _build_correlations_prompt(self, data_context: str, files: List[str]) -> str:
        """Build prompt for correlations-focused report"""
        return f"""Analyze correlations between these website analytics data files.

Files analyzed: {', '.join(files)}

{data_context}

Identify:
- How blog traffic (blog file) correlates with overall site traffic (traffic file)
- How page views relate to unique visitors
- Timing relationships (e.g., does blog activity drive site traffic?)
- Bounce rate vs engagement correlations
- Causal patterns and lead/lag indicators
- Which metrics drive other metrics

Provide specific correlation insights with timing details."""
    
    def _build_executive_prompt(self, data_context: str, files: List[str]) -> str:
        """Build prompt for executive summary report"""
        return f"""Generate an executive summary for website performance.

Files analyzed: {', '.join(files)}

{data_context}

Provide a concise executive summary (2-3 paragraphs) covering:
- Overall traffic performance status
- Key metrics and trends
- Top 3 strategic recommendations
- Risk areas to monitor (high bounce rates, traffic drops)

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
