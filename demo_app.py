import streamlit as st
import pandas as pd
import plotly.express as px
import dashboard_utils as utils
from typing import Dict, Any

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
        
        /* Info, Warning, Success, Error messages - Black text */
        .stAlert,
        [data-baseweb="notification"],
        .stInfo,
        .stWarning,
        .stSuccess,
        .stError {
            color: #0F172A !important; /* Black */
        }
        .stInfo > div,
        .stWarning > div,
        .stSuccess > div,
        .stError > div {
            color: #0F172A !important; /* Black */
        }
        
        /* Expander text - Black */
        [data-baseweb="accordion"],
        .streamlit-expanderHeader,
        .streamlit-expanderContent {
            color: #0F172A !important; /* Black */
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
        /* Expander header and content - Black */
        [data-baseweb="accordion"] button,
        [data-baseweb="accordion"] summary,
        .streamlit-expanderHeader,
        .streamlit-expanderHeader *,
        .streamlit-expanderContent,
        .streamlit-expanderContent * {
            color: #0F172A !important; /* Black */
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
def init_agents():
    """Initialize all agents and load real data"""
    try:
        return agent_integration.load_agent_data()
    except Exception as e:
        st.error(f"Agent initialization failed: {e}")
        return None

# Initialize session state for agent data
if 'agent_data' not in st.session_state:
    st.session_state.agent_data = None
if 'ingestion_in_progress' not in st.session_state:
    st.session_state.ingestion_in_progress = False

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
            st.session_state.ingestion_in_progress = True
            st.rerun()
        
    st.markdown("---")
    st.markdown("**Version 1.2.1 (Enterprise)**")

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
if st.session_state.ingestion_in_progress and st.session_state.agent_data is None:
    st.info("Data Ingestion in Progress...")
    
    # File processing status
    status_placeholder = st.empty()
    
    try:
        with status_placeholder.container():
            st.markdown("**Processing files:**")
            
            # Show expected file processing steps
            file_status = st.empty()
            file_status.markdown("""
            - Loading LinkedIn data files...
            - Loading Instagram data files...
            - Loading Website data files...
            - Running analytics agents...
            - Generating insights...
            """)
        
        # Load data (this does all the work)
        agent_data = init_agents()
        
        # Update status
        with status_placeholder.container():
            if agent_data and agent_data.get('store'):
                store = agent_data['store']
                st.success("**Files processed successfully:**")
                st.markdown(f"""
                - LinkedIn: {len(store.linkedin_metrics)} records loaded
                - Instagram: {len(store.instagram_metrics)} records loaded
                - Website: {len(store.website_metrics)} records loaded
                """)
        
        # Store results
        st.session_state.agent_data = agent_data
        st.session_state.ingestion_in_progress = False
        
        st.success("All data loaded! Dashboard is ready.")
        st.balloons()
        st.rerun()
        
    except Exception as e:
        st.session_state.ingestion_in_progress = False
        st.error(f"Error loading data: {str(e)}")
        st.exception(e)

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
            evidence_html = ""
            if 'evidence' in item and item['evidence']:
                evidence_list = "<br>".join([f"• {e}" for e in item['evidence']])
                evidence_html = f"""
                <details style="margin-top:12px; font-size:0.85rem; color:#64748B;">
                    <summary style="cursor:pointer; font-weight:500;">View Evidence</summary>
                    <div style="margin-top:8px; padding-left:8px; border-left:2px solid #E2E8F0;">
                        {evidence_list}
                    </div>
                </details>
                """
            
            st.markdown(f"""
            <div class="content-card">
                <div>
                    <div class="card-header-row">
                        <span class="badge {badge_cls}">Confidence: {item.get('confidence', 'Medium')}</span>
                    </div>
                    <div class="card-main-title">{item.get('title', 'Insight')}</div>
                    <div class="card-body-text">{item.get('description', '')}</div>
                    {evidence_html}
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
                    options=['comprehensive', 'trends', 'correlations', 'executive'],
                    index=0,
                    key="linkedin_report_type"
                )
            
            st.markdown("---")
            col_btn1, col_btn2 = st.columns([1, 3])
            with col_btn1:
                linkedin_generate = st.button("Generate Report", type="primary", use_container_width=True, key="linkedin_generate")
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
            
            if linkedin_generate:
                if not linkedin_files:
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
                    options=['comprehensive', 'trends', 'correlations', 'executive'],
                    index=0,
                    key="instagram_report_type"
                )
            
            st.markdown("---")
            col_btn1, col_btn2 = st.columns([1, 3])
            with col_btn1:
                instagram_generate = st.button("Generate Report", type="primary", use_container_width=True, key="instagram_generate")
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
            
            if instagram_generate:
                if not instagram_files:
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
                    options=['comprehensive', 'trends', 'correlations', 'executive'],
                    index=0,
                    key="website_report_type"
                )
            
            st.markdown("---")
            col_btn1, col_btn2 = st.columns([1, 3])
            with col_btn1:
                website_generate = st.button("Generate Report", type="primary", use_container_width=True, key="website_generate")
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
            
            if website_generate:
                if not website_files:
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
                                _display_report(report, 'website', website_report_type)
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
            elif 'website_report' in st.session_state:
                _display_cached_report(st.session_state['website_report'], 'website')
        
        # Executive Summary Section (shown in all tabs)
        st.markdown("---")
        st.markdown("### Executive Summary (Cross-Platform)")
        
        if agent_data and 'executive' in agent_data:
            exec_insights = agent_data['executive']
            for insight in exec_insights:
                with st.expander(f"{insight.title}", expanded=False):
                    st.markdown(insight.summary)
                    st.caption(f"**Metric Basis:** {insight.metric_basis} | **Confidence:** {insight.confidence}")
                    st.markdown(f"**Recommendation:** {insight.recommendation}")
        else:
            st.info("Executive insights will appear here after agents complete analysis.")

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
        if st.button("Clear Chat", key="clear_chat"):
            st.session_state.chat_history = []
            st.rerun()

# Force Reload
