import pandas as pd
import json
import random
import os
from datetime import datetime, timedelta
from typing import List
from .models import DataStore, DailyMetric, InstagramMetric, WebsiteMetric

class IngestionAgent:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.store = DataStore()

    def load_data(self):
        """Load all data sources: LinkedIn (real), Website (real), Instagram (synthetic)"""
        print("Loading LinkedIn data...")
        self._load_linkedin_data()
        
        print("Loading Website data...")
        self._load_website_data()
        
        print("Generating Instagram synthetic data...")
        self._generate_instagram_data()
        
        print("Loading competitors...")
        self._load_competitors()
        
        return self.store

    def _load_linkedin_data(self):
        """Load real LinkedIn CSV data (converted from XLS)"""
        try:
            # Use the verified CSV file from conversion
            csv_path = f"{self.data_dir}/src/data/linkedin/shorthills-ai_content_1766385907708 1.csv"
            
            # Read CSV directly
            df = pd.read_csv(csv_path)
            print(f"DEBUG: Processing CSV with {len(df)} rows. Columns: {list(df.columns)}")
            
            count = 0
            for index, row in df.iterrows():
                try:
                    # Date parsing
                    date_str = str(row['Date'])
                    date_obj = None
                    try:
                        date_obj = pd.to_datetime(date_str).date()
                    except:
                        # Try standard formats
                        for fmt in ['%m/%d/%Y', '%Y-%m-%d', '%d/%m/%Y']:
                            try:
                                date_obj = datetime.strptime(date_str, fmt).date()
                                break
                            except:
                                continue
                    
                    if date_obj is None:
                        # print(f"DEBUG: Could not parse date: {date_str}")
                        continue

                    # Safe metric extraction
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

                    metric = DailyMetric(
                        date=date_obj,
                        platform="linkedin",
                        impressions=safe_int(row.get('Impressions (total)', 0)),
                        clicks=safe_int(row.get('Clicks (total)', 0)),
                        reactions=safe_int(row.get('Reactions (total)', 0)),
                        engagement_rate=safe_float(row.get('Engagement rate (total)', 0))
                    )
                    self.store.linkedin_metrics.append(metric)
                    count += 1
                except Exception as e:
                    print(f"Skipping row {index}: {e}")
                    continue
                    
            print(f"✓ Loaded {len(self.store.linkedin_metrics)} LinkedIn records")
        except Exception as e:
            print(f"✗ Error loading LinkedIn data: {e}")
            import traceback
            traceback.print_exc()
        except Exception as e:
            print(f"✗ Error loading LinkedIn data: {e}")
        except Exception as e:
            print(f"✗ Error loading LinkedIn data: {e}")
            print(f"   Trying alternate file...")
            # Try the CSV version as fallback
            try:
                csv_path = f"{self.data_dir}/src/data/linkedin/shorthills-ai_content_1766048688824(Metrics).csv"
                df = pd.read_csv(csv_path, skiprows=1)
                
                for _, row in df.iterrows():
                    try:
                        date_obj = datetime.strptime(row['Date'], '%m/%d/%Y').date()
                        metric = DailyMetric(
                            date=date_obj,
                            platform="linkedin",
                            impressions=int(row['Impressions (total)']),
                            clicks=int(row['Clicks (total)']),
                            reactions=int(row['Reactions (total)']),
                            engagement_rate=float(row['Engagement rate (total)'])
                        )
                        self.store.linkedin_metrics.append(metric)
                    except:
                        continue
                print(f"✓ Loaded {len(self.store.linkedin_metrics)} LinkedIn records (from CSV fallback)")
            except Exception as e2:
                print(f"✗ CSV fallback also failed: {e2}")

    def _load_website_data(self):
        """Load real Website analytics from src/data/website"""
        try:
            # Load blog metrics (daily post views)
            blog_path = f"{self.data_dir}/src/data/website/blog_table_api_2024-12-23-2025-12-23 1.csv"
            df_blog = pd.read_csv(blog_path)
            
            # Create date->metrics map
            blog_data = {}
            for _, row in df_blog.iterrows():
                try:
                    date_obj = datetime.strptime(row['Action date'], '%d/%m/%Y').date()
                    blog_data[date_obj] = {
                        'post_views': int(row['Post views']),
                        'unique_visitors': int(row['Unique visitors'])
                    }
                except:
                    continue
            
            # Load traffic report (aggregate stats)
            traffic_path = f"{self.data_dir}/src/data/website/Traffic report_2024-12-23-2025-12-23 1.csv"
            df_traffic = pd.read_csv(traffic_path)
            
            # Calculate total metrics from traffic
            total_page_views = sum([int(str(x).replace(',', '')) for x in df_traffic['Page views']])
            total_visitors = sum([int(str(x).replace(',', '')) for x in df_traffic['Unique visitors']])
            
            # Generate daily metrics based on blog data + distribute traffic data
            if blog_data:
                for date_obj, metrics in blog_data.items():
                    # Estimate bounce rate (inverse of engagement)
                    page_views = metrics['post_views']
                    visitors = metrics['unique_visitors']
                    bounce_rate = 1.0 - (page_views / max(visitors * 5, 1))  # Rough estimate
                    bounce_rate = max(0.3, min(0.8, bounce_rate))  # Constrain to realistic range
                    
                    metric = WebsiteMetric(
                        date=date_obj,
                        platform="website",
                        page_views=page_views * 10,  # Blog views are subset, scale up
                        unique_visitors=visitors * 8,
                        bounce_rate=bounce_rate
                    )
                    self.store.website_metrics.append(metric)
                    
            print(f"✓ Loaded {len(self.store.website_metrics)} Website records")
        except Exception as e:
            print(f"✗ Error loading Website data: {e}")
            # Fallback: generate based on LinkedIn date range
            if self.store.linkedin_metrics:
                print("   → Using estimated data based on LinkedIn date range")
                self._generate_website_data_fallback()

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

    def _generate_instagram_data(self):
        """Generate synthetic Instagram metrics"""
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
    agent = IngestionAgent("/Users/shtlpmac084/sh-hackathon/agentic-1")
    data = agent.load_data()
    print(f"\nData Summary:")
    print(f"  LinkedIn: {len(data.linkedin_metrics)} records")
    print(f"  Instagram: {len(data.instagram_metrics)} records")
    print(f"  Website: {len(data.website_metrics)} records")
