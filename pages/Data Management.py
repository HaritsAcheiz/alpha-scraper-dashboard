"""
Data Management Page
"""
import streamlit as st
import pandas as pd
import config
from utils.init_db import get_manager

# Page Configuration
st.set_page_config(layout="wide", page_title="Data Management")

# Database Connection (Safe & Persistent)
try:
    db = get_manager("management_db")
except Exception as e:
    st.error(f"Failed to connect to database: {e}")
    st.stop()

st.markdown('<p class="main-header">Data Management</p>', unsafe_allow_html=True)

# Load Data
try:
    df = db.fetch_data(f"SELECT * FROM {config.MANAGEMENT_TABLE}")
except Exception as e:
    st.error(f"Error loading table: {e}")
    df = pd.DataFrame()

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["👀 View", "➕ Add", "✏️ Edit", "🗑️ Delete"])

# TAB 1: VIEW RECORDS
with tab1:
    st.subheader("View All Records")
    
    if df.empty:
        st.warning("No data available or table is empty.")
    else:
        # Search and Filter Layout
        col1, col2 = st.columns([2, 1])
        with col1:
            search_col = st.selectbox("Search in column", ["All"] + df.columns.tolist())
        with col2:
            search_term = st.text_input("Search term", "")
        
        # Apply Logic
        if search_term and search_col != "All":
            filtered_df = df[df[search_col].astype(str).str.contains(search_term, case=False, na=False)]
        elif search_term:
            filtered_df = df[df.astype(str).apply(lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)]
        else:
            filtered_df = df
        
        st.info(f"Showing {len(filtered_df)} of {len(df)} records")
        st.dataframe(filtered_df, width='stretch', height=500, hide_index=True)

# TAB 2: ADD RECORD
with tab2:
    st.subheader("➕ Add New Record")
    
    # Logic to split schema.table (e.g., 'from_news.news_source' -> schema='from_news', table='news_source')
    if "." in config.MANAGEMENT_TABLE:
        schema_name, table_name = config.MANAGEMENT_TABLE.split(".", 1)
    else:
        schema_name, table_name = 'public', config.MANAGEMENT_TABLE

    # Fetch Table Schema safely using raw SQL
    schema_query = f"""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = '{schema_name}' 
        AND table_name = '{table_name}'
    """
    schema_df = db.fetch_data(schema_query)
    
    # Fetch one row to guess default values/formats (optional but helpful UX)
    sample_df = df.head(1) if not df.empty else pd.DataFrame()

    if schema_df.empty:
        st.error(f"❌ Could not find structure for table '{config.MANAGEMENT_TABLE}'. Check your config.")
    else:
        # Exclude auto-increment ID columns usually named 'id'
        form_fields = schema_df[~schema_df['column_name'].str.lower().isin(['id'])]
        
        with st.form("add_record_form", clear_on_submit=True):
            new_record_data = {}
            ui_cols = st.columns(2)
            
            for idx, row in form_fields.reset_index().iterrows():
                col_name = row['column_name']
                data_type = row['data_type'].lower()
                
                # Try to get an example value to determine input type logic
                example_val = sample_df[col_name].iloc[0] if not sample_df.empty and col_name in sample_df.columns else None
                is_val_null = pd.isna(example_val)
                
                with ui_cols[idx % 2]:
                    # Integers
                    if 'int' in data_type:
                        default_int = int(example_val) if not is_val_null and str(example_val).isdigit() else 0
                        new_record_data[col_name] = st.number_input(f"{col_name}", step=1, value=default_int)
                        
                    # Floats/Decimals
                    elif any(t in data_type for t in ['numeric', 'decimal', 'real', 'double', 'float']):
                        default_float = float(example_val) if not is_val_null else 0.0
                        new_record_data[col_name] = st.number_input(f"{col_name}", step=0.01, format="%.2f", value=default_float)
                        
                    # Dates
                    elif 'date' in data_type or 'timestamp' in data_type:
                        new_record_data[col_name] = st.date_input(f"{col_name}")
                        
                    # Booleans
                    elif 'bool' in data_type:
                        default_bool = bool(example_val) if not is_val_null else False
                        new_record_data[col_name] = st.checkbox(f"{col_name}", value=default_bool)
                        
                    # Strings / Text (Default)
                    else:
                        placeholder_text = f"e.g., {example_val}" if not is_val_null else ""
                        new_record_data[col_name] = st.text_input(f"{col_name}", placeholder=placeholder_text)

            submit_btn = st.form_submit_button("💾 Save Record", width='stretch')
            
            if submit_btn:
                # Dynamic SQL Generation with Parameterized Queries
                # Columns: "url, source_name, is_active"
                columns_str = ", ".join(new_record_data.keys())
                
                # Placeholders: ":url, :source_name, :is_active"
                placeholders_str = ", ".join([f":{col}" for col in new_record_data.keys()])
                
                # Query Construction
                insert_query = f"INSERT INTO {config.MANAGEMENT_TABLE} ({columns_str}) VALUES ({placeholders_str})"
                
                # Execute
                success, message = db.execute_query(insert_query, new_record_data)
                
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

# TAB 3: EDIT RECORD
with tab3:
    st.subheader("✏️ Edit Existing Record")
    st.info("Select a record ID to edit.")
    
    # Simple ID selector for editing
    if not df.empty and 'id' in df.columns:
        record_id = st.selectbox("Select Record ID to Edit", df['id'].tolist())
        st.write(f"Editing functionality for ID {record_id} can be implemented here.")
        # Implementation would follow similar pattern to Add, but with UPDATE query
    else:
        st.write("No records available to edit.")

# TAB 4: DELETE RECORD
with tab4:
    st.subheader("🗑️ Delete Record")
    
    if not df.empty and 'id' in df.columns:
        delete_id = st.selectbox("Select Record ID to Delete", df['id'].tolist(), key='del_select')
        
        if st.button("Delete Selected Record", type="primary"):
            # Parameterized Delete Query
            delete_query = f"DELETE FROM {config.MANAGEMENT_TABLE} WHERE id = :id"
            success, message = db.execute_query(delete_query, {"id": delete_id})
            
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
    else:
        st.write("No records available to delete.")