
import pandas as pd
import os

def convert_xls_to_csv(xls_path, csv_path):
    print(f"Converting {xls_path} to {csv_path}...")
    try:
        # Try reading with default engine (openpyxl for xlsx, xlrd for xls)
        # Since these are .xls, we might need xlrd. 
        # Sometimes .xls files are actually HTML or XML.
        try:
            df = pd.read_excel(xls_path)
        except Exception as e:
            print(f"Standard read_excel failed: {e}")
            # Try reading as HTML (common for some exports)
            try:
                dfs = pd.read_html(xls_path)
                df = dfs[0]
            except Exception as e2:
                print(f"HTML read failed: {e2}")
                raise e
        
        # Clean up header if needed (often row 1 is metadata)
        if 'Date' not in df.columns:
            # Look for the row that contains "Date"
            for i, row in df.iterrows():
                if row.astype(str).str.contains('Date').any():
                    print(f"Found header at row {i}")
                    df.columns = df.iloc[i]
                    df = df.iloc[i+1:]
                    break
        
        df.to_csv(csv_path, index=False)
        print(f"✓ Success: {csv_path}")
    except Exception as e:
        print(f"✗ Failed to convert {xls_path}: {e}")

base_dir = "/Users/shtlpmac084/sh-hackathon/agentic-1/src/data/linkedin"
files = [
    "shorthills-ai_content_1766385907708 1.xls",
    "shorthills-ai_followers_1766385928211 1.xls", 
    "shorthills-ai_visitors_1766385917155 1.xls"
]

for f in files:
    xls = os.path.join(base_dir, f)
    csv = os.path.join(base_dir, f.replace(".xls", ".csv"))
    convert_xls_to_csv(xls, csv)
