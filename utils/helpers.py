"""
Helper functions and utilities
"""
import streamlit as st
from datetime import datetime


def apply_custom_css():
    """Apply custom CSS styling"""
    st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: bold;
            color: #1f77b4;
            margin-bottom: 1rem;
        }
        .sub-header {
            font-size: 1.5rem;
            color: #555;
            margin-bottom: 1rem;
        }
        </style>
    """, unsafe_allow_html=True)


def display_metrics(df):
    """Display summary metrics"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Records", f"{len(df):,}")
    with col2:
        st.metric("Total Columns", len(df.columns))
    with col3:
        numeric_cols = df.select_dtypes(include=['number']).columns
        st.metric("Numeric Columns", len(numeric_cols))
    with col4:
        st.metric("Data Updated", datetime.now().strftime("%H:%M:%S"))


def get_numeric_columns(df):
    """Get list of numeric columns"""
    return df.select_dtypes(include=['number']).columns.tolist()


def get_categorical_columns(df):
    """Get list of categorical columns"""
    return df.select_dtypes(include=['object', 'category']).columns.tolist()


def create_download_button(df, table_name):
    """Create CSV download button"""
    csv = df.to_csv(index=False).encode('utf-8')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name=f"{table_name}_{timestamp}.csv",
        mime="text/csv",
        width='stretch'
    )