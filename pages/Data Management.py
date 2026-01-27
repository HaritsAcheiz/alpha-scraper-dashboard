"""
Data Management Page
"""
import streamlit as st
from database.db_manager import DatabaseManager
import config
import pandas as pd

st.set_page_config(layout="wide")

# Get database manager from session
if "management_db" not in st.session_state:
    st.session_state.management_db = DatabaseManager(config.MANAGEMENT_DB_CONFIG)

db_manager = st.session_state.management_db

st.markdown('<p class="main-header">Data Management</p>', unsafe_allow_html=True)

# Load data
df = db_manager.get_all_data(config.MANAGEMENT_TABLE)

# Tabs for different operations
tab1, tab2, tab3, tab4 = st.tabs(["👀 View", "➕ Add", "✏️ Edit", "🗑️ Delete"])

with tab1:
    st.subheader("View All Records")
    
    if df.empty:
        st.warning("No data available")
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
    
    schema_df = db_manager.get_table_info(config.MANAGEMENT_TABLE)
    # Fetch sample data for placeholders
    sample_df = db_manager.get_all_data(config.MANAGEMENT_TABLE).head(1)
    
    if schema_df.empty:
        st.error(f"❌ Table '{config.MANAGEMENT_TABLE}' not found.")
    else:
        form_fields = schema_df[~schema_df['column_name'].str.lower().isin(['id'])]
        
        with st.form("add_record_form", clear_on_submit=True):
            new_record_data = {}
            ui_cols = st.columns(2)
            
            for idx, row in form_fields.reset_index().iterrows():
                col_name = row['column_name']
                data_type = row['data_type'].lower()
                
                # Use pd.isna() to safely check for Null/NaN values
                example_val = sample_df[col_name].iloc[0] if not sample_df.empty else None
                is_val_null = pd.isna(example_val) or example_val is None
                
                with ui_cols[idx % 2]:
                    if 'int' in data_type:
                        # Safely convert to int, defaulting to 0 if NaN/Null
                        default_int = int(example_val) if not is_val_null else 0
                        new_record_data[col_name] = st.number_input(f"{col_name}", step=1, value=default_int)
                        
                    elif any(t in data_type for t in ['numeric', 'decimal', 'real', 'double']):
                        # Safely convert to float, defaulting to 0.0 if NaN/Null
                        default_float = float(example_val) if not is_val_null else 0.0
                        new_record_data[col_name] = st.number_input(f"{col_name}", step=0.01, format="%.2f", value=default_float)
                        
                    elif 'date' in data_type or 'timestamp' in data_type:
                        new_record_data[col_name] = st.date_input(f"{col_name}")
                        
                    elif 'bool' in data_type:
                        default_bool = bool(example_val) if not is_val_null else False
                        new_record_data[col_name] = st.checkbox(f"{col_name}", value=default_bool)
                        
                    else:
                        # For text/string, use the example as a placeholder only
                        placeholder_text = f"e.g., {example_val}" if not is_val_null else ""
                        new_record_data[col_name] = st.text_input(f"{col_name}", placeholder=placeholder_text)

            submit_btn = st.form_submit_button("💾 Save Record", width="stretch")
            
            if submit_btn:
                success, message = db_manager.insert_record(config.MANAGEMENT_TABLE, new_record_data)
                if success:
                    st.success(message)
                    st.rerun() 
                else:
                    st.error(message)

with tab3:
    st.subheader("✏️ Edit Existing Record")
    st.write("Edit form would appear here")

with tab4:
    st.subheader("🗑️ Delete Record")
    st.write("Delete confirmation would appear here")
