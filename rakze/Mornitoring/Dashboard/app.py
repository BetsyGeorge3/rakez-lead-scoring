"""
Streamlit dashboard for model monitoring
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import requests
import json

# Page configuration
st.set_page_config(
    page_title="RAKEZ Lead Scoring Dashboard",
    page_icon="📊",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #F3F4F6;
        border-radius: 10px;
        padding: 20px;
        margin: 10px;
    }
    .alert-warning {
        background-color: #FEF3C7;
        border-left: 5px solid #F59E0B;
        padding: 15px;
    }
    .alert-critical {
        background-color: #FEE2E2;
        border-left: 5px solid #DC2626;
        padding: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<h1 class="main-header">📈 RAKEZ Lead Scoring Model Dashboard</h1>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/artificial-intelligence.png", width=100)
    st.title("Dashboard Controls")
    
    # Date range selector
    date_range = st.date_input(
        "Select Date Range",
        value=[datetime.now() - timedelta(days=7), datetime.now()],
        max_value=datetime.now()
    )
    
    # Model version selector
    model_version = st.selectbox(
        "Model Version",
        ["v2.1.0 (Production)", "v2.0.0 (Staging)", "v1.5.0 (Archived)"]
    )
    
    # Refresh interval
    refresh = st.slider("Auto-refresh (minutes)", 1, 60, 5)
    
    if st.button("🔄 Manual Refresh"):
        st.experimental_rerun()

# Load data (in production, this would come from APIs/database)
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_monitoring_data():
    """Load monitoring data from API"""
    try:
        # Simulated data - replace with actual API calls
        return {
            "predictions_today": 1245,
            "avg_score": 0.42,
            "conversion_rate": 0.18,
            "high_quality_leads": 287,
            "api_latency": 145,
            "error_rate": 0.012,
            "drift_detected": True,
            "alerts": [
                {"type": "DATA_DRIFT", "severity": "WARNING", "message": "Feature 'website_visits' showing drift"},
                {"type": "PERFORMANCE", "severity": "INFO", "message": "Model accuracy stable at 85%"}
            ],
            "predictions_over_time": pd.DataFrame({
                "timestamp": pd.date_range(start="2024-01-01", periods=24, freq="H"),
                "predictions": np.random.poisson(50, 24),
                "avg_score": np.random.uniform(0.3, 0.6, 24)
            }),
            "score_distribution": pd.DataFrame({
                "score_category": ["Low", "Medium", "High"],
                "count": [800, 300, 145],
                "conversion_rate": [0.05, 0.25, 0.48]
            })
        }
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# Load data
data = load_monitoring_data()

if data is None:
    st.warning("Unable to load monitoring data. Please check API connections.")
    st.stop()

# Top metrics row
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Predictions Today",
        value=f"{data['predictions_today']:,}",
        delta="+12%"
    )

with col2:
    st.metric(
        label="Avg Lead Score",
        value=f"{data['avg_score']:.2f}",
        delta="-0.03"
    )

with col3:
    st.metric(
        label="Conversion Rate",
        value=f"{data['conversion_rate']:.1%}",
        delta="+2.1%"
    )

with col4:
    st.metric(
        label="High-Quality Leads",
        value=f"{data['high_quality_leads']}",
        delta="+15"
    )

# Alerts section
st.subheader("🚨 Alerts & Notifications")

if data['drift_detected']:
    with st.container():
        st.markdown('<div class="alert-warning">⚠️ Data drift detected in recent predictions. Consider retraining model.</div>', unsafe_allow_html=True)

for alert in data['alerts'][:3]:  # Show top 3 alerts
    alert_class = "alert-warning" if alert['severity'] == 'WARNING' else "alert-critical"
    st.markdown(f'<div class="{alert_class}">{alert["severity"]}: {alert["message"]}</div>', unsafe_allow_html=True)

# Charts - Row 1
col1, col2 = st.columns(2)

with col1:
    st.subheader("Predictions Over Time")
    
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=data['predictions_over_time']['timestamp'],
        y=data['predictions_over_time']['predictions'],
        mode='lines+markers',
        name='Predictions',
        line=dict(color='#3B82F6', width=2)
    ))
    fig1.update_layout(
        height=300,
        xaxis_title="Time",
        yaxis_title="Number of Predictions",
        template="plotly_white"
    )
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("Score Distribution")
    
    fig2 = go.Figure(data=[
        go.Pie(
            labels=data['score_distribution']['score_category'],
            values=data['score_distribution']['count'],
            hole=0.4,
            marker=dict(colors=['#EF4444', '#F59E0B', '#10B981'])
        )
    ])
    fig2.update_layout(
        height=300,
        showlegend=True,
        template="plotly_white"
    )
    st.plotly_chart(fig2, use_container_width=True)

# Charts - Row 2
col1, col2 = st.columns(2)

with col1:
    st.subheader("Conversion Rate by Score")
    
    fig3 = px.bar(
        data['score_distribution'],
        x='score_category',
        y='conversion_rate',
        color='score_category',
        color_discrete_map={'Low': '#EF4444', 'Medium': '#F59E0B', 'High': '#10B981'},
        text_auto='.1%'
    )
    fig3.update_layout(
        height=300,
        xaxis_title="Score Category",
        yaxis_title="Conversion Rate",
        showlegend=False,
        template="plotly_white"
    )
    st.plotly_chart(fig3, use_container_width=True)

with col2:
    st.subheader("System Health")
    
    # Create radar chart for system metrics
    categories = ['Accuracy', 'Latency', 'Throughput', 'Stability', 'Coverage']
    
    fig4 = go.Figure(data=go.Scatterpolar(
        r=[0.85, 0.9, 0.75, 0.95, 0.8],  # Example metrics
        theta=categories,
        fill='toself',
        line_color='#8B5CF6'
    ))
    
    fig4.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )),
        showlegend=False,
        height=300,
        template="plotly_white"
    )
    st.plotly_chart(fig4, use_container_width=True)

# Performance metrics table
st.subheader("📋 Detailed Metrics")

metrics_df = pd.DataFrame({
    "Metric": ["Model Accuracy", "Precision", "Recall", "F1-Score", "AUC-ROC", "API Latency (p95)", "Error Rate"],
    "Value": ["85.2%", "82.1%", "76.8%", "79.3%", "0.89", "145ms", "1.2%"],
    "Target": [">80%", ">75%", ">70%", ">75%", ">0.85", "<200ms", "<2%"],
    "Status": ["✅", "✅", "✅", "✅", "✅", "✅", "✅"]
})

st.dataframe(
    metrics_df,
    use_container_width=True,
    hide_index=True
)

# Drift detection section
st.subheader("🔍 Drift Detection")

if st.button("Run Drift Analysis"):
    with st.spinner("Analyzing data drift..."):
        # Simulate drift analysis
        drift_results = {
            "features": ["website_visits", "email_open_rate", "company_size"],
            "psi_scores": [0.15, 0.08, 0.03],
            "status": ["⚠️ Drift", "✅ OK", "✅ OK"]
        }
        
        drift_df = pd.DataFrame(drift_results)
        st.dataframe(drift_df, use_container_width=True, hide_index=True)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #6B7280;'>
        <p>Last updated: {}</p>
        <p>RAKEZ Lead Scoring System • Model: {} • Auto-refresh: {} minutes</p>
    </div>
    """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), model_version, refresh),
    unsafe_allow_html=True
)

# Auto-refresh
if refresh > 0:
    st.experimental_rerun()
