import streamlit as st
import pandas as pd
import plotly.express as px
import dashboard_utils as utils
from typing import Dict, Any
import re

# ===== AGENT INTEGRATION =====
# Our multi-agent system takes precedence - this loads REAL data
import streamlit_integration as agent_integration

# ===== Page Configuration =====
st.set_page_config(
    page_title="The Insight Room",
    page_icon="🐺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Theme & CSS System ---
def inject_custom_css():
    st.markdown("""
        <style>
        /* Import Fonts: Inter (UI) and Outfit (Headers) */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Outfit:wght@400;500;600;700&display=swap');

        :root {
            --bg-body: #F8FAFC;
            --bg-card: #FFFFFF;
            --text-primary: #0F172A;
            --text-secondary: #64748B;
            --accent-primary: #2563EB;
            --border-light: #E2E8F0;
        }

        /* Global Reset */
        .stApp {
            background-color: var(--bg-body);
            font-family: 'Inter', sans-serif;
            color: var(--text-primary);
        }
        
        h1, h2, h3, h4, h5 {
            font-family: 'Outfit', sans-serif;
            color: var(--text-primary);
            font-weight: 600 !important;
        }

        /* Top Bar Styling */
        .top-bar-container {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--border-light);
            margin-bottom: 30px;
        }
        .page-title {
            font-size: 1.8rem;
            font-weight: 700;
            margin: 0;
            color: #1E293B;
        }
        .page-subtext {
            font-size: 0.95rem;
            color: var(--text-secondary);
            margin-top: 5px;
        }

        /* KPI Cards */
        .kpi-card {
            background: var(--bg-card);
            border: 1px solid var(--border-light);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            transition: transform 0.2s;
        }
        .kpi-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }
        .kpi-label {
            font-size: 0.85rem;
            color: var(--text-secondary);
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .kpi-value {
            font-size: 1.8rem;
            font-weight: 700;
            color: var(--text-primary);
            margin: 8px 0;
        }
        .kpi-trend {
            font-size: 0.85rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 4px;
        }
        .trend-up { color: #10B981; }
        .trend-down { color: #EF4444; }
        .trend-neutral { color: #64748B; }

        /* Insight & Recommendation Cards */
        .content-card {
            background: var(--bg-card);
            border: 1px solid var(--border-light);
            border-radius: 12px;
            padding: 24px;
            height: 100%;
            box-shadow: 0 1px 3px rgba(0,0,0,0.02);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        .card-header-row {
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 12px;
        }
        .card-main-title {
            font-family: 'Outfit', sans-serif;
            font-weight: 600;
            font-size: 1.1rem;
            line-height: 1.4;
            color: #1E293B;
        }
        .card-body-text {
            font-size: 0.95rem;
            color: #475569;
            line-height: 1.6;
            margin-bottom: 16px;
        }

        /* Confidence Badges */
        .badge {
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .badge-high { background-color: #ECFDF5; color: #047857; border: 1px solid #D1FAE5; }
        .badge-medium { background-color: #FFFBEB; color: #B45309; border: 1px solid #FEF3C7; }

        /* Input Panel */
        .input-panel {
            background: #F1F5F9;
            border: 1px solid var(--border-light);
            border-radius: 8px;
            padding: 20px;
            margin-top: 30px;
        }

        /* Hide Streamlit components */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stDeployButton {display:none;}
        
        /* Sidebar Styling fixes */
        [data-testid="stSidebar"] {
            background-color: #FFFFFF;
            border-right: 1px solid #E2E8F0;
        }

        /* Fix Streamlit Tabs */
        button[data-baseweb="tab"] {
            color: #64748B !important; /* text-secondary */
            font-weight: 600;
            background-color: transparent !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            color: #2563EB !important; /* accent-primary */
            border-bottom-color: #2563EB !important;
        }
        button[data-baseweb="tab"] div {
            color: inherit !important;
        }
        
        /* Info messages - make wrapper transparent, style only notification component */
        .stInfo {
            background-color: transparent !important;
            border: none !important;
            padding: 0 !important;
            margin: 0 !important;
            box-shadow: none !important;
        }
        /* Style only the actual notification component */
        [data-baseweb="notification"][kind="info"],
        .stInfo [data-baseweb="notification"][kind="info"] {
            background-color: #EFF6FF !important;
            border-left: 4px solid #2563EB !important;
            border-right: none !important;
            border-top: none !important;
            border-bottom: none !important;
            border-radius: 4px !important;
            color: #0F172A !important;
            padding: 1rem !important;
        }
        /* Remove all styling from wrapper divs to prevent double boxes */
        .stInfo > div,
        .stInfo > div > div,
        .stInfo [data-baseweb="notification"] > div,
        .stInfo [data-baseweb="notification"] > div > div,
        [data-baseweb="notification"][kind="info"] > div,
        [data-baseweb="notification"][kind="info"] > div > div {
            border: none !important;
            background-color: transparent !important;
            box-shadow: none !important;
            padding: 0 !important;
            margin: 0 !important;
        }
        .stInfo p,
        .stInfo span,
        .stInfo * {
            color: #0F172A !important;
        }
        
        /* Warning messages - make wrapper transparent, style only notification component */
        .stWarning {
            background-color: transparent !important;
            border: none !important;
            padding: 0 !important;
            margin: 0 !important;
            box-shadow: none !important;
        }
        /* Style only the actual notification component */
        [data-baseweb="notification"][kind="warning"],
        .stWarning [data-baseweb="notification"][kind="warning"] {
            background-color: #FFFBEB !important;
            border-left: 4px solid #F59E0B !important;
            border-right: none !important;
            border-top: none !important;
            border-bottom: none !important;
            border-radius: 4px !important;
            color: #0F172A !important;
            padding: 1rem !important;
        }
        /* Remove all styling from wrapper divs to prevent double boxes */
        .stWarning > div,
        .stWarning > div > div,
        .stWarning [data-baseweb="notification"] > div,
        .stWarning [data-baseweb="notification"] > div > div,
        [data-baseweb="notification"][kind="warning"] > div,
        [data-baseweb="notification"][kind="warning"] > div > div {
            border: none !important;
            background-color: transparent !important;
            box-shadow: none !important;
            padding: 0 !important;
            margin: 0 !important;
        }
        .stWarning p,
        .stWarning span,
        .stWarning * {
            color: #0F172A !important;
        }

        /* Sidebar Title and Text Visibility */
        [data-testid="stSidebar"] h3 {
            color: #0F172A !important;
            font-family: 'Outfit', sans-serif;
            font-weight: 600;
        }
        [data-testid="stSidebar"] .element-container {
            color: #0F172A;
        }

        /* Sidebar Menu Radio Button Styling */
        [data-testid="stSidebar"] label[data-baseweb="radio"] {
            background-color: transparent;
            padding: 12px 16px;
            border-radius: 8px;
            transition: background-color 0.2s;
            font-weight: 500;
            color: #475569 !important;
        }
        [data-testid="stSidebar"] label[data-baseweb="radio"]:hover {
            background-color: #F8FAFC;
        }
        [data-testid="stSidebar"] label[data-baseweb="radio"] input:checked + div {
            background-color: #EEF2FF !important;
            color: #2563EB !important;
            font-weight: 600 !important;
        }
        
        /* Button Styling - Black Text for Primary Buttons */
        button[kind="primary"],
        button[data-baseweb="button"][kind="primary"],
        .stButton > button[kind="primary"],
        div[data-testid="stButton"] > button[kind="primary"],
        [data-testid="stButton"] button[kind="primary"] {
            color: #000000 !important;
            font-weight: 600 !important;
        }
        button[kind="primary"]:hover,
        button[data-baseweb="button"][kind="primary"]:hover,
        .stButton > button[kind="primary"]:hover,
        div[data-testid="stButton"] > button[kind="primary"]:hover {
            color: #000000 !important;
        }
        /* Ensure text is visible in sidebar buttons too */
        [data-testid="stSidebar"] button[kind="primary"],
        [data-testid="stSidebar"] .stButton > button[kind="primary"] {
            color: #000000 !important;
            font-weight: 600 !important;
        }
        
        /* Global Text Color Enforcement - Black or Grey Only */
        
        /* All markdown text - Black */
        .stMarkdown,
        .stMarkdown p,
        .stMarkdown li,
        .stMarkdown ul,
        .stMarkdown ol,
        .stMarkdown h1,
        .stMarkdown h2,
        .stMarkdown h3,
        .stMarkdown h4,
        .stMarkdown h5,
        .stMarkdown h6 {
            color: #0F172A !important; /* Black */
        }
        
        /* Captions and helper text - Grey */
        .stCaption,
        [data-testid="stCaption"],
        small {
            color: #64748B !important; /* Grey */
        }
        
        /* All form labels - Black */
        label,
        [data-baseweb="form-control"] label,
        [data-baseweb="select"] label,
        [data-baseweb="input"] label,
        .stSelectbox label,
        .stMultiselect label,
        .stTextInput label,
        .stTextArea label,
        .stNumberInput label,
        .stDateInput label,
        .stTimeInput label,
        [data-baseweb="label"] {
            color: #0F172A !important; /* Black */
        }
        
        /* Input text values - Black */
        input[type="text"],
        input[type="number"],
        input[type="date"],
        input[type="time"],
        textarea,
        select {
            color: #0F172A !important; /* Black */
        }
        
        /* Metric labels and values - Black */
        [data-testid="stMetricLabel"],
        [data-testid="stMetricValue"],
        [data-testid="stMetricDelta"] {
            color: #0F172A !important; /* Black */
        }
        
        /* Success and Error messages - Black text */
        .stAlert,
        [data-baseweb="notification"][kind="success"],
        [data-baseweb="notification"][kind="error"],
        .stSuccess,
        .stError {
            color: #0F172A !important; /* Black */
        }
        .stSuccess > div,
        .stError > div {
            color: #0F172A !important; /* Black */
        }
        
        /* Expander styling - white background with black text */
        [data-baseweb="accordion"],
        [data-baseweb="accordion"] > div,
        [data-baseweb="accordion"] > div > div,
        .streamlit-expanderHeader,
        .streamlit-expanderContent {
            background-color: #FFFFFF !important;
            color: #0F172A !important; /* Black text */
            border: 1px solid #E2E8F0 !important;
            border-radius: 8px !important;
        }
        
        /* Table text - Black */
        table,
        .stDataFrame,
        [data-testid="stDataFrame"] {
            color: #0F172A !important; /* Black */
        }
        table td,
        table th {
            color: #0F172A !important; /* Black */
        }
        
        /* JSON viewer text - Black */
        .stJson {
            color: #0F172A !important; /* Black */
        }
        
        /* All headings - Black */
        h1, h2, h3, h4, h5, h6 {
            color: #0F172A !important; /* Black */
        }
        
        /* List items - Black */
        li, ul, ol {
            color: #0F172A !important; /* Black */
        }
        
        /* Paragraphs - Black */
        p {
            color: #0F172A !important; /* Black */
        }
        
        /* Code blocks - Black text on light background */
        code,
        pre {
            color: #0F172A !important; /* Black */
            background-color: #F1F5F9 !important; /* Light grey background */
        }
        
        /* Links - Keep blue for visibility */
        a {
            color: #2563EB !important; /* Blue for links */
        }
        a:visited {
            color: #2563EB !important;
        }
        
        /* Spinner text - Black */
        .stSpinner {
            color: #0F172A !important; /* Black */
        }
        
        /* Progress bar text - Black */
        [data-baseweb="progress-bar"] {
            color: #0F172A !important; /* Black */
        }
        
        /* Status component styling - ensure visibility with light background */
        [data-testid="stStatus"],
        [data-baseweb="notification"],
        [data-baseweb="notification"] > div,
        div[data-testid="stStatus"] {
            background-color: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 8px !important;
            padding: 16px !important;
        }
        
        /* Status component container - force white background */
        div[data-testid="stStatus"],
        div[data-testid="stStatus"] > div,
        div[data-testid="stStatus"] > div > div {
            background-color: #FFFFFF !important;
        }
        
        /* Status component - force white background everywhere - HIGH PRIORITY */
        div[data-testid="stStatus"],
        [data-testid="stStatus"],
        [data-testid="stStatus"] > div,
        [data-testid="stStatus"] > div > div,
        [data-testid="stStatus"] > div > div > button,
        [data-testid="stStatus"] button,
        [data-testid="stStatus"] > button,
        [data-testid="stStatus"] [data-baseweb="button"],
        [data-baseweb="notification"],
        [data-baseweb="notification"] > div,
        [data-baseweb="notification"] button,
        [data-baseweb="notification"] > button,
        [data-baseweb="notification"] [data-baseweb="button"] {
            background-color: #FFFFFF !important;
            color: #0F172A !important;
        }
        
        /* Status component header/button - white background with visible text - SPECIFIC TARGETING */
        [data-testid="stStatus"] button,
        [data-testid="stStatus"] > div > button,
        [data-testid="stStatus"] > div > div > button,
        [data-testid="stStatus"] [data-baseweb="button"],
        [data-testid="stStatus"] [role="button"],
        [data-baseweb="notification"] button,
        [data-baseweb="notification"] > button,
        [data-baseweb="notification"] [data-baseweb="button"] {
            background-color: #FFFFFF !important;
            color: #0F172A !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 8px !important;
            padding: 12px 16px !important;
            font-weight: 600 !important;
        }
        
        /* Status component button text - ensure black text */
        [data-testid="stStatus"] button *,
        [data-testid="stStatus"] button span,
        [data-testid="stStatus"] button div,
        [data-testid="stStatus"] button p,
        [data-testid="stStatus"] button label {
            color: #0F172A !important;
            background-color: transparent !important;
        }
        
        /* Status component text content */
        [data-testid="stStatus"] span,
        [data-testid="stStatus"] div,
        [data-testid="stStatus"] p,
        [data-testid="stStatus"] label,
        [data-baseweb="notification"] span,
        [data-baseweb="notification"] div,
        [data-baseweb="notification"] p,
        [data-baseweb="notification"] label {
            color: #0F172A !important;
            background-color: transparent !important;
        }
        
        /* Status component header text specifically */
        [data-testid="stStatus"] button span,
        [data-testid="stStatus"] button div,
        [data-testid="stStatus"] button label,
        [data-testid="stStatus"] button *,
        [data-baseweb="notification"] button span,
        [data-baseweb="notification"] button div,
        [data-baseweb="notification"] button label,
        [data-baseweb="notification"] button * {
            color: #0F172A !important;
            background-color: transparent !important;
        }
        
        /* Status component text and labels - ensure black text on white background */
        [data-testid="stStatus"] label,
        [data-testid="stStatus"] div,
        [data-testid="stStatus"] p,
        [data-testid="stStatus"] span,
        [data-testid="stStatus"] *:not(button),
        [data-baseweb="notification"] label,
        [data-baseweb="notification"] div,
        [data-baseweb="notification"] p,
        [data-baseweb="notification"] span,
        [data-baseweb="notification"] *:not(button) {
            color: #0F172A !important;
            background-color: transparent !important;
        }
        
        /* Status component spinner/icon - blue when running */
        [data-testid="stStatus"] svg,
        [data-baseweb="notification"] svg {
            color: #2563EB !important;
        }
        
        /* Status component header button hover state */
        [data-testid="stStatus"] button:hover,
        [data-baseweb="notification"] button:hover {
            background-color: #F8FAFC !important;
            color: #0F172A !important;
        }
        
        /* Status component when running - blue accent */
        [data-testid="stStatus"][aria-label*="Progress"],
        [data-testid="stStatus"][aria-label*="Progress"] * {
            color: #0F172A !important;
        }
        
        /* Additional targeting for status component accordion/expandable header */
        [data-testid="stStatus"] [role="button"],
        [data-testid="stStatus"] [data-baseweb="button"][role="button"],
        [data-baseweb="notification"] [role="button"] {
            background-color: #FFFFFF !important;
            color: #0F172A !important;
        }
        
        /* Status component summary/header element */
        [data-testid="stStatus"] summary,
        [data-testid="stStatus"] summary *,
        [data-baseweb="notification"] summary,
        [data-baseweb="notification"] summary * {
            background-color: #FFFFFF !important;
            color: #0F172A !important;
            font-weight: 600 !important;
        }
        
        /* Status component - UNIVERSAL TARGETING for header - force white background and black text */
        [data-testid="stStatus"] *,
        [data-testid="stStatus"] > *,
        [data-testid="stStatus"] > * > *,
        [data-testid="stStatus"] > * > * > * {
            background-color: #FFFFFF !important;
            color: #0F172A !important;
        }
        
        /* Status component header button specifically - AGGRESSIVE TARGETING */
        [data-testid="stStatus"] > div:first-child,
        [data-testid="stStatus"] > div:first-child > button,
        [data-testid="stStatus"] > div:first-child > div,
        [data-testid="stStatus"] > div:first-child > div > button,
        [data-testid="stStatus"] > div:first-child > div > span,
        [data-testid="stStatus"] > div:first-child > div > div,
        [data-testid="stStatus"] > div:first-child > div > div > span,
        [data-testid="stStatus"] > div:first-child > div > div > div,
        [data-testid="stStatus"] > div:first-child > div > div > div > span,
        [data-testid="stStatus"] label,
        [data-testid="stStatus"] > label,
        [data-testid="stStatus"] button[aria-expanded],
        [data-testid="stStatus"] button[aria-expanded] *,
        [data-testid="stStatus"] button[aria-expanded] span,
        [data-testid="stStatus"] button[aria-expanded] div {
            background-color: #FFFFFF !important;
            color: #0F172A !important;
            font-weight: 600 !important;
        }
        
        /* Status component - target all possible nested structures for header */
        [data-testid="stStatus"] button,
        [data-testid="stStatus"] button > *,
        [data-testid="stStatus"] button > * > *,
        [data-testid="stStatus"] button > * > * > *,
        [data-testid="stStatus"] [data-baseweb="button"],
        [data-testid="stStatus"] [data-baseweb="button"] > *,
        [data-testid="stStatus"] [data-baseweb="button"] > * > * {
            background-color: #FFFFFF !important;
            color: #0F172A !important;
        }
        
        /* CRITICAL: Status header text visibility - highest priority */
        div[data-testid="stStatus"] button,
        div[data-testid="stStatus"] button *,
        div[data-testid="stStatus"] button span,
        div[data-testid="stStatus"] button div,
        div[data-testid="stStatus"] button p,
        div[data-testid="stStatus"] button label,
        div[data-testid="stStatus"] > div > button,
        div[data-testid="stStatus"] > div > button *,
        div[data-testid="stStatus"] > div > button span,
        div[data-testid="stStatus"] > div > button div {
            background-color: #FFFFFF !important;
            background: #FFFFFF !important;
            color: #0F172A !important;
            font-weight: 600 !important;
        }
        
        /* Override any dark theme styles for status component */
        [data-testid="stStatus"],
        [data-testid="stStatus"] * {
            background-color: #FFFFFF !important;
            background: #FFFFFF !important;
        }
        
        /* Ensure text is always black/visible on white background */
        [data-testid="stStatus"],
        [data-testid="stStatus"] * {
            color: #0F172A !important;
        }
        
        /* Status component content area - ensure logs are visible */
        [data-testid="stStatus"] > div:last-child,
        [data-testid="stStatus"] > div:last-child > div,
        [data-testid="stStatus"] > div:last-child *,
        [data-testid="stStatus"] [class*="status"],
        [data-testid="stStatus"] [class*="Status"],
        [data-testid="stStatus"] pre,
        [data-testid="stStatus"] code,
        [data-testid="stStatus"] p {
            background-color: #FFFFFF !important;
            color: #0F172A !important;
        }
        
        /* Status component when complete - green accent */
        [data-testid="stStatus"][aria-label*="complete"],
        [data-testid="stStatus"][aria-label*="complete"] *,
        [data-testid="stStatus"][aria-label*="completed"],
        [data-testid="stStatus"][aria-label*="completed"] * {
            color: #0F172A !important;
        }
        
        /* Status component when error - red accent */
        [data-testid="stStatus"][aria-label*="error"],
        [data-testid="stStatus"][aria-label*="error"] *,
        [data-testid="stStatus"][aria-label*="failed"],
        [data-testid="stStatus"][aria-label*="failed"] * {
            color: #0F172A !important;
        }
        
        /* Chat messages - Black text */
        .stChatMessage {
            color: #0F172A !important; /* Black */
        }
        .stChatMessage p,
        .stChatMessage div,
        .stChatMessage span,
        .stChatMessage * {
            color: #0F172A !important; /* Black */
        }
        /* Chat input - Black text */
        [data-testid="stChatInput"] input,
        [data-testid="stChatInput"] textarea,
        [data-testid="stChatInput"] * {
            color: #0F172A !important; /* Black */
        }
        /* Expander header and content - white background with black text */
        [data-baseweb="accordion"] button,
        [data-baseweb="accordion"] summary,
        [data-baseweb="accordion"] > div > button,
        [data-baseweb="accordion"] > div > div > button,
        .streamlit-expanderHeader,
        .streamlit-expanderHeader *,
        .streamlit-expanderContent,
        .streamlit-expanderContent * {
            background-color: #FFFFFF !important;
            color: #0F172A !important; /* Black text */
        }
        
        /* Expander header button - ensure white background */
        [data-baseweb="accordion"] button,
        [data-baseweb="accordion"] > div > button,
        [data-baseweb="accordion"] > div > div > button,
        .streamlit-expanderHeader button,
        .streamlit-expanderHeader [role="button"] {
            background-color: #FFFFFF !important;
            color: #0F172A !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 8px !important;
            padding: 12px 16px !important;
        }
        
        /* Expander content area - white background */
        [data-baseweb="accordion"] > div:last-child,
        [data-baseweb="accordion"] > div > div:last-child,
        .streamlit-expanderContent,
        .streamlit-expanderContent > div {
            background-color: #FFFFFF !important;
            color: #0F172A !important;
            padding: 16px !important;
        }
        
        /* Expander hover state */
        [data-baseweb="accordion"] button:hover,
        .streamlit-expanderHeader button:hover {
            background-color: #F8FAFC !important;
            color: #0F172A !important;
        }
        /* Chat message avatars and containers */
        [data-testid="stChatMessage"] * {
            color: #0F172A !important;
        }
        /* Ensure chat input placeholder is visible but not too dark */
        [data-testid="stChatInput"] input::placeholder {
            color: #64748B !important; /* Grey for placeholder */
        }
        
        /* Sidebar text - Black (captions already handled above as grey) */
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] div:not(.stCaption):not(small) {
            color: #0F172A !important; /* Black */
        }
        
        /* Streamlit element containers - ensure text is black */
        .element-container {
            color: #0F172A !important; /* Black */
        }
        
        /* Override any potential white text in Streamlit widgets */
        [data-baseweb="text"],
        [data-baseweb="text"] * {
            color: #0F172A !important; /* Black */
        }
        
        /* Sidebar expand/collapse buttons - make visible */
        [data-testid="stSidebar"] button[aria-label*="Close"],
        [data-testid="stSidebar"] button[aria-label*="Open"],
        [data-testid="stSidebar"] button[aria-label*="Expand"],
        [data-testid="stSidebar"] button[aria-label*="Collapse"],
        button[kind="header"] {
            background-color: #FFFFFF !important;
            color: #0F172A !important;
            border: 1px solid #E2E8F0 !important;
        }
        
        /* Multiselect and selectbox - white background */
        [data-baseweb="select"],
        [data-baseweb="select"] input,
        [data-baseweb="select"] div,
        [data-baseweb="select"] button,
        [data-baseweb="select"] span,
        [data-baseweb="select"] *,
        [data-baseweb="multiselect"],
        [data-baseweb="multiselect"] input,
        [data-baseweb="multiselect"] div,
        [data-baseweb="multiselect"] button,
        [data-baseweb="multiselect"] span,
        [data-baseweb="multiselect"] *,
        .stSelectbox,
        .stSelectbox > div,
        .stSelectbox > div > div,
        .stSelectbox > div > div > div,
        .stSelectbox button,
        .stSelectbox [data-baseweb="select"],
        .stMultiselect,
        .stMultiselect > div,
        .stMultiselect > div > div,
        .stMultiselect > div > div > div,
        .stMultiselect button,
        .stMultiselect [data-baseweb="multiselect"],
        [data-baseweb="popover"],
        [data-baseweb="popover"] * {
            background-color: #FFFFFF !important;
            color: #0F172A !important;
        }
        
        /* Selectbox dropdown options */
        [data-baseweb="menu"],
        [data-baseweb="menu"] li,
        [data-baseweb="menu"] ul,
        [data-baseweb="menu"] *,
        [role="listbox"],
        [role="listbox"] *,
        [role="option"] {
            background-color: #FFFFFF !important;
            color: #0F172A !important;
        }
        
        /* Multiselect tags/chips */
        [data-baseweb="tag"],
        [data-baseweb="tag"] * {
            background-color: #F1F5F9 !important;
            color: #0F172A !important;
        }
        
        /* Dropdown arrow icons */
        [data-baseweb="select"] svg,
        [data-baseweb="multiselect"] svg {
            color: #0F172A !important;
        }
        
        /* Download button - ensure visible with proper styling */
        [data-testid="stDownloadButton"] button,
        .stDownloadButton button,
        button[data-testid="baseButton-secondary"] {
            background-color: #2563EB !important;
            color: #FFFFFF !important;
            border: 1px solid #2563EB !important;
        }
        
        /* Download button hover */
        [data-testid="stDownloadButton"] button:hover,
        .stDownloadButton button:hover {
            background-color: #1D4ED8 !important;
            color: #FFFFFF !important;
        }
        
        /* Secondary buttons (like Clear Chat) - ensure visible */
        button[kind="secondary"],
        [data-baseweb="button"][kind="secondary"],
        .stButton > button[kind="secondary"],
        div[data-testid="stButton"] > button[kind="secondary"],
        [data-testid="stButton"] button[kind="secondary"] {
            background-color: #F1F5F9 !important;
            color: #0F172A !important;
            border: 1px solid #E2E8F0 !important;
            font-weight: 500 !important;
        }
        
        button[kind="secondary"]:hover,
        [data-baseweb="button"][kind="secondary"]:hover,
        .stButton > button[kind="secondary"]:hover {
            background-color: #E2E8F0 !important;
            color: #0F172A !important;
        }
        
        /* Chat input - white background */
        [data-testid="stChatInput"] input,
        [data-testid="stChatInput"] textarea {
            background-color: #FFFFFF !important;
            color: #0F172A !important;
            border: 1px solid #E2E8F0 !important;
        }
        
        /* Tooltip styling */
        .tooltip-icon {
            display: inline-block;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background-color: #2563EB;
            color: #FFFFFF;
            text-align: center;
            line-height: 16px;
            font-size: 12px;
            font-weight: bold;
            cursor: help;
            margin-left: 4px;
            vertical-align: middle;
        }
        </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# ===== LOAD AGENT DATA (On-demand) =====
def init_agents(status_writer=None):
    """Initialize all agents and load real data"""
    try:
        return agent_integration.load_agent_data(status_writer=status_writer)
    except Exception as e:
        st.error(f"Agent initialization failed: {e}")
        return None

# Initialize session state for agent data
if 'agent_data' not in st.session_state:
    st.session_state.agent_data = None
if 'ingestion_in_progress' not in st.session_state:
    st.session_state.ingestion_in_progress = False
if 'ingestion_started' not in st.session_state:
    st.session_state.ingestion_started = False
if 'ingestion_completed' not in st.session_state:
    st.session_state.ingestion_completed = False

# Get agent data from session state
agent_data = st.session_state.agent_data

# --- Sidebar Navigation ---
with st.sidebar:
    # Updated 2025-12-31 deprecation fix
    st.image("logo.png")
    st.markdown("### 🐺 The Insight Room")
    st.markdown("---")
    
    # Navigation Menu
    menu_options = [
        "Dashboard", 
        "Marketing", 
        "Reports"
    ]
    
    selected_menu = st.radio("Navigation", menu_options, index=0, label_visibility="collapsed")
    
    st.markdown("---")
    st.caption("Data Status")
    
    if agent_data and agent_data.get('store'):
        store = agent_data['store']
        n_li = len(store.linkedin_metrics)
        n_ig = len(store.instagram_metrics)
        n_web = len(store.website_metrics)
        
        st.success(f"LinkedIn ({n_li} records)")
        st.success(f"Instagram ({n_ig} records)")
        st.success(f"Website ({n_web} records)")
    elif st.session_state.ingestion_in_progress:
        st.info("Loading data...")
    else:
        st.warning("No data loaded")
        st.markdown("---")
        if st.button("Load Data", type="primary", use_container_width=True):
            # Reset ingestion flags when user explicitly clicks Load Data
            st.session_state.ingestion_in_progress = True
            st.session_state.ingestion_started = False
            st.session_state.ingestion_completed = False
            st.session_state.agent_data = None  # Clear old data
            st.rerun()
        
    st.markdown("---")
    # st.markdown("**Version 1.2.1 (Enterprise)**")

# --- Main Header ---
col_head_main, col_head_user = st.columns([3, 1])

with col_head_main:
    st.markdown('<div class="page-title">Marketing Overview</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtext">Insights generated from marketing channels - LinkedIn, Instagram, and Website.</div>', unsafe_allow_html=True)

with col_head_user:
    # Clean header area
    st.markdown("")

st.markdown("---")

# Handle ingestion if button was clicked
# Add a guard to prevent duplicate ingestion runs
if st.session_state.ingestion_in_progress and st.session_state.agent_data is None:
    # Check if ingestion is already running (prevent duplicate calls)
    # Only start ingestion if it hasn't been started yet in this session
    if not st.session_state.get('ingestion_started', False):
        st.session_state.ingestion_started = True
        
        try:
            # Initialize status_writer outside the with block so it's accessible later
            status_writer = None
            
            # Use st.status() for better progress visibility
            with st.status("📊 Data Ingestion in Progress...", expanded=True) as status:
                # Create status writer that will accumulate messages
                status_writer = agent_integration.StreamlitStatusWriter(status)
                
                # Load data (this does all the work via OrchestratorAgent)
                # Messages will be written to status container as they come in
                agent_data = init_agents(status_writer=status_writer)
                
                # Update status to show completion
                if agent_data and agent_data.get('store'):
                    status.update(label="✅ Data ingestion completed!", state="complete")
                else:
                    status.update(label="❌ Data ingestion failed", state="error")
            
            # Show detailed logs below the status - always show during and after execution
            # Logs should appear both in the status component (when it exits) and in the expander
            if status_writer and hasattr(status_writer, 'messages') and len(status_writer.messages) > 0:
                with st.expander("📋 Detailed Progress Log", expanded=True):
                    message_text = "\n".join(status_writer.messages)
                    st.text_area(
                        "Execution Log:",
                        value=message_text,
                        height=min(400, max(200, len(status_writer.messages) * 20)),
                        disabled=True,
                        label_visibility="collapsed"
                    )
            elif status_writer:
                # If status_writer exists but no messages, show a message
                st.info("No progress logs available. Check console for details.")
            
            # Show execution summary
            if agent_data and agent_data.get('store'):
                store = agent_data['store']
                st.success("**Files processed successfully:**")
                
                # Show record counts
                record_info = f"""
                - LinkedIn: {len(store.linkedin_metrics)} records loaded
                - Instagram: {len(store.instagram_metrics)} records loaded
                - Website: {len(store.website_metrics)} records loaded
                """
                
                # Show execution summary if available
                exec_summary = agent_data.get('execution_summary', {})
                if exec_summary and 'platform_agents' in exec_summary:
                    platform_agents = exec_summary['platform_agents']
                    record_info += "\n**Agent Execution Status:**\n"
                    for platform, status_info in platform_agents.items():
                        status_icon = "✓" if status_info['status'] == 'success' else "✗"
                        record_info += f"- {status_icon} {platform.capitalize()}: {status_info['status']}\n"
                
                st.markdown(record_info)
                
                # Show token usage and cost in a dedicated expander
                exec_summary = agent_data.get('execution_summary', {})
                if exec_summary and 'token_usage' in exec_summary:
                    token_usage = exec_summary['token_usage']
                    if token_usage and token_usage.get('total_calls', 0) > 0:
                        # Print to console for logging
                        print("\n" + "="*70)
                        print("💰 TOKEN USAGE & COST SUMMARY")
                        print("="*70)
                        print(f"Total LLM Calls: {token_usage.get('total_calls', 0)}")
                        print(f"Total Tokens: {token_usage.get('total_tokens', 0):,}")
                        print(f"Prompt Tokens: {token_usage.get('total_prompt_tokens', 0):,}")
                        print(f"Completion Tokens: {token_usage.get('total_completion_tokens', 0):,}")
                        print(f"Total Cost: ${token_usage.get('total_cost', 0.0):.4f}")
                        
                        if token_usage.get('by_agent'):
                            print("\nBreakdown by Agent:")
                            print("-" * 70)
                            for agent, metrics in token_usage['by_agent'].items():
                                if metrics.get('calls', 0) > 0:
                                    print(f"  {agent}:")
                                    print(f"    Calls: {metrics.get('calls', 0)}")
                                    print(f"    Tokens: {metrics.get('tokens', 0):,}")
                                    print(f"    Cost: ${metrics.get('cost', 0.0):.4f}")
                        print("="*70 + "\n")
                        
                        with st.expander("💰 Token Usage & Cost Summary", expanded=True):
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.metric("Total LLM Calls", token_usage.get('total_calls', 0))
                            
                            with col2:
                                st.metric("Total Tokens", f"{token_usage.get('total_tokens', 0):,}")
                            
                            with col3:
                                prompt_tokens = token_usage.get('total_prompt_tokens', 0)
                                completion_tokens = token_usage.get('total_completion_tokens', 0)
                                st.metric("Prompt / Completion", f"{prompt_tokens:,} / {completion_tokens:,}")
                            
                            with col4:
                                total_cost = token_usage.get('total_cost', 0.0)
                                st.metric("Total Cost", f"${total_cost:.4f}")
                            
                            # Detailed breakdown by agent
                            if token_usage.get('by_agent'):
                                st.markdown("---")
                                st.markdown("**Breakdown by Agent:**")
                                
                                breakdown_data = []
                                for agent, metrics in token_usage['by_agent'].items():
                                    if metrics.get('calls', 0) > 0:
                                        breakdown_data.append({
                                            "Agent": agent,
                                            "Calls": metrics.get('calls', 0),
                                            "Tokens": f"{metrics.get('tokens', 0):,}",
                                            "Cost": f"${metrics.get('cost', 0.0):.4f}"
                                        })
                                
                                if breakdown_data:
                                    df_breakdown = pd.DataFrame(breakdown_data)
                                    st.dataframe(df_breakdown, use_container_width=True, hide_index=True)
                    else:
                        # Show message if token usage exists but no calls were made
                        st.warning("💰 Token tracking is enabled, but no LLM calls were recorded in this run.")
                else:
                    # Show message if token usage is not available
                    st.warning("💰 Token usage data is not available. Token tracking may not have been initialized properly.")
            
            # Store results
            if 'agent_data' in locals():
                st.session_state.agent_data = agent_data
                st.session_state.ingestion_in_progress = False
                st.session_state.ingestion_completed = True
                st.session_state.ingestion_started = False  # Reset for next time
                
                st.success("All data loaded! Dashboard is ready.")
                st.balloons()
                st.rerun()
        
        except Exception as e:
            st.session_state.ingestion_in_progress = False
            st.session_state.ingestion_started = False  # Reset on error
            st.error(f"Error loading data: {str(e)}")
            st.exception(e)
    else:
        # Ingestion already started, show loading message
        st.info("Data Ingestion in Progress... Please wait.")

# Show data loading prompt if no data
if agent_data is None and not st.session_state.ingestion_in_progress:
    st.markdown("### 👋 Welcome to The Insight Room")
    st.markdown("""
    Get started by loading your data from all sources. This will:
    - Ingest LinkedIn, Instagram, and Website data
    - Run AI-powered analytics agents
    - Generate insights and recommendations
    
    **Click the "Load Data" button in the sidebar to begin.**
    """)
    st.markdown("---")

def _display_report(report: Dict[str, Any], platform: str, report_type: str):
    """Helper function to display a generated report"""
    if 'error' in report:
        st.error(f"Error: {report['error']}")
        return
    
    # Store report in session state
    st.session_state[f'{platform}_report'] = report
    
    # Display report
    st.markdown("---")
    st.markdown("### Generated Report")
    
    # Report metadata
    col_meta1, col_meta2, col_meta3 = st.columns(3)
    with col_meta1:
        st.metric("Files Analyzed", len(report.get('files_analyzed', [])))
    with col_meta2:
        st.metric("Report Type", report.get('report_type', 'N/A').title())
    with col_meta3:
        st.metric("Generated", pd.Timestamp.now().strftime('%H:%M:%S'))
    
    st.markdown("---")
    
    # Data Summary
    if 'data_summary' in report:
        with st.expander("Data Summary", expanded=False):
            for file_type, summary in report['data_summary'].items():
                st.markdown(f"**{file_type.title()} File:**")
                st.json(summary)
    
    # Main Analysis
    st.markdown("### Analysis")
    st.markdown(report.get('analysis', 'No analysis available'))
    
    # Recommendations
    if report.get('recommendations'):
        st.markdown("---")
        st.markdown("### Key Recommendations")
        for i, rec in enumerate(report['recommendations'], 1):
            st.markdown(f"{i}. {rec}")
    
    # Prepare markdown text for download
    report_text = f"# {platform.title()} {report_type.title()} Report\n\n"
    report_text += f"**Generated:** {report.get('generated_at', 'N/A')}\n"
    report_text += f"**Files Analyzed:** {', '.join(report.get('files_analyzed', []))}\n\n"
    report_text += "---\n\n"
    report_text += report.get('analysis', '')
    if report.get('recommendations'):
        report_text += "\n\n## Recommendations\n\n"
        for i, rec in enumerate(report['recommendations'], 1):
            report_text += f"{i}. {rec}\n"
    
    st.session_state[f'{platform}_report_text'] = report_text
    st.success("Report generated successfully!")

def _display_cached_report(report: Dict[str, Any], platform: str):
    """Helper function to display a cached report"""
    st.markdown("---")
    st.markdown("### Last Generated Report")
    st.info("Click 'Generate Report' to create a new report or modify settings above.")
    
    col_meta1, col_meta2, col_meta3 = st.columns(3)
    with col_meta1:
        st.metric("Files Analyzed", len(report.get('files_analyzed', [])))
    with col_meta2:
        st.metric("Report Type", report.get('report_type', 'N/A').title())
    with col_meta3:
        st.metric("Generated", report.get('generated_at', 'N/A')[:10])
    
    st.markdown("---")
    st.markdown("### Analysis")
    st.markdown(report.get('analysis', 'No analysis available'))
    
    if report.get('recommendations'):
        st.markdown("---")
        st.markdown("### Key Recommendations")
        for i, rec in enumerate(report['recommendations'], 1):
            st.markdown(f"{i}. {rec}")

def _get_kpi_tooltip(label: str, platform: str) -> str:
    """Get tooltip text for KPI metrics"""
    tooltips = {
        "Avg Engagement Rate": "Average percentage of people who interacted with your content (likes, comments, shares, clicks) relative to total impressions.",
        "Reach Growth": "Change in the number of unique people who saw your content compared to the previous period.",
        "Avg Daily Impressions": "Average number of times your content was displayed to users per day.",
        "Avg Bounce Rate": "Percentage of visitors who leave your website after viewing only one page. Lower is better.",
        "Page Views Growth": "Change in the number of page views compared to the previous period.",
        "Unique Visitors": "Number of distinct individuals who visited your website during the period."
    }
    return tooltips.get(label, f"Metric: {label}")

def render_dashboard_tab(platform_name):
    # --- Section 1: KPI Cards (REAL DATA FROM AGENTS) ---
    if agent_data:
        kpis = agent_integration.get_kpi_metrics_from_agent(platform_name, agent_data)
    else:
        kpis = utils.get_kpi_metrics(platform=platform_name)  # Fallback to synthetic
    
    cols = st.columns(len(kpis))

    for idx, col in enumerate(cols):
        item = kpis[idx]
        trend_color = "trend-up" if item['trend_direction'] == 'up' else ("trend-down" if item['trend_direction'] == 'down' else "trend-neutral")
        trend_icon = ""  # Removed icon
        
        # Get tooltip text based on metric label
        tooltip_text = _get_kpi_tooltip(item['label'], platform_name)
        
        with col:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">
                    {item['label']}
                    <span class="tooltip-icon" title="{tooltip_text}">!</span>
                </div>
                <div class="kpi-value">{item['value']}</div>
                <div class="kpi-trend {trend_color}">
                    {item['trend']} <span style="font-weight:400; color:#94A3B8; margin-left:4px;">{item['helper']} (Last 30 days)</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Section 2: Charts Area ---
    col_chart_main, col_chart_side = st.columns([2, 1])

    with col_chart_main:
        st.markdown(f"### {platform_name} Engagement Trend")
        
        # Use real agent data if available, fallback to synthetic
        if agent_data:
            df_trend = agent_integration.get_engagement_trend_data_from_agent(platform_name, agent_data)
            if df_trend is None:
                df_trend = utils.get_engagement_trend_data(platform=platform_name)  # Fallback
                st.caption("Using estimated data (insufficient real data for trend)")
            else:
                st.caption("Real data from agent metrics")
        else:
            df_trend = utils.get_engagement_trend_data(platform=platform_name)  # Fallback
            st.caption("Using estimated data (no agent data loaded)")
        
        fig = px.line(df_trend, x="Month", y="Engagement Index", 
                      template="plotly_white", markers=True, line_shape="spline")
        fig.update_traces(line_color="#2563EB", line_width=4, marker_size=8)
        fig.update_layout(
            height=350,
            margin=dict(l=20, r=20, t=10, b=20),
            yaxis=dict(showgrid=True, gridcolor='rgba(226, 232, 240, 0.5)'),
            xaxis=dict(showgrid=False)
        )
        st.plotly_chart(fig, key=f"{platform_name}_main_trend", on_select="ignore")

    with col_chart_side:
        st.markdown("### Growth & Activity")
        
        # Use real agent data if available, fallback to synthetic
        if agent_data:
            df_follow, df_visit = agent_integration.get_supporting_charts_data_from_agent(agent_data)
            if df_follow is None:
                df_follow, df_visit = utils.get_supporting_charts_data()  # Fallback
        else:
            df_follow, df_visit = utils.get_supporting_charts_data()  # Fallback
        
        # Sparkline-ish Follower Growth
        st.markdown("**Follower Growth (6 Mo)**")
        fig_spark = px.bar(df_follow, x="Month", y="Growth", template="plotly_white")
        fig_spark.update_traces(marker_color="#CBD5E1") # Subtle grey bars
        fig_spark.update_layout(height=120, margin=dict(l=0,r=0,t=0,b=0), xaxis_title=None, yaxis_title=None)
        fig_spark.update_yaxes(showgrid=False, showticklabels=False)
        st.plotly_chart(fig_spark, config={'displayModeBar': False}, key=f"{platform_name}_spark")
        
        # Visitor Activity
        st.markdown("**Weekly Visitor Pattern**")
        fig_visit = px.bar(df_visit, x="Day", y="Visits", template="plotly_white")
        fig_visit.update_traces(marker_color="#3B82F6")
        fig_visit.update_layout(height=120, margin=dict(l=0,r=0,t=0,b=0), xaxis_title=None, yaxis_title=None)
        fig_visit.update_yaxes(showgrid=False, showticklabels=False)
        st.plotly_chart(fig_visit, config={'displayModeBar': False}, key=f"{platform_name}_visit")

    st.markdown("---")

    # --- Section 3: Top Insights (REAL AGENT INSIGHTS) ---
    st.markdown("### Top Strategic Insights")
    
    if agent_data:
        insights = agent_integration.get_insights_from_agent(platform_name, agent_data)
    else:
        insights = utils.get_insights(platform=platform_name)  # Fallback
    
    # Ensure we have at least 3 for layout
    while len(insights) < 3:
        insights.append({
            "title": "More insights coming...",
            "description": "Upload more data to unlock additional insights",
            "confidence": "Low"
        })
    
    cols_ins = st.columns(min(3, len(insights)))

    for idx, col in enumerate(cols_ins):
        if idx >= len(insights):
            break
        item = insights[idx]
        badge_cls = "badge-high" if item.get('confidence') == 'High' else "badge-medium"
        
        with col:
            # Clean description - aggressively remove all HTML tags and escape special characters
            description = str(item.get('description', ''))
            # Remove any HTML tags that might be in the description (including nested tags)
            import re
            # Remove all HTML tags (including self-closing, nested, and multiline tags)
            # This regex handles tags that might span multiple lines
            description = re.sub(r'<[^>]*>', '', description, flags=re.DOTALL)  # Remove all HTML tags (multiline)
            # Remove any stray closing tags or fragments that might remain
            description = re.sub(r'</[^>]*>', '', description)  # Remove any remaining closing tags
            # Remove any HTML-like patterns that might be left
            description = re.sub(r'<[^>]*$', '', description)  # Remove incomplete opening tags at end
            # Clean up any extra whitespace/newlines left by removed tags
            description = re.sub(r'\s+', ' ', description)  # Replace multiple whitespace with single space
            description = description.strip()
            # Escape remaining special characters (do this last to avoid double-escaping)
            description = description.replace('&amp;', '&')  # First unescape if already escaped
            description = description.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            st.markdown(f"""
            <div class="content-card">
                <div>
                    <div class="card-header-row">
                        <span class="badge {badge_cls}">Confidence: {item.get('confidence', 'Medium')}</span>
                    </div>
                    <div class="card-main-title">{item.get('title', 'Insight')}</div>
                    <div class="card-body-text">{description}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Section 4: Recommendations (REAL AGENT RECOMMENDATIONS) ---
    st.markdown("### Recommended Actions")
    
    if agent_data:
        recs = agent_integration.get_recommendations_from_agent(platform_name, agent_data)
    else:
        recs = utils.get_recommendations(platform=platform_name)  # Fallback
    
    # Ensure we have at least 3 for layout
    while len(recs) < 3:
        recs.append({
            "action": "Optimize strategy",
            "description": "More recommendations available with additional data",
            "confidence": "Low"
        })
    
    cols_rec = st.columns(min(3, len(recs)))

    for idx, col in enumerate(cols_rec):
        if idx >= len(recs):
            break
        item = recs[idx]
        badge_cls = "badge-high" if item.get('confidence') == 'High' else "badge-medium"
        
        with col:
            st.markdown(f"""
            <div class="content-card" style="border-left: 4px solid #2563EB;">
                <div>
                     <div class="card-header-row">
                        <span class="badge {badge_cls}">{item.get('confidence', 'Medium')} Confidence</span>
                    </div>
                    <div class="card-main-title">{item.get('action', 'Action')}</div>
                    <div class="card-body-text">{item.get('description', '')}</div>
                </div>
                <button style="
                    background-color:#F1F5F9; 
                    border:none; 
                    padding:8px 16px; 
                    border-radius:6px; 
                    color:#0F172A; 
                    font-size:0.85rem; 
                    font-weight:600; 
                    cursor:pointer;
                    margin-top:10px;">
                    Add to Roadmap
                </button>
            </div>
            """, unsafe_allow_html=True)

if "Reports" in selected_menu:
    st.markdown('<div class="page-title">Platform Reports</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtext">Generate comprehensive reports from platform data files using AI analysis.</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Check if data is loaded
    if agent_data is None and not st.session_state.ingestion_in_progress:
        st.info("Please load data using the button in the sidebar to generate reports.")
        st.markdown("""
        ### How to Generate Reports
        
        1. Click **"Load Data"** in the sidebar
        2. Wait for data ingestion to complete
        3. Select a platform tab below to generate reports
        
        Reports can analyze:
        - **LinkedIn**: Content, followers, and visitors data
        - **Instagram**: Posts, audience insights, and interactions
        - **Website**: Blog traffic, site sessions, and visitor analytics
        """)
    elif agent_data is None:
        st.info("Data is loading... Please wait.")
    else:
        # Platform Tabs
        report_tab1, report_tab2, report_tab3 = st.tabs(["LinkedIn", "Instagram", "Website"])
        
        # LinkedIn Reports Tab
        with report_tab1:
            st.markdown("### LinkedIn Report Generation")
            
            # Report type explanation
            with st.expander("ℹ️ Report Type Guide", expanded=False):
                st.markdown("""
                **Report Types:**
                - **Comprehensive**: Full analysis including trends, patterns, correlations, and recommendations
                - **Trends**: Focus on time-series trends, growth rates, and period-over-period comparisons
                - **Correlations**: Analyze relationships between different metrics and files
                - **Executive**: High-level summary (2-3 paragraphs) for C-suite decision making
                """)
            
            col1, col2 = st.columns([2, 1])
            with col1:
                linkedin_files = st.multiselect(
                    "Choose LinkedIn data files:",
                    options=['content', 'followers', 'visitors'],
                    default=['content'],
                    help="Select one or more files to include in the report"
                )
            with col2:
                linkedin_report_type = st.selectbox(
                    "Report type:",
                    options=['comprehensive', 'trends', 'correlations', 'executive', 'competitor analysis'],
                    index=0,
                    key="linkedin_report_type",
                    disabled=False
                )
            st.markdown("---")
            col_btn1, col_btn2 = st.columns([1, 3])
            with col_btn1:
                # Disable generate button if competitor analysis is selected
                linkedin_generate = st.button(
                    "Generate Report", 
                    type="primary", 
                    use_container_width=True, 
                    key="linkedin_generate",
                    disabled=(linkedin_report_type == 'competitor analysis')
                )
            with col_btn2:
                if 'linkedin_report' in st.session_state:
                    st.download_button(
                        "Download Report",
                        st.session_state.get('linkedin_report_text', ''),
                        file_name=f"linkedin_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.md",
                        mime="text/markdown",
                        use_container_width=True,
                        key="linkedin_download"
                    )
            
            # Show warning if competitor analysis is selected
            if linkedin_report_type == 'competitor analysis':
                st.warning("⚠️ Competitor analysis is coming soon. Please select another report type.")
            
            if linkedin_generate:
                if linkedin_report_type == 'competitor analysis':
                    st.error("Competitor analysis is not yet available. Please select another report type.")
                elif not linkedin_files:
                    st.warning("Please select at least one file to analyze.")
                else:
                    with st.spinner(f"Generating {linkedin_report_type} report..."):
                        try:
                            report = agent_integration.generate_linkedin_report(
                                files=linkedin_files,
                                report_type=linkedin_report_type
                            )
                            if not report:
                                st.error("Report generation returned no data")
                            elif 'error' in report:
                                st.error(f"Error: {report['error']}")
                            else:
                                # Print token usage for report generation
                                try:
                                    from src.agents.token_tracker import get_tracker
                                    tracker = get_tracker()
                                    # Get calls since last reset (report generation calls)
                                    report_calls = tracker.get_calls_by_agent("LinkedInReportAgent")
                                    if report_calls:
                                        latest_call = report_calls[-1]
                                        print("\n" + "="*70)
                                        print(f"💰 LINKEDIN REPORT GENERATION COST")
                                        print("="*70)
                                        print(f"Tokens Used: {latest_call.total_tokens:,} (Prompt: {latest_call.prompt_tokens:,}, Completion: {latest_call.completion_tokens:,})")
                                        print(f"Cost: ${latest_call.cost:.4f}")
                                        print("="*70 + "\n")
                                except Exception as e:
                                    print(f"⚠️ Could not retrieve report generation cost: {e}")
                                
                                _display_report(report, 'linkedin', linkedin_report_type)
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
            elif 'linkedin_report' in st.session_state:
                _display_cached_report(st.session_state['linkedin_report'], 'linkedin')
        
        # Instagram Reports Tab
        with report_tab2:
            st.markdown("### Instagram Report Generation")
            
            # Report type explanation
            with st.expander("ℹ️ Report Type Guide", expanded=False):
                st.markdown("""
                **Report Types:**
                - **Comprehensive**: Full analysis including trends, patterns, correlations, and recommendations
                - **Trends**: Focus on time-series trends, growth rates, and period-over-period comparisons
                - **Correlations**: Analyze relationships between different metrics and files
                - **Executive**: High-level summary (2-3 paragraphs) for C-suite decision making
                """)
            
            col1, col2 = st.columns([2, 1])
            with col1:
                instagram_files = st.multiselect(
                    "Choose Instagram data files:",
                    options=['posts', 'audience_insights', 'content_interactions', 'live_videos', 'profiles_reached'],
                    default=['posts'],
                    help="Select one or more files to include in the report"
                )
            with col2:
                instagram_report_type = st.selectbox(
                    "Report type:",
                    options=['comprehensive', 'trends', 'correlations', 'executive', 'competitor analysis'],
                    index=0,
                    key="instagram_report_type",
                    disabled=False
                )
            st.markdown("---")
            col_btn1, col_btn2 = st.columns([1, 3])
            with col_btn1:
                # Disable generate button if competitor analysis is selected
                instagram_generate = st.button(
                    "Generate Report", 
                    type="primary", 
                    use_container_width=True, 
                    key="instagram_generate",
                    disabled=(instagram_report_type == 'competitor analysis')
                )
            with col_btn2:
                if 'instagram_report' in st.session_state:
                    st.download_button(
                        "Download Report",
                        st.session_state.get('instagram_report_text', ''),
                        file_name=f"instagram_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.md",
                        mime="text/markdown",
                        use_container_width=True,
                        key="instagram_download"
                    )
            
            # Show warning if competitor analysis is selected
            if instagram_report_type == 'competitor analysis':
                st.warning("⚠️ Competitor analysis is coming soon. Please select another report type.")
            
            if instagram_generate:
                if instagram_report_type == 'competitor analysis':
                    st.error("Competitor analysis is not yet available. Please select another report type.")
                elif not instagram_files:
                    st.warning("Please select at least one file to analyze.")
                else:
                    with st.spinner(f"Generating {instagram_report_type} report..."):
                        try:
                            report = agent_integration.generate_instagram_report(
                                files=instagram_files,
                                report_type=instagram_report_type
                            )
                            if not report:
                                st.error("Report generation returned no data")
                            elif 'error' in report:
                                st.error(f"Error: {report['error']}")
                            else:
                                # Print token usage for report generation
                                try:
                                    from src.agents.token_tracker import get_tracker
                                    tracker = get_tracker()
                                    # Get calls since last reset (report generation calls)
                                    report_calls = tracker.get_calls_by_agent("InstagramReportAgent")
                                    if report_calls:
                                        latest_call = report_calls[-1]
                                        print("\n" + "="*70)
                                        print(f"💰 INSTAGRAM REPORT GENERATION COST")
                                        print("="*70)
                                        print(f"Tokens Used: {latest_call.total_tokens:,} (Prompt: {latest_call.prompt_tokens:,}, Completion: {latest_call.completion_tokens:,})")
                                        print(f"Cost: ${latest_call.cost:.4f}")
                                        print("="*70 + "\n")
                                except Exception as e:
                                    print(f"⚠️ Could not retrieve report generation cost: {e}")
                                
                                _display_report(report, 'instagram', instagram_report_type)
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
            elif 'instagram_report' in st.session_state:
                _display_cached_report(st.session_state['instagram_report'], 'instagram')
        
        # Website Reports Tab
        with report_tab3:
            st.markdown("### Website Report Generation")
            
            # Report type explanation
            with st.expander("ℹ️ Report Type Guide", expanded=False):
                st.markdown("""
                **Report Types:**
                - **Comprehensive**: Full analysis including trends, patterns, correlations, and recommendations
                - **Trends**: Focus on time-series trends, growth rates, and period-over-period comparisons
                - **Correlations**: Analyze relationships between different metrics and files
                - **Executive**: High-level summary (2-3 paragraphs) for C-suite decision making
                """)
            
            col1, col2 = st.columns([2, 1])
            with col1:
                website_files = st.multiselect(
                    "Choose Website data files:",
                    options=['blog', 'traffic', 'sessions', 'all'],
                    default=['all'],
                    help="Select files to include. 'all' will analyze all available files."
                )
            with col2:
                website_report_type = st.selectbox(
                    "Report type:",
                    options=['comprehensive', 'trends', 'correlations', 'executive', 'competitor analysis'],
                    index=0,
                    key="website_report_type",
                    disabled=False
                )
            st.markdown("---")
            col_btn1, col_btn2 = st.columns([1, 3])
            with col_btn1:
                # Disable generate button if competitor analysis is selected
                website_generate = st.button(
                    "Generate Report", 
                    type="primary", 
                    use_container_width=True, 
                    key="website_generate",
                    disabled=(website_report_type == 'competitor analysis')
                )
            with col_btn2:
                if 'website_report' in st.session_state:
                    st.download_button(
                        "Download Report",
                        st.session_state.get('website_report_text', ''),
                        file_name=f"website_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.md",
                        mime="text/markdown",
                        use_container_width=True,
                        key="website_download"
                    )
            
            # Show warning if competitor analysis is selected
            if website_report_type == 'competitor analysis':
                st.warning("⚠️ Competitor analysis is coming soon. Please select another report type.")
            
            if website_generate:
                if website_report_type == 'competitor analysis':
                    st.error("Competitor analysis is not yet available. Please select another report type.")
                elif not website_files:
                    st.warning("Please select at least one file to analyze.")
                else:
                    with st.spinner(f"Generating {website_report_type} report..."):
                        try:
                            report = agent_integration.generate_website_report(
                                files=website_files,
                                report_type=website_report_type
                            )
                            if not report:
                                st.error("Report generation returned no data")
                            elif 'error' in report:
                                st.error(f"Error: {report['error']}")
                            else:
                                # Print token usage for report generation
                                try:
                                    from src.agents.token_tracker import get_tracker
                                    tracker = get_tracker()
                                    # Get calls since last reset (report generation calls)
                                    report_calls = tracker.get_calls_by_agent("WebsiteReportAgent")
                                    if report_calls:
                                        latest_call = report_calls[-1]
                                        print("\n" + "="*70)
                                        print(f"💰 WEBSITE REPORT GENERATION COST")
                                        print("="*70)
                                        print(f"Tokens Used: {latest_call.total_tokens:,} (Prompt: {latest_call.prompt_tokens:,}, Completion: {latest_call.completion_tokens:,})")
                                        print(f"Cost: ${latest_call.cost:.4f}")
                                        print("="*70 + "\n")
                                except Exception as e:
                                    print(f"⚠️ Could not retrieve report generation cost: {e}")
                                
                                _display_report(report, 'website', website_report_type)
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
            elif 'website_report' in st.session_state:
                _display_cached_report(st.session_state['website_report'], 'website')
        

else:
    # --- Main Dashboard View (Dashboard & Marketing) ---
    
    # Check if data is loaded
    if agent_data is None and not st.session_state.ingestion_in_progress:
        st.info("Please load data using the button in the sidebar to view the dashboard.")
    elif agent_data is None:
        st.info("Data is loading... Please wait.")
    else:
        # --- Tabs Implementation ---
        tab1, tab2, tab3 = st.tabs(["LinkedIn", "Instagram", "Website"])

        with tab1:
            render_dashboard_tab("LinkedIn")

        with tab2:
            render_dashboard_tab("Instagram")

        with tab3:
            render_dashboard_tab("Website")

    st.markdown("---")

# --- Ask The Insight Room Chat Interface ---
# Only enable if data is loaded
if agent_data and agent_data.get('store'):
    with st.expander("Ask The Insight Room", expanded=False):
        st.markdown("**AI Analyst** - Ask questions about your marketing data")
        
        # Initialize chat history in session state
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
            # Add welcome message
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": "Hello! I'm your AI analyst. I can help you understand your marketing data across LinkedIn, Instagram, and Website. Ask me anything about trends, performance, or recommendations!"
            })
        
        # Display chat history
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # User input
        user_question = st.chat_input("Ask a question about your data...", key="insight_room_input")
        
        if user_question:
            # Add user message to history
            st.session_state.chat_history.append({
                "role": "user",
                "content": user_question
            })
            
            # Show user message
            with st.chat_message("user"):
                st.markdown(user_question)
            
            # Generate AI response
            with st.chat_message("assistant"):
                with st.spinner("Analyzing data..."):
                    try:
                        response = agent_integration.ask_insight_room(user_question, agent_data)
                        st.markdown(response)
                        
                        # Print token usage for chatbot
                        try:
                            from src.agents.token_tracker import get_tracker
                            tracker = get_tracker()
                            # Get the latest chatbot call
                            chatbot_calls = tracker.get_calls_by_agent("ChatbotAgent")
                            if chatbot_calls:
                                latest_call = chatbot_calls[-1]
                                print("\n" + "="*70)
                                print(f"💰 CHATBOT RESPONSE COST")
                                print("="*70)
                                print(f"Question: {user_question[:60]}...")
                                print(f"Tokens Used: {latest_call.total_tokens:,} (Prompt: {latest_call.prompt_tokens:,}, Completion: {latest_call.completion_tokens:,})")
                                print(f"Cost: ${latest_call.cost:.4f}")
                                print("="*70 + "\n")
                        except Exception as e:
                            print(f"⚠️ Could not retrieve chatbot cost: {e}")
                        
                        # Add assistant response to history
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": response
                        })
                    except Exception as e:
                        error_msg = f"Error: {str(e)}"
                        st.error(error_msg)
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": error_msg
                        })
        
        # Clear chat button
        if st.session_state.chat_history:
            if st.button("Clear Chat", key="clear_chat", type="secondary"):
                st.session_state.chat_history = []
                st.rerun()
else:
    with st.expander("Ask The Insight Room", expanded=False):
        st.markdown("**AI Analyst** - Ask questions about your marketing data")
        st.info("Please load data using the 'Load Data' button in the sidebar to use this feature.")
        st.chat_input("Ask a question about your data...", key="insight_room_input_disabled", disabled=True)

# Force Reload
