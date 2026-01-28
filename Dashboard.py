import streamlit as st
import pandas as pd
import plotly.express as px
from utils.helpers import apply_custom_css
import config
from utils.init_db import get_manager

# Page Configuration
st.set_page_config(page_title="News Source Monitor", layout="wide")
apply_custom_css()

db = get_manager("dashboard_db")

st.markdown('<p class="main-header">News Source Status</p>', unsafe_allow_html=True)

# Data Loading from PostgreSQL
df = db.fetch_data(f"SELECT * FROM {config.DASHBOARD_TABLE}")

if df.empty:
    st.warning("No data found in the PostgreSQL table.")
else:
    # KPI CARDS
    st.subheader("Overview")
    col1, col2, col3, col4= st.columns(4)

    with col1:
        # Total News Source
        total_sources = df['portal_url'].shape[0]
        st.metric("Total News Source", f"{total_sources}")

    with col2:
        # Total Status Success
        total_success = df[df['status'] == 'SUCCESS'].shape[0]
        st.metric("Total Success", f"{total_success}")

    with col3:
        # Total Status Failed
        total_failed = df[df['status'] == 'FAILED'].shape[0]
        st.metric("Total Failed", f"{total_failed}")

    with col4:
        # Latest Updated
        if 'updated_at' in df.columns:
            df['updated_at'] = pd.to_datetime(df['updated_at'])
            latest_date = df['updated_at'].max()
        else:
            latest_date = None

        if pd.notna(latest_date):
            display_date = latest_date.strftime("%d/%m/%y %H:%M")
        else:
            display_date = "N/A"
        st.metric("Last Updated", display_date)

    st.markdown("---")

    # FAILED SCRAPER BAR GRAPH
    st.subheader("Failures by Code")

    # Define the failure code based on your requirements
    failure_types = ['NO_PORTAL', 'NO_ARTICLE', 'BAD_SEL']
    
    # Filter only for failed records
    failed_df = df[df['failure_code'].isin(failure_types)].copy()

    if not failed_df.empty:
        failure_by_cat = failed_df.groupby('failure_code').size().reset_index(name='total_failures')
        
        # Create the Bar Chart
        fig = px.bar(
            failure_by_cat, 
            x='failure_code', 
            y='total_failures',
            color='failure_code',
            title="Failures by Code",
            labels={'scope': 'Category', 'total_failures': 'Total Failures'},
            text_auto=True
        )

        fig.update_layout(
            xaxis_title="Failure Code",
            yaxis_title="Count of Failures",
            showlegend=False,
            template="plotly_white",
            height=500
        )
        
        st.plotly_chart(fig, width='stretch')
        
        # Breakdown table for the specific types of failures
        with st.expander("🔍 Detailed Failure Breakdown"):
            breakdown = failed_df.groupby(['failure_code']).size().reset_index(name='count')
            st.dataframe(breakdown, width='stretch', hide_index=True)

        # # DATA PREVIEW
        # with st.expander("📋 View Failed Records"):
        #     # Filter for the specific failure types
        #     failure_types = ['NO_PORTAL', 'NO_ARTICLE', 'BAD_SEL']
        #     filtered_df = df[df['failure_code'].isin(failure_types)]
            
        #     st.dataframe(filtered_df, width='stretch', hide_index=True)
            
        with st.expander("📋 Data Preview with JSON Support"):
            failure_types = ['NO_PORTAL', 'NO_ARTICLE', 'BAD_SEL']
            filtered_df = df[df['failure_code'].isin(failure_types)]

            st.data_editor(
                filtered_df,
                column_config={
                    "remarks": st.column_config.JsonColumn(
                        "Remarks",
                        help="Detailed error logs in JSON format",
                    ),
                    "url": st.column_config.LinkColumn("Source URL"),
                },
                hide_index=True,
                width='stretch'
            )

    else:
        st.success("✅ No failures detected. All scrapers are returning 'Success'.")