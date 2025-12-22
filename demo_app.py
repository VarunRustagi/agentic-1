import streamlit as st
import pandas as pd
import plotly.express as px
import dashboard_utils as utils

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
        </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# ===== LOAD AGENT DATA (Cached for performance) =====
@st.cache_resource(show_spinner="Loading intelligence agents...")
def init_agents():
    """Initialize all agents and load real data"""
    try:
        return agent_integration.load_agent_data()
    except Exception as e:
        st.error(f"Agent initialization failed: {e}")
        return None

# Load agent data ONCE
agent_data = init_agents()

# --- Sidebar Navigation ---
with st.sidebar:
    st.image("logo.png", use_container_width=True)
    st.markdown("### 🐺 The Insight Room")
    st.markdown("---")
    
    # Navigation Menu
    menu_options = [
        "📊 Dashboard", 
        "📢 Marketing", 
        "📑 Reports"
    ]
    
    selected_menu = st.radio("Navigation", menu_options, index=0, label_visibility="collapsed")
    
    st.markdown("---")
    st.caption("Active Agents")
    
    if agent_data and agent_data.get('store'):
        store = agent_data['store']
        n_li = len(store.linkedin_metrics)
        n_ig = len(store.instagram_metrics)
        n_web = len(store.website_metrics)
        
        st.success(f"● LinkedIn Agent ({n_li} records)")
        st.success(f"● Instagram Agent ({n_ig} records)")
        st.success(f"● Website Agent ({n_web} records)")
    else:
        st.warning("⚠ Agents initializing...")
        
    st.markdown("---")
    st.markdown("**Version 1.2.1 (Enterprise)**")


# --- Main Header ---
col_head_main, col_head_user = st.columns([3, 1])

with col_head_main:
    st.markdown('<div class="page-title">Marketing Overview</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtext">Insights generated from approved public sources and analytics data.</div>', unsafe_allow_html=True)

with col_head_user:
    # User Profile Snippet
    with st.container():
        c1, c2 = st.columns([1, 3])
        with c1:
            st.markdown("👤", unsafe_allow_html=True) # Placeholder avatar
        with c2:
            st.markdown("**Sharanya**")
            st.caption("CMO • Shorthills AI")
    
    # Date Range
    st.selectbox("Date Range", ["Last 3 Months", "Last 6 Months", "Year to Date"], index=1, label_visibility="collapsed")

st.markdown("---")

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
        trend_icon = "↑" if item['trend_direction'] == 'up' else ("↓" if item['trend_direction'] == 'down' else "→")
        
        with col:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">{item['label']}</div>
                <div class="kpi-value">{item['value']}</div>
                <div class="kpi-trend {trend_color}">
                    {trend_icon} {item['trend']} <span style="font-weight:400; color:#94A3B8; margin-left:4px;">{item['helper']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Section 2: Charts Area ---
    col_chart_main, col_chart_side = st.columns([2, 1])

    with col_chart_main:
        st.markdown(f"### 📈 {platform_name} Engagement Trend")
        df_trend = utils.get_engagement_trend_data(platform=platform_name)
        
        fig = px.line(df_trend, x="Month", y="Engagement Index", 
                      template="plotly_white", markers=True, line_shape="spline")
        fig.update_traces(line_color="#2563EB", line_width=4, marker_size=8)
        fig.update_layout(
            height=350,
            margin=dict(l=20, r=20, t=10, b=20),
            yaxis=dict(showgrid=True, gridcolor='rgba(226, 232, 240, 0.5)'),
            xaxis=dict(showgrid=False)
        )
        st.plotly_chart(fig, use_container_width=True, key=f"{platform_name}_main_trend")
        st.caption("Index calculated based on weighted average of various engagement metrics.")

    with col_chart_side:
        st.markdown("### Growth & Activity")
        df_follow, df_visit = utils.get_supporting_charts_data()
        
        # Sparkline-ish Follower Growth
        st.markdown("**Follower Growth (6 Mo)**")
        fig_spark = px.bar(df_follow, x="Month", y="Growth", template="plotly_white")
        fig_spark.update_traces(marker_color="#CBD5E1") # Subtle grey bars
        fig_spark.update_layout(height=120, margin=dict(l=0,r=0,t=0,b=0), xaxis_title=None, yaxis_title=None)
        fig_spark.update_yaxes(showgrid=False, showticklabels=False)
        st.plotly_chart(fig_spark, use_container_width=True, config={'displayModeBar': False}, key=f"{platform_name}_spark")
        
        # Visitor Activity
        st.markdown("**Weekly Visitor Pattern**")
        fig_visit = px.bar(df_visit, x="Day", y="Visits", template="plotly_white")
        fig_visit.update_traces(marker_color="#3B82F6")
        fig_visit.update_layout(height=120, margin=dict(l=0,r=0,t=0,b=0), xaxis_title=None, yaxis_title=None)
        fig_visit.update_yaxes(showgrid=False, showticklabels=False)
        st.plotly_chart(fig_visit, use_container_width=True, config={'displayModeBar': False}, key=f"{platform_name}_visit")

    st.markdown("---")

    # --- Section 3: Top Insights (REAL AGENT INSIGHTS) ---
    st.markdown("### 💡 Top Strategic Insights")
    
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
    st.markdown("### 🚀 Recommended Actions")
    
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
    # --- Executive Report View ---
    st.markdown("### 📄 Generated Executive Report")
    
    # Use real agent executive summary if available
    if agent_data and 'executive' in agent_data:
        # Format the executive insights into a report
        exec_insights = agent_data['executive']
        report_content = "# PERFORMANCE & STRATEGY REPORT\n\n"
        report_content += f"**Generated:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        
        for insight in exec_insights:
            report_content += f"## {insight.title}\n"
            report_content += f"{insight.summary}\n\n"
            report_content += f"**Metric:** {insight.metric_basis}\n"
            report_content += f"**Recommendation:** {insight.recommendation}\n\n"
            report_content += "---\n\n"
    else:
        report_content = utils.get_report_summary()  # Fallback
    
    st.markdown(report_content)
    
    st.markdown("---")
    st.download_button("Download PDF Report", report_content, file_name="executive_report.txt")

else:
    # --- Main Dashboard View (Dashboard & Marketing) ---
    
    # --- Tabs Implementation ---
    tab1, tab2, tab3 = st.tabs(["LinkedIn", "Instagram", "Website"])

    with tab1:
        render_dashboard_tab("LinkedIn")

    with tab2:
        render_dashboard_tab("Instagram")

    with tab3:
        render_dashboard_tab("Website")

    st.markdown("---")

    # --- Data Input Panel ---
    st.markdown("### 🔌 Data & Competitor Sources")
    with st.container():
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Approved Public Sources**")
            st.text_input("Website URL", placeholder="https://shorthills.ai")
            st.text_input("LinkedIn Page URL", placeholder="https://linkedin.com/company/shorthills-ai")
        with c2:
            st.markdown("**Competitor Benchmarking**")
            st.text_area("Competitor URLs (one per line)", placeholder="https://competitor.com\nhttps://rival.com")
            st.button("Run Analysis", type="primary")

# --- Chatbot Overlay (Floating) ---
# To simulate the floating chat, we use a fixed position button in CSS
# For the actual interaction, we'll use a sidebar or expander
with st.expander("💬 Ask The Insight Room", expanded=False):
    st.markdown("**AI Analyst**")
    st.chat_message("assistant").write("I've analyzed the latest engagement data. The drop in posting consistency seems to be correlating with the dip in weekend engagement. Shall I draft a schedule?")
    st.text_input("Ask a question...", placeholder="Why is engagement down?")

# Force Reload
