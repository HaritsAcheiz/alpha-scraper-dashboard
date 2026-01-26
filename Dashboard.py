import streamlit as st
import pandas as pd
import plotly.express as px
from database.db_manager import DatabaseManager
from utils.helpers import apply_custom_css
import config

# 1. Page Configuration
st.set_page_config(page_title="News Source Monitor", layout="wide")
apply_custom_css()

# Initialize Database Connection
if "db_manager" not in st.session_state:
    st.session_state.db_manager = DatabaseManager(config.DB_CONFIG)

db_manager = st.session_state.db_manager

st.markdown('<p class="main-header">📊 News Source Status</p>', unsafe_allow_html=True)

# 2. Data Loading from PostgreSQL
df = db_manager.get_all_data(config.TABLE_NAME)

if df.empty:
    st.warning("⚠️ No data found in the PostgreSQL table.")
else:
    # --- 1. KPI CARDS ---
    st.subheader("📌 Overview")
    col1, col2, col3, col4= st.columns(4)

    with col1:
        # Total News Source (webname)
        total_sources = df['url'].shape[0]
        st.metric("Total News Source", f"{total_sources}")

    with col2:
        # Total Active News Source (is_active is True)
        total_active = df[df['is_active'] == True].shape[0]
        st.metric("Total Active News Source", f"{total_active}")

    with col3:
        # Total Static News Source Page (useselenium is False)
        total_static = df[df['useselenium'] == False].shape[0]
        st.metric("Total Static News Source Page", f"{total_static}")

    with col4:
        # Total Dynamic News Source Page (useselenium is True)
        total_dynamic = df[df['useselenium'] == True].shape[0]
        st.metric("Total Dynamic News Source Page", f"{total_dynamic}")

    st.markdown("---")

    # --- 2. FAILED SCRAPER BAR GRAPH ---
    st.subheader("🚫 Failures by Remark")

    # Define the failure statuses based on your requirements
    failure_types = ['Failed (Page Not Found)', 'Failed (Invalid Selector)']
    
    # Filter only for failed records
    failed_df = df[df['remarks'].isin(failure_types)].copy()

    if not failed_df.empty:
        # Group by 'scope' (Category) to get total failure count per category
        failure_by_cat = failed_df.groupby('remarks').size().reset_index(name='total_failures')
        
        # Create the Bar Chart
        fig = px.bar(
            failure_by_cat, 
            x='remarks', 
            y='total_failures',
            color='remarks',
            title="Failures by Remarks",
            labels={'scope': 'Category', 'total_failures': 'Total Failures'},
            text_auto=True
        )

        fig.update_layout(
            xaxis_title="Category (Remarks)",
            yaxis_title="Count of Failures",
            showlegend=False,
            template="plotly_white",
            height=500
        )
        
        st.plotly_chart(fig, width='stretch')
        
        # Optional: Breakdown table for the specific types of failures
        with st.expander("🔍 Detailed Failure Breakdown"):
            breakdown = failed_df.groupby(['remarks']).size().reset_index(name='count')
            st.dataframe(breakdown, width='stretch', hide_index=True)

        # --- 3. DATA PREVIEW ---
        with st.expander("📋 View Failed Records"):
            # Filter for the specific failure types
            failure_types = ['Failed (Page Not Found)', 'Failed (Invalid Selector)']
            filtered_df = df[df['remarks'].isin(failure_types)]
            
            st.dataframe(filtered_df, width='stretch', hide_index=True)
            
    else:
        st.success("✅ No failures detected. All scrapers are returning 'Success'.")