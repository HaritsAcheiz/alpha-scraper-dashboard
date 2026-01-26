"""
Data Visualization Page
"""
import streamlit as st
import plotly.express as px
from database.db_manager import DatabaseManager
from utils.helpers import display_metrics, get_numeric_columns, get_categorical_columns, create_download_button, apply_custom_css
import config

# Apply custom styling
apply_custom_css()

# Initialize database manager in session state
if "db_manager" not in st.session_state:
    st.session_state.db_manager = DatabaseManager(config.DB_CONFIG)

db_manager = st.session_state.db_manager

st.markdown('<p class="main-header">📈 Data Visualization</p>', unsafe_allow_html=True)

# Load data
df = db_manager.get_all_data(config.TABLE_NAME)

if df.empty:
    st.warning("⚠️ No data available in the table")
else:
    # Summary metrics
    st.subheader("📊 Summary Statistics")
    display_metrics(df)
    
    st.markdown("---")
    
    # Data preview
    st.subheader("📋 Data Preview")
    st.dataframe(df.head(10), use_container_width=True, height=300)
    
    st.markdown("---")
    
    # Visualizations
    st.subheader("📊 Charts & Analysis")
    
    numeric_cols = get_numeric_columns(df)
    categorical_cols = get_categorical_columns(df)
    
    if numeric_cols:
        tab1, tab2, tab3 = st.tabs(["📊 Distribution", "📈 Trends", "🔍 Comparison"])
        
        with tab1:
            st.info("Distribution charts for numeric columns")
            col = st.selectbox("Select column to visualize", numeric_cols)
            if col:
                fig = px.histogram(df, x=col, nbins=30, title=f"Distribution of {col}")
                st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            st.info("Trend analysis")
            st.write("Trend charts would appear here")
        
        with tab3:
            st.info("Comparison charts")
            st.write("Comparison charts would appear here")
    else:
        st.info("ℹ️ No numeric columns available for visualization")
