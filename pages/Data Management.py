"""
Data Management Page
"""
import streamlit as st
from database.db_manager import DatabaseManager
import config

# Get database manager from session
if "db_manager" not in st.session_state:
    st.session_state.db_manager = DatabaseManager(config.DB_CONFIG)

db_manager = st.session_state.db_manager

st.markdown('<p class="main-header">🗂️ Data Management</p>', unsafe_allow_html=True)

# Load data
df = db_manager.get_all_data(config.TABLE_NAME)

# Tabs for different operations
tab1, tab2, tab3, tab4 = st.tabs(["👀 View", "➕ Add", "✏️ Edit", "🗑️ Delete"])

with tab1:
    st.subheader("📋 View All Records")
    
    if df.empty:
        st.warning("⚠️ No data available")
    else:
        # Search and filter
        col1, col2 = st.columns([2, 1])
        with col1:
            search_col = st.selectbox("Search in column", ["All"] + df.columns.tolist())
        with col2:
            search_term = st.text_input("Search term", "")
        
        # Apply filter
        if search_term and search_col != "All":
            filtered_df = df[df[search_col].astype(str).str.contains(search_term, case=False, na=False)]
        elif search_term:
            filtered_df = df[df.astype(str).apply(lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)]
        else:
            filtered_df = df
        
        st.info(f"Showing {len(filtered_df)} of {len(df)} records")
        st.dataframe(filtered_df, width='stretch', height=400, hide_index=True)

with tab2:
    st.subheader("➕ Add New Record")
    st.write("Add new record form would appear here")

with tab3:
    st.subheader("✏️ Edit Existing Record")
    st.write("Edit form would appear here")

with tab4:
    st.subheader("🗑️ Delete Record")
    st.write("Delete confirmation would appear here")
