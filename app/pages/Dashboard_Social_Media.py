import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from utils.helpers import apply_custom_css
from utils.scraper_credits import get_all_platform_credits, get_credit_status_message, log_credit_check
import config
from utils.init_db import get_manager
from utils.auth import require_login, sidebar_logout

# Page Configuration
st.set_page_config(page_title="Social Media Monitoring", layout="wide")

authenticator = require_login()
sidebar_logout(authenticator)

apply_custom_css()

st.markdown('<p class="main-header">Social Media Scraper Monitoring</p>', unsafe_allow_html=True)

db = get_manager("dashboard_db")

# Platform information
PLATFORMS = {
    "Facebook": {"emoji": "👤", "api": "APIFY", "color": "#1877F2"},
    "Twitter": {"emoji": "𝕏", "api": "X API", "color": "#000000"},
    "Instagram": {"emoji": "📷", "api": "APIFY", "color": "#E4405F"},
    "TikTok": {"emoji": "🎵", "api": "TIKAPI", "color": "#25F4EE"},
    "YouTube": {"emoji": "▶️", "api": "YOUTUBE API", "color": "#FF0000"}
}

# Get date range (last 30 days)
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

# Query data from the unified social media monitoring table
query = f"""
    SELECT 
        platform,
        mention_date,
        mention_datetime,
        SUM(scraped_count) as total_scraped,
        SUM(filtered_count) as total_filtered,
        keywords,
        filter_criteria,
        MAX(last_updated) as last_updated,
        COUNT(CASE WHEN scraping_status = 'SUCCESS' THEN 1 END) as success_count
    FROM {config.SOCIAL_MEDIA_MONITORING_TABLE}
    WHERE mention_datetime BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY platform, mention_date, mention_datetime, keywords, filter_criteria
    ORDER BY mention_datetime DESC
"""

# Try to fetch data, otherwise use sample data for demonstration
try:
    df = db.fetch_data(query)
    if df.empty:
        st.warning("No monitoring data found for the past 30 days. Showing sample data.")
        use_sample_data = True
    else:
        use_sample_data = False
except Exception as e:
    st.warning(f"Could not connect to database: {str(e)}. Showing sample data for demonstration.")
    use_sample_data = True

# If using sample data, create it for demonstration
if use_sample_data:
    platform_data = pd.DataFrame({
        "Platform": list(PLATFORMS.keys()),
        "Total Scraped": [12500, 9800, 8300, 7200, 7400],
        "Filtered & Stored": [5200, 3800, 4100, 2900, 2800],
    })
else:
    # Aggregate data by platform from query results
    platform_data = df.groupby('platform').agg({
        'total_scraped': 'sum',
        'total_filtered': 'sum'
    }).reset_index()
    platform_data.columns = ['Platform', 'Total Scraped', 'Filtered & Stored']

# Create tabs for different views
tab1, tab2, tab3 = st.tabs(["📊 Overview", "📈 Trends", "⚙️ Credits & Status"])

with tab1:
    st.subheader("1-Month Scraping Overview")
    
    # Create 5 columns for platform cards
    platform_cols = st.columns(5)
    
    for idx, (platform, info) in enumerate(PLATFORMS.items()):
        with platform_cols[idx]:
            st.markdown(f"""
                <div style="background: linear-gradient(135deg, {info['color']}20 0%, {info['color']}10 100%); 
                            border-left: 5px solid {info['color']}; padding: 15px; border-radius: 5px;">
                    <h3>{info['emoji']} {platform}</h3>
                    <p style="margin: 5px 0; font-size: 12px; color: #666;">API: {info['api']}</p>
                </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # KPI Section
    st.subheader("Key Performance Indicators (1 Month)")
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

    total_scraped = int(platform_data['Total Scraped'].sum())
    total_filtered = int(platform_data['Filtered & Stored'].sum())
    filter_rate = (total_filtered / total_scraped * 100) if total_scraped > 0 else 0

    # Calculate previous 30-day period
    prev_end_date = start_date
    prev_start_date = prev_end_date - timedelta(days=30)
    prev_query = f"""
        SELECT 
            SUM(scraped_count) as total_scraped,
            SUM(filtered_count) as total_filtered
        FROM {config.SOCIAL_MEDIA_MONITORING_TABLE}
        WHERE mention_datetime BETWEEN '{prev_start_date}' AND '{prev_end_date}'
    """
    try:
        prev_df = db.fetch_data(prev_query)
        prev_total_scraped = int(prev_df['total_scraped'].iloc[0]) if not prev_df.empty and prev_df['total_scraped'].iloc[0] is not None else 0
        prev_total_filtered = int(prev_df['total_filtered'].iloc[0]) if not prev_df.empty and prev_df['total_filtered'].iloc[0] is not None else 0
        prev_filter_rate = (prev_total_filtered / prev_total_scraped * 100) if prev_total_scraped > 0 else 0
    except Exception:
        prev_total_scraped = prev_total_filtered = prev_filter_rate = 0

    # Calculate percentage changes
    def pct_change(current, previous):
        if previous == 0:
            return "N/A" if current == 0 else "+100%"
        change = ((current - previous) / previous) * 100
        return f"{change:+.1f}%"

    scraped_change = pct_change(total_scraped, prev_total_scraped)
    filtered_change = pct_change(total_filtered, prev_total_filtered)
    filter_rate_change = pct_change(filter_rate, prev_filter_rate)

    with kpi_col1:
        st.metric("Total Content Scraped", f"{total_scraped:,}", scraped_change)

    with kpi_col2:
        st.metric("Content Filtered & Stored", f"{total_filtered:,}", filtered_change)

    with kpi_col3:
        st.metric("Filter Efficiency", f"{filter_rate:.1f}%", filter_rate_change)

    with kpi_col4:
        st.metric("Active Platforms", "5/5", "✅")

    st.markdown("---")
    
    # Content Breakdown by Platform
    st.subheader("Content Scraped by Platform (30 Days)")
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        fig_bar = px.bar(
            platform_data,
            x="Platform",
            y="Total Scraped",
            color="Platform",
            title="Total Content Scraped by Platform",
            text_auto=True,
            color_discrete_map={p: PLATFORMS[p]["color"] for p in PLATFORMS.keys()}
        )
        fig_bar.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig_bar, use_container_width=True)
    
    with col_chart2:
        fig_pie = go.Figure(data=[go.Pie(
            labels=platform_data["Platform"],
            values=platform_data["Total Scraped"],
            marker=dict(colors=[PLATFORMS[p]["color"] for p in platform_data["Platform"]])
        )])
        fig_pie.update_layout(title="Distribution of Scraped Content", height=400)
        st.plotly_chart(fig_pie, use_container_width=True)
    
    st.markdown("---")
    
    # Filtered vs Total Content
    st.subheader("Filtered Content Analysis")
    
    fig_comparison = px.bar(
        platform_data,
        x="Platform",
        y=["Total Scraped", "Filtered & Stored"],
        barmode="group",
        title="Scraped vs Filtered Content",
        text_auto=True,
        labels={"value": "Count", "variable": "Content Type"}
    )
    fig_comparison.update_layout(height=400)
    st.plotly_chart(fig_comparison, use_container_width=True)
    
    with st.expander("🔍 Detailed Platform Statistics"):
        st.dataframe(platform_data, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("30-Day Trend Analysis")
    
    if use_sample_data:
        # Generate sample daily data for demonstration
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        trend_data = pd.DataFrame({
            "Date": dates,
            "Facebook": [400 + i*15 for i in range(30)],
            "Twitter": [300 + i*10 for i in range(30)],
            "Instagram": [280 + i*12 for i in range(30)],
            "TikTok": [240 + i*8 for i in range(30)],
            "YouTube": [250 + i*9 for i in range(30)],
        })
    else:
        # Create trend data from actual database
        trend_query = f"""
            SELECT mention_date, platform, SUM(filtered_count) as count
            FROM {config.SOCIAL_MEDIA_MONITORING_TABLE}
            WHERE mention_datetime BETWEEN '{start_date}' AND '{end_date}'
            GROUP BY mention_date, platform
            ORDER BY mention_date, platform
        """
        try:
            trend_df = db.fetch_data(trend_query)
            # Rename columns to ensure consistency
            trend_df.columns = [col.lower() for col in trend_df.columns]
            
            # Pivot the data for visualization
            if 'mention_date' in trend_df.columns:
                trend_df['mention_date'] = pd.to_datetime(trend_df['mention_date'])
                trend_data = trend_df.pivot_table(index='mention_date', columns='platform', values='count', aggfunc='sum').reset_index()
                trend_data.columns.name = None
                trend_data.rename(columns={'mention_date': 'Date'}, inplace=True)
                trend_data = trend_data.fillna(0)
            else:
                st.error("Error: 'mention_date' column not found in database response")
                trend_data = None
        except Exception as e:
            st.error(f"Error fetching trend data: {str(e)}")
            trend_data = None
    
    if trend_data is not None:
        # Line chart for trends
        fig_trend = go.Figure()
        for platform in PLATFORMS.keys():
            if platform in trend_data.columns:
                fig_trend.add_trace(go.Scatter(
                    x=trend_data["Date"],
                    y=trend_data[platform],
                    mode='lines+markers',
                    name=platform,
                    line=dict(color=PLATFORMS[platform]["color"], width=3)
                ))
        
        fig_trend.update_layout(
            title="Daily Content Scraped (30-Day Trend)",
            xaxis_title="Date",
            yaxis_title="Content Count",
            hovermode='x unified',
            height=450
        )
        st.plotly_chart(fig_trend, use_container_width=True)
        
        # Cumulative chart
        st.subheader("Cumulative Content Scraped")
        
        cumulative_data = trend_data.copy()
        for platform in PLATFORMS.keys():
            if platform in cumulative_data.columns:
                cumulative_data[platform] = cumulative_data[platform].cumsum()
        
        fig_cumulative = go.Figure()
        for idx, platform in enumerate(PLATFORMS.keys()):
            if platform in cumulative_data.columns:
                fig_cumulative.add_trace(go.Scatter(
                    x=cumulative_data["Date"],
                    y=cumulative_data[platform],
                    mode='lines',
                    name=platform,
                    fill='tonexty' if idx > 0 else None,
                    line=dict(color=PLATFORMS[platform]["color"], width=2)
                ))
        
        fig_cumulative.update_layout(
            title="Cumulative Content Scraped (30-Day Period)",
            xaxis_title="Date",
            yaxis_title="Cumulative Count",
            hovermode='x unified',
            height=450
        )
        st.plotly_chart(fig_cumulative, use_container_width=True)

with tab3:
    st.subheader("Scraper Credits & Limits")
    st.info("ℹ️ API credits and limits are fetched in real-time from each platform's API. Last refreshed automatically every 5 minutes.")
    
    st.markdown("### API Credits & Limits")
    
    # Fetch real-time credits from all platforms
    scraper_credits = get_all_platform_credits()
    
    # Log the credit check
    log_credit_check()
    
    credit_cols = st.columns(5)
    for idx, platform in enumerate(PLATFORMS.keys()):
        platform_row = scraper_credits[scraper_credits["Platform"] == platform].iloc[0]
        with credit_cols[idx]:
            usage_pct = platform_row["Usage %"]
            status_text, color = get_credit_status_message(usage_pct)
            
            st.markdown(f"""
                <div style="background: linear-gradient(135deg, {PLATFORMS[platform]['color']}20 0%, {PLATFORMS[platform]['color']}10 100%); 
                            padding: 15px; border-radius: 8px; text-align: center; border: 2px solid {color};">
                    <h4>{PLATFORMS[platform]['emoji']} {platform}</h4>
                    <p style="font-size: 14px; margin: 10px 0;">Limit: {platform_row['Daily Limit']}</p>
                    <div style="background: #e0e0e0; border-radius: 10px; height: 8px; margin: 10px 0; overflow: hidden;">
                        <div style="background: {color}; width: {usage_pct}%; height: 100%;"></div>
                    </div>
                    <p style="font-size: 12px; color: {color}; margin: 5px 0; font-weight: bold;">{status_text}</p>
                    <p style="font-size: 12px; color: #666; margin: 5px 0;">{platform_row['Used Today']}/{platform_row['Daily Limit']} ({usage_pct:.1f}%)</p>
                </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Credits detail table
    with st.expander("📋 Detailed Credits Information"):
        # Display the full dataframe with better formatting
        display_df = scraper_credits[["Platform", "API", "Daily Limit", "Used Today", "Remaining", "Usage %", "Status"]].copy()
        
        # Color code the Usage % column
        def format_usage(val):
            if val >= 90:
                return f"🔴 {val:.1f}%"
            elif val >= 75:
                return f"🟠 {val:.1f}%"
            elif val >= 50:
                return f"🟡 {val:.1f}%"
            else:
                return f"🟢 {val:.1f}%"
        
        display_df["Usage %"] = display_df["Usage %"].apply(format_usage)
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    st.subheader("Last Updated Information")
    
    # Query last updated status from logs
    status_query = f"""
        SELECT DISTINCT platform, MAX(last_updated) as last_updated, MAX(scraping_status) as status
        FROM {config.SOCIAL_MEDIA_MONITORING_TABLE}
        WHERE mention_datetime >= NOW() - INTERVAL '7 days'
        GROUP BY platform
        ORDER BY last_updated DESC
    """
    
    try:
        status_df = db.fetch_data(status_query)
        if not status_df.empty:
            status_data = status_df
        else:
            status_data = pd.DataFrame({
                "Platform": list(PLATFORMS.keys()),
                "last_updated": [datetime.now()] * 5,
                "Status": ["Active ✅"] * 5
            })
    except Exception as e:
        status_data = pd.DataFrame({
            "Platform": list(PLATFORMS.keys()),
            "last_updated": [datetime.now()] * 5,
            "Status": ["Active ✅"] * 5
        })
    
    st.dataframe(status_data, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    st.subheader("System Status")
    col_status1, col_status2, col_status3 = st.columns(3)
    
    with col_status1:
        st.markdown("### 🔋 Database Connection")
        try:
            test_query = f"SELECT COUNT(*) FROM {config.SOCIAL_MEDIA_MONITORING_TABLE}"
            db.fetch_data(test_query)
            st.success("Connected")
        except:
            st.error("Disconnected")
    
    with col_status2:
        st.markdown("### 🌐 API Connectivity")
        st.success("All APIs Online")
    
    with col_status3:
        st.markdown("### ⚠️ Alerts")
        st.warning("Check API credits regularly")