import pandas as pd
import json
import random
import os
import glob
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import litellm
from .models import (
    DataStore, DailyMetric, InstagramMetric, WebsiteMetric,
    LinkedInFollowersMetric, LinkedInVisitorsMetric,
    InstagramAudienceInsight, InstagramContentInteraction,
    InstagramLiveVideo, InstagramProfilesReached
)

load_dotenv()
litellm.use_litellm_proxy = True
API_BASE = os.getenv("LITELLM_PROXY_API_BASE")
API_KEY = os.getenv("LITELLM_PROXY_GEMINI_API_KEY")

class IngestionAgent:
    """AI-powered data ingestion agent that uses LLMs to understand schemas and extract metrics"""
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.store = DataStore()

    def load_data(self):
        """Load all data sources: LinkedIn (real), Website (real), Instagram (real)"""
        print("Loading LinkedIn data...")
        self._load_linkedin_data()
        
        print("Loading Website data...")
        self._load_website_data()
        
        print("Loading Instagram data...")
        self._load_instagram_data()
        
        # print("Loading competitors...")
        # self._load_competitors()
        
        return self.store
    
    def _complete_truncated_json(self, json_str: str) -> str:
        """Attempt to complete truncated JSON by closing open structures"""
        if not json_str:
            return json_str
        
        # Count open/close braces and brackets
        open_braces = json_str.count('{')
        close_braces = json_str.count('}')
        open_brackets = json_str.count('[')
        close_brackets = json_str.count(']')
        
        # Remove trailing comma if present
        json_str = json_str.rstrip().rstrip(',')
        
        # Close any open strings (find last unclosed quote)
        # Simple heuristic: if ends with quote, it's likely incomplete
        if json_str.rstrip().endswith('"'):
            # Check if it's actually closed
            quote_count = json_str.count('"')
            if quote_count % 2 != 0:
                # Unclosed string, remove the incomplete part
                last_quote = json_str.rfind('"')
                if last_quote > 0:
                    # Find the start of this property
                    before_quote = json_str[:last_quote].rstrip()
                    if before_quote.endswith(':'):
                        # Incomplete property value, remove it
                        json_str = before_quote.rstrip(':').rstrip()
        
        # Close any open objects/arrays
        for _ in range(open_braces - close_braces):
            json_str += '}'
        for _ in range(open_brackets - close_brackets):
            json_str += ']'
        
        return json_str
    
    def _call_llm(self, prompt: str, context: str) -> Optional[Dict[str, Any]]:
        """Helper to call LLM via LiteLLM for schema discovery and data mapping"""
        if not API_BASE or not API_KEY:
            return None
            
        try:
            response = litellm.completion(
                model="hackathon-gemini-2.5-pro",
                api_base=API_BASE,
                api_key=API_KEY,
                messages=[
                    {"role": "system", "content": "You are a data schema expert. Analyze file structures and provide ONLY valid JSON responses with field mappings. Do not include any markdown formatting or code blocks. Return complete, valid JSON only. Keep responses concise."},
                    {"role": "user", "content": f"{context}\n\n{prompt}"}
                ],
                max_tokens=2000,  # Increased to prevent truncation
                response_format={"type": "json_object"}
            )
            
            # Handle None response
            if not response:
                print(f"    ⚠ LLM returned None response (check API connection)")
                return None
            
            if not response.choices:
                print(f"    ⚠ LLM response has no choices (check API response)")
                return None
            
            if not response.choices[0].message:
                print(f"    ⚠ LLM response message is None")
                return None
            
            result = response.choices[0].message.content
            if not result:
                print(f"    ⚠ LLM response content is None (model may have refused or errored)")
                # Debug: print response structure
                print(f"    🔍 Debug - Response object type: {type(response)}")
                print(f"    🔍 Debug - Response attributes: {dir(response)}")
                if hasattr(response, 'error'):
                    print(f"    Error details: {response.error}")
                if hasattr(response, 'choices') and response.choices:
                    choice = response.choices[0]
                    print(f"    🔍 Debug - Choice finish_reason: {getattr(choice, 'finish_reason', 'N/A')}")
                    print(f"    🔍 Debug - Choice message type: {type(choice.message) if hasattr(choice, 'message') else 'N/A'}")
                    if hasattr(choice, 'message'):
                        msg = choice.message
                        print(f"    🔍 Debug - Message attributes: {dir(msg)}")
                        print(f"    🔍 Debug - Message content type: {type(msg.content) if hasattr(msg, 'content') else 'N/A'}")
                        if hasattr(msg, 'content') and msg.content is None:
                            # Check for refusal or other indicators
                            if hasattr(msg, 'refusal'):
                                print(f"    🔍 Debug - Message refusal: {msg.refusal}")
                return None
            
            result = result.strip()
            
            # Check if response was truncated
            finish_reason = response.choices[0].finish_reason if hasattr(response.choices[0], 'finish_reason') else None
            if finish_reason == 'length':
                print(f"    ⚠ LLM response was truncated (hit max_tokens limit)")
                # Try to complete the JSON by closing open structures
                result = self._complete_truncated_json(result)
            
            # Print LLM output for debugging (show full response)
            print(f"    🔍 LLM Response (full, {len(result)} chars):")
            print(f"    {result}")
            print(f"    📊 Finish reason: {finish_reason}")
            
            # Try to extract JSON if wrapped in markdown code blocks
            original_result = result
            if result.startswith("```"):
                # Extract JSON from markdown code block
                lines = result.split("\n")
                json_lines = []
                in_json = False
                for line in lines:
                    if line.strip().startswith("```"):
                        in_json = not in_json
                        continue
                    if in_json:
                        json_lines.append(line)
                result = "\n".join(json_lines)
                if result != original_result:
                    print(f"    📝 Extracted from markdown code block")
            
            # Try to parse JSON
            try:
                parsed = json.loads(result) if result else None
                print(f"    ✅ Successfully parsed JSON")
                return parsed
            except json.JSONDecodeError as json_err:
                print(f"    ⚠ JSON parse error: {str(json_err)[:100]}")
                # Try to fix common JSON issues
                import re
                # Remove trailing commas before closing braces/brackets
                fixed_result = re.sub(r',\s*}', '}', result)
                fixed_result = re.sub(r',\s*]', ']', fixed_result)
                # Try to extract JSON object if wrapped in other text
                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', fixed_result, re.DOTALL)
                if json_match:
                    fixed_result = json_match.group(0)
                    print(f"    🔧 Attempting to extract JSON object from text...")
                
                try:
                    parsed = json.loads(fixed_result)
                    print(f"    ✅ Successfully parsed after fixing")
                    return parsed
                except Exception as fix_err:
                    print(f"    ❌ Still invalid JSON after fixes: {str(fix_err)[:100]}")
                    print(f"    📋 Fixed result (first 300 chars): {fixed_result[:300]}")
                    print(f"    ⚠ Using fallback heuristic mapping")
                    return None
                    
        except Exception as e:
            print(f"  ⚠ LLM analysis unavailable: {str(e)[:100]}")
            return None

    def _load_linkedin_data(self):
        """Load LinkedIn data from all CSV files using LLM for schema discovery"""
        linkedin_dir = f"{self.data_dir}/src/data/linkedin"
        if not os.path.exists(linkedin_dir):
            print(f"✗ LinkedIn directory not found: {linkedin_dir}")
            return
        
        # Discover all CSV files
        csv_files = glob.glob(f"{linkedin_dir}/*.csv")
        print(f"  Found {len(csv_files)} CSV files")
        
        for csv_path in csv_files:
            try:
                filename = os.path.basename(csv_path)
                print(f"  Processing: {filename}")
                
                # Read sample of CSV to understand structure
                df = pd.read_csv(csv_path, nrows=5)
                columns = list(df.columns)
                
                # Use LLM to understand schema and map to our data model
                schema_info = self._discover_csv_schema(csv_path, columns, "linkedin")
                
                if schema_info:
                    file_type = schema_info.get('file_type', 'unknown')
                    print(f"    → LLM identified: {file_type} file")
                    
                    # Check if this file type can be processed
                    if file_type == 'content':
                        self._process_linkedin_csv(csv_path, schema_info)
                    elif file_type == 'followers':
                        self._process_linkedin_followers(csv_path, schema_info)
                    elif file_type == 'visitors':
                        self._process_linkedin_visitors(csv_path, schema_info)
                    elif file_type == 'other':
                        print(f"    → Skipping {file_type} file (not in current data model)")
                    else:
                        # Try to process anyway if we have valid mappings
                        mappings = schema_info.get('mappings', {})
                        if any(mappings.get(k) for k in ['impressions', 'clicks', 'reactions']):
                            self._process_linkedin_csv(csv_path, schema_info)
                        else:
                            print(f"    → Skipping {file_type} file (no valid metric mappings)")
                else:
                    # Fallback: try to infer from filename and columns
                    print(f"    → Using heuristic mapping")
                    self._process_linkedin_csv_heuristic(csv_path, columns)
                    
            except Exception as e:
                print(f"    ✗ Error processing {filename}: {e}")
                continue
        
        print(f"✓ Loaded {len(self.store.linkedin_metrics)} LinkedIn content records")
        print(f"✓ Loaded {len(self.store.linkedin_followers)} LinkedIn followers records")
        print(f"✓ Loaded {len(self.store.linkedin_visitors)} LinkedIn visitors records")
    
    def _discover_csv_schema(self, filepath: str, columns: List[str], platform: str) -> Optional[Dict[str, Any]]:
        """Use LLM to discover CSV schema and map to our data models"""
        # Read first few rows for context (simplified format)
        try:
            df_sample = pd.read_csv(filepath, nrows=3)
            # Convert to simple string representation instead of JSON
            sample_text = df_sample.to_string(max_rows=3, max_cols=10)
        except:
            sample_text = "Unable to read sample"
        
        context = f"""Analyze this {platform} CSV file and determine its schema.

File: {os.path.basename(filepath)}
Columns: {', '.join(columns[:15])}
Sample data:
{sample_text[:500]}

Our data model for LinkedIn DailyMetric requires:
- date: date field
- impressions: total impressions
- clicks: total clicks  
- reactions: total reactions
- engagement_rate: engagement rate (0-1)

IMPORTANT: If this file does NOT contain metrics that match DailyMetric (e.g., it's a followers or visitors file), set file_type to "other" and mappings to null values. Always return valid JSON.

Return ONLY valid JSON (no markdown, no code blocks) with this structure:
{{
  "file_type": "content" | "followers" | "visitors" | "other",
  "date_column": "column name or null",
  "date_format": "format or null",
  "mappings": {{
    "impressions": "column name or null",
    "clicks": "column name or null",
    "reactions": "column name or null",
    "engagement_rate": "column name or null"
  }},
  "extraction_strategy": "description"
}}"""
        
        return self._call_llm("Analyze the schema. Return JSON only - use null for fields that don't exist.", context)
    
    def _process_linkedin_csv(self, csv_path: str, schema_info: Dict[str, Any]):
        """Process LinkedIn CSV using LLM-discovered schema"""
        try:
            df = pd.read_csv(csv_path)
            mappings = schema_info.get('mappings', {})
            date_col = schema_info.get('date_column', 'Date')
            
            # Safe extraction helpers
            def safe_int(val):
                try:
                    return int(float(str(val).replace(',','')))
                except:
                    return 0
                    
            def safe_float(val):
                try:
                    val_str = str(val).replace('%','')
                    return float(val_str) / 100 if '%' in str(val) else float(val_str)
                except:
                    return 0.0
            
            for index, row in df.iterrows():
                try:
                    # Parse date
                    date_str = str(row.get(date_col, ''))
                    date_obj = self._parse_date(date_str, schema_info.get('date_format'))
                    if not date_obj:
                        continue
                    
                    # Extract metrics based on LLM mappings
                    impressions = safe_int(row.get(mappings.get('impressions', 'Impressions (total)'), 0))
                    clicks = safe_int(row.get(mappings.get('clicks', 'Clicks (total)'), 0))
                    reactions = safe_int(row.get(mappings.get('reactions', 'Reactions (total)'), 0))
                    engagement_rate = safe_float(row.get(mappings.get('engagement_rate', 'Engagement rate (total)'), 0))
                    
                    # Only create metric if we have meaningful data
                    if impressions > 0 or clicks > 0 or reactions > 0:
                        metric = DailyMetric(
                            date=date_obj,
                            platform="linkedin",
                            impressions=impressions,
                            clicks=clicks,
                            reactions=reactions,
                            engagement_rate=engagement_rate
                        )
                        self.store.linkedin_metrics.append(metric)
                        
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"    ✗ Error processing CSV: {e}")
    
    def _process_linkedin_followers(self, csv_path: str, schema_info: Dict[str, Any]):
        """Process LinkedIn followers CSV file"""
        try:
            df = pd.read_csv(csv_path)
            mappings = schema_info.get('mappings', {})
            date_col = schema_info.get('date_column', 'Date')
            
            def safe_int(val):
                try:
                    return int(float(str(val).replace(',','')))
                except:
                    return 0
            
            for index, row in df.iterrows():
                try:
                    date_str = str(row.get(date_col, ''))
                    date_obj = self._parse_date(date_str, schema_info.get('date_format'))
                    if not date_obj:
                        continue
                    
                    metric = LinkedInFollowersMetric(
                        date=date_obj,
                        sponsored_followers=safe_int(row.get(mappings.get('sponsored_followers', 'Sponsored followers'), 0)),
                        organic_followers=safe_int(row.get(mappings.get('organic_followers', 'Organic followers'), 0)),
                        total_followers=safe_int(row.get(mappings.get('total_followers', 'Total followers'), 0)),
                        raw_data=row.to_dict()  # Store full row for LLM access
                    )
                    self.store.linkedin_followers.append(metric)
                except Exception as e:
                    continue
        except Exception as e:
            print(f"    ✗ Error processing followers CSV: {e}")
    
    def _process_linkedin_visitors(self, csv_path: str, schema_info: Dict[str, Any]):
        """Process LinkedIn visitors CSV file"""
        try:
            df = pd.read_csv(csv_path)
            mappings = schema_info.get('mappings', {})
            date_col = schema_info.get('date_column', 'Date')
            
            def safe_int(val):
                try:
                    return int(float(str(val).replace(',','')))
                except:
                    return 0
            
            for index, row in df.iterrows():
                try:
                    date_str = str(row.get(date_col, ''))
                    date_obj = self._parse_date(date_str, schema_info.get('date_format'))
                    if not date_obj:
                        continue
                    
                    metric = LinkedInVisitorsMetric(
                        date=date_obj,
                        page_views=safe_int(row.get(mappings.get('page_views', 'Page views'), 0)),
                        unique_visitors=safe_int(row.get(mappings.get('unique_visitors', 'Unique visitors'), 0)),
                        raw_data=row.to_dict()  # Store full row for LLM access
                    )
                    self.store.linkedin_visitors.append(metric)
                except Exception as e:
                    continue
        except Exception as e:
            print(f"    ✗ Error processing visitors CSV: {e}")
    
    def _process_linkedin_csv_heuristic(self, csv_path: str, columns: List[str]):
        """Fallback: heuristic processing based on filename and columns"""
        filename = os.path.basename(csv_path).lower()
        
        # Content metrics file
        if 'content' in filename:
            self._process_linkedin_csv(csv_path, {
                'date_column': 'Date',
                'mappings': {
                    'impressions': 'Impressions (total)',
                    'clicks': 'Clicks (total)',
                    'reactions': 'Reactions (total)',
                    'engagement_rate': 'Engagement rate (total)'
                }
            })
        # Followers file - process with new model
        elif 'followers' in filename:
            self._process_linkedin_followers(csv_path, {
                'date_column': 'Date',
                'mappings': {
                    'sponsored_followers': 'Sponsored followers',
                    'organic_followers': 'Organic followers',
                    'total_followers': 'Total followers'
                }
            })
        # Visitors file - process with new model
        elif 'visitors' in filename:
            self._process_linkedin_visitors(csv_path, {
                'date_column': 'Date',
                'mappings': {
                    'page_views': 'Page views',
                    'unique_visitors': 'Unique visitors'
                }
            })
    
    def _parse_date(self, date_str: str, format_hint: Optional[str] = None) -> Optional[datetime]:
        """Parse date string with multiple format attempts"""
        if not date_str or str(date_str).lower() in ['nan', 'none', '']:
            return None
        
        # Try format hint first if provided (most reliable)
        if format_hint:
            try:
                return datetime.strptime(date_str, format_hint).date()
            except:
                pass
        
        # Try common formats
        for fmt in ['%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d', '%d-%m-%Y', '%Y/%m/%d']:
            try:
                return datetime.strptime(date_str, fmt).date()
            except:
                continue
        
        # Try pandas as last resort (with dayfirst for ambiguous formats)
        try:
            # If format looks like DD/MM/YYYY, use dayfirst
            if '/' in date_str and len(date_str.split('/')) == 3:
                return pd.to_datetime(date_str, dayfirst=True).date()
            return pd.to_datetime(date_str).date()
        except:
            pass
        
        return None

    def _load_website_data(self):
        """Load Website data from all CSV files using LLM for schema discovery"""
        website_dir = f"{self.data_dir}/src/data/website"
        if not os.path.exists(website_dir):
            print(f"✗ Website directory not found: {website_dir}")
            return
        
        # Discover all CSV files
        csv_files = glob.glob(f"{website_dir}/*.csv")
        print(f"  Found {len(csv_files)} CSV files")
        
        # Aggregate data from all files
        daily_metrics = {}  # date -> aggregated metrics
        
        for csv_path in csv_files:
            try:
                filename = os.path.basename(csv_path)
                print(f"  Processing: {filename}")
                
                # Read sample to understand structure
                df = pd.read_csv(csv_path, nrows=5)
                columns = list(df.columns)
                
                # Use LLM to understand schema
                schema_info = self._discover_website_csv_schema(csv_path, columns)
                
                if schema_info:
                    print(f"    → LLM identified: {schema_info.get('file_type', 'unknown')} file")
                    self._process_website_csv(csv_path, schema_info, daily_metrics)
                else:
                    # Fallback: heuristic processing
                    print(f"    → Using heuristic mapping")
                    self._process_website_csv_heuristic(csv_path, columns, daily_metrics)
                    
            except Exception as e:
                print(f"    ✗ Error processing {filename}: {e}")
                continue
        
        # Convert aggregated daily metrics to WebsiteMetric objects
        for date_obj, metrics in daily_metrics.items():
            metric = WebsiteMetric(
                date=date_obj,
                platform="website",
                page_views=metrics.get('page_views', 0),
                unique_visitors=metrics.get('unique_visitors', 0),
                bounce_rate=metrics.get('bounce_rate', 0.5)
            )
            self.store.website_metrics.append(metric)
        
        print(f"✓ Loaded {len(self.store.website_metrics)} Website records total")
    
    def _discover_website_csv_schema(self, filepath: str, columns: List[str]) -> Optional[Dict[str, Any]]:
        """Use LLM to discover website CSV schema"""
        try:
            df_sample = pd.read_csv(filepath, nrows=3)
            sample_data = df_sample.to_dict('records')
        except:
            sample_data = []
        
        context = f"""Analyze this website analytics CSV file and determine its schema.

File: {os.path.basename(filepath)}
Columns: {columns}
Sample rows: {json.dumps(sample_data, default=str)}

Our data model for WebsiteMetric requires:
- date: date field
- page_views: total page views
- unique_visitors: unique visitor count
- bounce_rate: bounce rate (0-1)

Task: Return JSON with:
{{
  "file_type": "daily_blog" | "traffic_report" | "sessions" | "other",
  "date_column": "column name for date or null if aggregate",
  "date_format": "format hint if needed",
  "mappings": {{
    "page_views": "column name or null",
    "unique_visitors": "column name or null",
    "bounce_rate": "column name or null"
  }},
  "aggregation_level": "daily" | "aggregate" | "country",
  "extraction_strategy": "how to extract/aggregate metrics"
}}"""
        
        return self._call_llm("Analyze the schema.", context)
    
    def _process_website_csv(self, csv_path: str, schema_info: Dict[str, Any], daily_metrics: Dict):
        """Process website CSV using LLM-discovered schema"""
        try:
            df = pd.read_csv(csv_path)
            mappings = schema_info.get('mappings', {})
            date_col = schema_info.get('date_column')
            agg_level = schema_info.get('aggregation_level', 'daily')
            
            def safe_int(val):
                try:
                    return int(float(str(val).replace(',','')))
                except:
                    return 0
            
            def safe_float(val):
                try:
                    return float(str(val).replace('%','')) / 100 if '%' in str(val) else float(val)
                except:
                    return 0.0
            
            if agg_level == 'daily' and date_col:
                # Daily time series data
                for _, row in df.iterrows():
                    try:
                        date_str = str(row.get(date_col, ''))
                        date_obj = self._parse_date(date_str, schema_info.get('date_format'))
                        if not date_obj:
                            continue
                        
                        page_views = safe_int(row.get(mappings.get('page_views', 'Page views'), 0))
                        unique_visitors = safe_int(row.get(mappings.get('unique_visitors', 'Unique visitors'), 0))
                        
                        if date_obj not in daily_metrics:
                            daily_metrics[date_obj] = {'page_views': 0, 'unique_visitors': 0, 'bounce_rate': 0.5}
                        
                        daily_metrics[date_obj]['page_views'] += page_views
                        daily_metrics[date_obj]['unique_visitors'] = max(
                            daily_metrics[date_obj]['unique_visitors'], unique_visitors
                        )
                        
                    except:
                        continue
            elif agg_level == 'aggregate':
                # Aggregate data - distribute across date range if we have LinkedIn dates
                if self.store.linkedin_metrics:
                    total_page_views = safe_int(df[mappings.get('page_views', 'Page views')].sum() if mappings.get('page_views') in df.columns else 0)
                    total_visitors = safe_int(df[mappings.get('unique_visitors', 'Unique visitors')].sum() if mappings.get('unique_visitors') in df.columns else 0)
                    
                    # Distribute across date range
                    start_date = min(m.date for m in self.store.linkedin_metrics)
                    end_date = max(m.date for m in self.store.linkedin_metrics)
                    days = (end_date - start_date).days + 1
                    
                    if days > 0:
                        daily_pv = total_page_views // days
                        daily_uv = total_visitors // days
                        
                        current_date = start_date
                        while current_date <= end_date:
                            if current_date not in daily_metrics:
                                daily_metrics[current_date] = {'page_views': 0, 'unique_visitors': 0, 'bounce_rate': 0.5}
                            daily_metrics[current_date]['page_views'] += daily_pv
                            daily_metrics[current_date]['unique_visitors'] = max(
                                daily_metrics[current_date]['unique_visitors'], daily_uv
                            )
                            current_date += timedelta(days=1)
                            
        except Exception as e:
            print(f"    ✗ Error processing CSV: {e}")
    
    def _process_website_csv_heuristic(self, csv_path: str, columns: List[str], daily_metrics: Dict):
        """Fallback: heuristic processing based on filename and columns"""
        filename = os.path.basename(csv_path).lower()
        
        if 'blog' in filename or 'post' in filename:
            # Daily blog metrics
            self._process_website_csv(csv_path, {
                'date_column': 'Action date',
                'aggregation_level': 'daily',
                'mappings': {
                    'page_views': 'Post views',
                    'unique_visitors': 'Unique visitors'
                }
            }, daily_metrics)
        elif 'traffic' in filename:
            # Aggregate traffic report
            self._process_website_csv(csv_path, {
                'date_column': None,
                'aggregation_level': 'aggregate',
                'mappings': {
                    'page_views': 'Page views',
                    'unique_visitors': 'Unique visitors'
                }
            }, daily_metrics)
        elif 'report' in filename or 'session' in filename:
            # Time series sessions
            self._process_website_csv(csv_path, {
                'date_column': 'Time period',
                'aggregation_level': 'daily',
                'mappings': {
                    'page_views': 'Site sessions',
                    'unique_visitors': 'Site sessions'
                }
            }, daily_metrics)

    def _generate_website_data_fallback(self):
        """Fallback: generate website data if loading fails"""
        if not self.store.linkedin_metrics:
            return
            
        start_date = min(m.date for m in self.store.linkedin_metrics)
        end_date = max(m.date for m in self.store.linkedin_metrics)
        
        current_date = start_date
        while current_date <= end_date:
            is_weekday = current_date.weekday() < 5
            
            if is_weekday:
                page_views = random.randint(500, 1500)
                unique_visitors = int(page_views * random.uniform(0.6, 0.8))
                bounce_rate = random.uniform(0.35, 0.55)
            else:
                page_views = random.randint(200, 600)
                unique_visitors = int(page_views * random.uniform(0.7, 0.85))
                bounce_rate = random.uniform(0.45, 0.65)
            
            metric = WebsiteMetric(
                date=current_date,
                platform="website",
                page_views=page_views,
                unique_visitors=unique_visitors,
                bounce_rate=bounce_rate
            )
            self.store.website_metrics.append(metric)
            current_date += timedelta(days=1)

    def _load_instagram_data(self):
        """Load Instagram data from all JSON files using LLM for schema discovery"""
        instagram_dir = f"{self.data_dir}/src/data/instagram"
        if not os.path.exists(instagram_dir):
            print(f"✗ Instagram directory not found: {instagram_dir}")
            return
        
        # Discover all JSON files
        json_files = glob.glob(f"{instagram_dir}/*.json")
        print(f"  Found {len(json_files)} JSON files")
        
        for json_path in json_files:
            try:
                filename = os.path.basename(json_path)
                print(f"  Processing: {filename}")
                
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Use LLM to understand JSON structure
                schema_info = self._discover_instagram_json_schema(json_path, data)
                
                if schema_info:
                    print(f"    → LLM identified: {schema_info.get('file_type', 'unknown')} file")
                    self._process_instagram_json(data, schema_info)
                else:
                    # Fallback: heuristic processing
                    print(f"    → Using heuristic mapping")
                    self._process_instagram_json_heuristic(data, filename)
                    
            except Exception as e:
                print(f"    ✗ Error processing {filename}: {e}")
                continue
        
        print(f"✓ Loaded {len(self.store.instagram_metrics)} Instagram post records")
        print(f"✓ Stored {len(self.store.instagram_audience_insights)} audience insights files")
        print(f"✓ Stored {len(self.store.instagram_content_interactions)} content interactions files")
        print(f"✓ Stored {len(self.store.instagram_live_videos)} live videos files")
        print(f"✓ Stored {len(self.store.instagram_profiles_reached)} profiles reached files")
    
    def _discover_instagram_json_schema(self, filepath: str, data: Dict) -> Optional[Dict[str, Any]]:
        """Use LLM to discover Instagram JSON schema"""
        # Sample first entry for context
        sample_entry = None
        top_level_keys = list(data.keys())
        
        if top_level_keys:
            first_key = top_level_keys[0]
            entries = data.get(first_key, [])
            if entries and len(entries) > 0:
                sample_entry = entries[0] if isinstance(entries, list) else entries
        
        context = f"""Analyze this Instagram JSON export file and determine its schema.

File: {os.path.basename(filepath)}
Top-level keys: {top_level_keys}
Sample entry structure: {json.dumps(sample_entry, default=str)[:500] if sample_entry else 'N/A'}

Our data model for InstagramMetric requires:
- date: date from timestamp
- impressions: total impressions
- likes: likes count
- comments: comments count
- shares: shares count
- engagement_rate: calculated from (likes + comments + shares) / impressions

Task: Return JSON with:
{{
  "file_type": "posts" | "audience" | "interactions" | "live_videos" | "profiles_reached" | "other",
  "data_key": "top-level key containing the data array",
  "timestamp_path": "path to timestamp (e.g., 'string_map_data.Creation timestamp.timestamp')",
  "metric_paths": {{
    "impressions": "path to impressions value",
    "likes": "path to likes value",
    "comments": "path to comments value",
    "shares": "path to shares value"
  }},
  "extraction_strategy": "how to extract daily metrics from this file type"
}}"""
        
        return self._call_llm("Analyze the schema.", context)
    
    def _process_instagram_json(self, data: Dict, schema_info: Dict[str, Any]):
        """Process Instagram JSON using LLM-discovered schema"""
        try:
            file_type = schema_info.get('file_type', 'other')
            
            # Handle unmapped file types by storing raw data
            if file_type == 'audience':
                insight = InstagramAudienceInsight(
                    date=None,  # May not have date
                    raw_data=data
                )
                self.store.instagram_audience_insights.append(insight)
                print(f"    → Stored audience insights data (raw JSON)")
                return
            elif file_type == 'interactions':
                interaction = InstagramContentInteraction(
                    date=None,
                    raw_data=data
                )
                self.store.instagram_content_interactions.append(interaction)
                print(f"    → Stored content interactions data (raw JSON)")
                return
            elif file_type == 'live_videos':
                video = InstagramLiveVideo(
                    date=None,
                    raw_data=data
                )
                self.store.instagram_live_videos.append(video)
                print(f"    → Stored live videos data (raw JSON)")
                return
            elif file_type == 'profiles_reached':
                reached = InstagramProfilesReached(
                    date=None,
                    raw_data=data
                )
                self.store.instagram_profiles_reached.append(reached)
                print(f"    → Stored profiles reached data (raw JSON)")
                return
            elif file_type != 'posts':
                print(f"    → Skipping {file_type} file (not mapped)")
                return
            
            # Process posts file (mapped to InstagramMetric)
            data_key = schema_info.get('data_key', 'organic_insights_posts')
            entries = data.get(data_key, [])
            
            if not isinstance(entries, list):
                entries = [entries] if entries else []
            
            timestamp_path = schema_info.get('timestamp_path', 'string_map_data.Creation timestamp.timestamp')
            metric_paths = schema_info.get('metric_paths', {})
            
            for entry in entries:
                try:
                    # Extract timestamp
                    timestamp = self._get_nested_value(entry, timestamp_path, 0)
                    if not timestamp:
                        continue
                    
                    date_obj = datetime.fromtimestamp(timestamp).date()
                    
                    # Extract metrics
                    impressions = int(self._get_nested_value(entry, metric_paths.get('impressions', 'string_map_data.Impressions.value'), '0'))
                    likes = int(self._get_nested_value(entry, metric_paths.get('likes', 'string_map_data.Likes.value'), '0'))
                    comments = int(self._get_nested_value(entry, metric_paths.get('comments', 'string_map_data.Comments.value'), '0'))
                    shares = int(self._get_nested_value(entry, metric_paths.get('shares', 'string_map_data.Shares.value'), '0'))
                    
                    # Calculate engagement rate
                    engagement_rate = (likes + comments + shares) / impressions if impressions > 0 else 0
                    
                    metric = InstagramMetric(
                        date=date_obj,
                        platform="instagram",
                        impressions=impressions,
                        likes=likes,
                        comments=comments,
                        shares=shares,
                        engagement_rate=engagement_rate
                    )
                    self.store.instagram_metrics.append(metric)
                    
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"    ✗ Error processing JSON: {e}")
    
    def _process_instagram_json_heuristic(self, data: Dict, filename: str):
        """Fallback: heuristic processing based on filename and structure"""
        filename_lower = filename.lower()
        
        if 'posts' in filename_lower:
            # Posts file - standard structure
            posts = data.get('organic_insights_posts', [])
            for post in posts:
                try:
                    string_data = post.get('string_map_data', {})
                    timestamp = string_data.get('Creation timestamp', {}).get('timestamp', 0)
                    if not timestamp:
                        continue
                    
                    date_obj = datetime.fromtimestamp(timestamp).date()
                    impressions = int(string_data.get('Impressions', {}).get('value', '0'))
                    likes = int(string_data.get('Likes', {}).get('value', '0'))
                    comments = int(string_data.get('Comments', {}).get('value', '0'))
                    shares = int(string_data.get('Shares', {}).get('value', '0'))
                    engagement_rate = (likes + comments + shares) / impressions if impressions > 0 else 0
                    
                    metric = InstagramMetric(
                        date=date_obj,
                        platform="instagram",
                        impressions=impressions,
                        likes=likes,
                        comments=comments,
                        shares=shares,
                        engagement_rate=engagement_rate
                    )
                    self.store.instagram_metrics.append(metric)
                except:
                    continue
        # Other file types (audience, interactions, etc.) are aggregate and don't map to daily metrics
        # Could be used for additional context but not for daily InstagramMetric records
    
    def _get_nested_value(self, obj: Any, path: str, default: Any = None) -> Any:
        """Get nested value from object using dot-notation path"""
        try:
            keys = path.split('.')
            value = obj
            for key in keys:
                if isinstance(value, dict):
                    value = value.get(key, default)
                elif isinstance(value, list) and key.isdigit():
                    value = value[int(key)] if int(key) < len(value) else default
                else:
                    return default
                if value is None:
                    return default
            return value
        except:
            return default
    
    def _generate_instagram_data_fallback(self):
        """Fallback: Generate synthetic Instagram metrics if real data unavailable"""
        if not self.store.linkedin_metrics:
            return
            
        start_date = min(m.date for m in self.store.linkedin_metrics)
        end_date = max(m.date for m in self.store.linkedin_metrics)
        
        current_date = start_date
        while current_date <= end_date:
            base_impressions = random.randint(800, 3000)
            is_reel_day = random.random() < 0.6
            
            if is_reel_day:
                likes = int(base_impressions * random.uniform(0.08, 0.15))
                comments = int(likes * random.uniform(0.05, 0.12))
                shares = int(likes * random.uniform(0.03, 0.08))
            else:
                likes = int(base_impressions * random.uniform(0.04, 0.08))
                comments = int(likes * random.uniform(0.03, 0.08))
                shares = int(likes * random.uniform(0.01, 0.04))
            
            engagement_rate = (likes + comments + shares) / base_impressions if base_impressions > 0 else 0
            
            metric = InstagramMetric(
                date=current_date,
                platform="instagram",
                impressions=base_impressions,
                likes=likes,
                comments=comments,
                shares=shares,
                engagement_rate=engagement_rate
            )
            self.store.instagram_metrics.append(metric)
            current_date += timedelta(days=1)
            
        print(f"✓ Generated {len(self.store.instagram_metrics)} Instagram records")

    def _load_competitors(self):
        """Load competitor list"""
        try:
            comp_path = f"{self.data_dir}/shorthills-ai_competitors.json"
            if os.path.exists(comp_path):
                with open(comp_path, "r") as f:
                    self.store.competitors = json.load(f)
                print(f"✓ Loaded {len(self.store.competitors)} competitors")
            else:
                # Try alternate location
                comp_path = f"{self.data_dir}/src/data/shorthills-ai_competitors.json"
                if os.path.exists(comp_path):
                    with open(comp_path, "r") as f:
                        self.store.competitors = json.load(f)
                    print(f"✓ Loaded {len(self.store.competitors)} competitors")
        except Exception as e:
            print(f"✗ Error loading competitors: {e}")

if __name__ == "__main__":
    # Get project root (parent of src/)
    import pathlib
    project_root = pathlib.Path(__file__).parent.parent.parent
    agent = IngestionAgent(str(project_root))
    data = agent.load_data()
    print(f"\n{'='*60}")
    print(f"Data Summary:")
    print(f"  LinkedIn: {len(data.linkedin_metrics)} records")
    print(f"  Instagram: {len(data.instagram_metrics)} records")
    print(f"  Website: {len(data.website_metrics)} records")
    print(f"{'='*60}")
    
    # Show sample data
    if data.linkedin_metrics:
        print(f"\nSample LinkedIn record:")
        sample = data.linkedin_metrics[0]
        print(f"  Date: {sample.date}, Impressions: {sample.impressions}, Engagement: {sample.engagement_rate:.2%}")
    
    if data.instagram_metrics:
        print(f"\nSample Instagram record:")
        sample = data.instagram_metrics[0]
        print(f"  Date: {sample.date}, Impressions: {sample.impressions}, Likes: {sample.likes}, Engagement: {sample.engagement_rate:.2%}")
    
    if data.website_metrics:
        print(f"\nSample Website record:")
        sample = data.website_metrics[0]
        print(f"  Date: {sample.date}, Page Views: {sample.page_views}, Visitors: {sample.unique_visitors}, Bounce: {sample.bounce_rate:.2%}")
