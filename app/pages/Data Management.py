import streamlit as st
import pandas as pd
import config
from utils.init_db import get_manager
from utils.auth import require_login, sidebar_logout
import time
from datetime import datetime

# Page Configuration
st.set_page_config(layout="wide", page_title="Data Management")

authenticator = require_login()
sidebar_logout(authenticator)

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

# --- TAB 2: ADD RECORD ---
with tab2:
    st.subheader("➕ Add New Record")
    
    if "." in config.MANAGEMENT_TABLE:
        schema_name, table_name = config.MANAGEMENT_TABLE.split(".", 1)
    else:
        schema_name, table_name = 'public', config.MANAGEMENT_TABLE

    schema_query = f"""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = '{schema_name}' 
        AND table_name = '{table_name}'
    """
    schema_df = db.fetch_data(schema_query)
    sample_df = df.head(1) if not df.empty else pd.DataFrame()

    if "add_msg" in st.session_state:
        st.success(st.session_state["add_msg"])
        del st.session_state["add_msg"]

    if schema_df.empty:
        st.error(f"❌ Could not find structure for table '{config.MANAGEMENT_TABLE}'.")
    else:
        # 1. HIDE the system columns from the UI
        exclude_cols = ['id', 'created_at', 'last_updated_at']
        form_fields = schema_df[~schema_df['column_name'].str.lower().isin(exclude_cols)]
        
        with st.form("add_record_form", clear_on_submit=True):
            new_record_data = {}
            ui_cols = st.columns(2)
            
            for idx, row in form_fields.reset_index().iterrows():
                col_name = row['column_name']
                data_type = row['data_type'].lower()
                example_val = sample_df[col_name].iloc[0] if not sample_df.empty and col_name in sample_df.columns else None
                is_val_null = pd.isna(example_val)
                
                with ui_cols[idx % 2]:
                    if 'int' in data_type:
                        default_int = int(example_val) if not is_val_null and str(example_val).isdigit() else 0
                        new_record_data[col_name] = st.number_input(f"{col_name}", step=1, value=default_int)
                    elif any(t in data_type for t in ['numeric', 'decimal', 'real', 'double', 'float']):
                        default_float = float(example_val) if not is_val_null else 0.0
                        new_record_data[col_name] = st.number_input(f"{col_name}", step=0.01, format="%.2f", value=default_float)
                    elif 'date' in data_type or 'timestamp' in data_type:
                        new_record_data[col_name] = st.date_input(f"{col_name}")
                    elif 'bool' in data_type:
                        default_bool = bool(example_val) if not is_val_null else False
                        new_record_data[col_name] = st.checkbox(f"{col_name}", value=default_bool)
                    else:
                        placeholder_text = f"e.g., {example_val}" if not is_val_null else ""
                        new_record_data[col_name] = st.text_input(f"{col_name}", placeholder=placeholder_text)

            submit_btn = st.form_submit_button("💾 Save Record", use_container_width=True)
            
            if submit_btn:
                # 2. INJECT 'created_at' into the dictionary before saving
                new_record_data['created_at'] = datetime.now()
                for key, val in new_record_data.items():
                    if val == 0 and key.endswith('_id'):
                        new_record_data[key] = None
                    elif val == "":
                        new_record_data[key] = None
                
                # Dynamic SQL Generation (now automatically includes created_at!)
                columns_str = ", ".join(new_record_data.keys())
                placeholders_str = ", ".join([f":{col}" for col in new_record_data.keys()])
                insert_query = f"INSERT INTO {config.MANAGEMENT_TABLE} ({columns_str}) VALUES ({placeholders_str})"
                
                success, message = db.execute_query(insert_query, new_record_data)
                
                if success:
                    st.success("✅ Record added successfully!")
                    st.session_state["add_msg"] = "✅ Record added successfully!"
                    time.sleep(1.5)
                    st.rerun()
                else:
                    st.error(message)

# --- TAB 3: EDIT RECORD ---
with tab3:
    st.subheader("✏️ Edit Existing Record")
    
    if df.empty or 'id' not in df.columns:
        st.warning("No records available to edit, or table lacks an 'id' column.")
    else:
        # Simple text input for the search term
        search_term_edit = st.text_input("Enter Record ID or exact search term to edit:", key="text_search_edit")
        
        if search_term_edit:
            # 1. Try to find the record by exact ID first
            if search_term_edit.isdigit():
                filtered_df = df[df['id'] == int(search_term_edit)]
            # 2. Otherwise, search across all columns
            else:
                filtered_df = df[df.astype(str).apply(lambda x: x.str.contains(search_term_edit, case=False, na=False)).any(axis=1)]
            
            # Handle the results
            if filtered_df.empty:
                st.error("❌ No matching records found.")
            elif len(filtered_df) > 1:
                st.warning(f"⚠️ Found {len(filtered_df)} records. Please type the exact ID to edit.")
            else:
                # Exactly 1 record found! Load the form.
                current_record = filtered_df.iloc[0]
                record_id = int(current_record['id'])
                
                st.success(f"Editing Record ID: {record_id}")
                
                # Fetch schema safely
                schema_name, table_name = config.MANAGEMENT_TABLE.split(".", 1) if "." in config.MANAGEMENT_TABLE else ('public', config.MANAGEMENT_TABLE)
                schema_df = db.fetch_data(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = '{schema_name}' AND table_name = '{table_name}'")
                exclude_cols = ['id', 'created_at', 'last_updated_at']
                form_fields = schema_df[~schema_df['column_name'].str.lower().isin(exclude_cols)]
                
                with st.form("edit_record_form"):
                    update_data = {}
                    ui_cols = st.columns(2)
                    
                    for idx, row in form_fields.reset_index().iterrows():
                        col_name = row['column_name']
                        data_type = row['data_type'].lower()
                        current_val = current_record[col_name]
                        is_val_null = pd.isna(current_val)
                        
                        with ui_cols[idx % 2]:
                            if 'int' in data_type:
                                val = int(current_val) if not is_val_null else 0
                                update_data[col_name] = st.number_input(f"{col_name}", step=1, value=val, key=f"edit_{col_name}")
                            elif any(t in data_type for t in ['numeric', 'decimal', 'real', 'double', 'float']):
                                val = float(current_val) if not is_val_null else 0.0
                                update_data[col_name] = st.number_input(f"{col_name}", step=0.01, format="%.2f", value=val, key=f"edit_{col_name}")
                            elif 'date' in data_type or 'timestamp' in data_type:
                                val = pd.to_datetime(current_val).date() if not is_val_null else None
                                update_data[col_name] = st.date_input(f"{col_name}", value=val, key=f"edit_{col_name}")
                            elif 'bool' in data_type:
                                val = bool(current_val) if not is_val_null else False
                                update_data[col_name] = st.checkbox(f"{col_name}", value=val, key=f"edit_{col_name}")
                            else:
                                val = str(current_val) if not is_val_null else ""
                                update_data[col_name] = st.text_input(f"{col_name}", value=val, key=f"edit_{col_name}")

                    submit_edit = st.form_submit_button("💾 Save Changes", use_container_width=True)
                    
                    if submit_edit:

                        for key, val in update_data.items():
                            if val == 0 and key.endswith('_id'):
                                update_data[key] = None
                            elif val == "":
                                update_data[key] = None

                        set_clause = ", ".join([f"{col} = :{col}" for col in update_data.keys()])
                        update_query = f"UPDATE {config.MANAGEMENT_TABLE} SET {set_clause} WHERE id = :id"
                        update_data['id'] = record_id
                        
                        success, message = db.execute_query(update_query, update_data)
                        if success:
                            st.success(f"✅ Record updated successfully!")
                            
                            time.sleep(1.5)
                            
                            if "text_search_edit" in st.session_state:
                                del st.session_state["text_search_edit"]
                            
                            st.rerun()
                        else:
                            st.error(message)

# --- TAB 4: DELETE RECORD ---
with tab4:
    st.subheader("🗑️ Delete Record")
    
    if df.empty or 'id' not in df.columns:
        st.warning("No records available to delete, or table lacks an 'id' column.")
    else:
        # Simple text input for the search term
        search_term_del = st.text_input("Enter Record ID or exact search term to delete:", key="text_search_del")
        
        if search_term_del:
            # 1. Try to find the record by exact ID first
            if search_term_del.isdigit():
                filtered_df = df[df['id'] == int(search_term_del)]
            # 2. Otherwise, search across all columns
            else:
                filtered_df = df[df.astype(str).apply(lambda x: x.str.contains(search_term_del, case=False, na=False)).any(axis=1)]
            
            # Handle the results
            if filtered_df.empty:
                st.error("❌ No matching records found.")
            elif len(filtered_df) > 1:
                st.warning(f"⚠️ Found {len(filtered_df)} records. Please type the exact ID to delete.")
            else:
                # Exactly 1 record found! Show the delete warning.
                current_record = filtered_df.iloc[0]
                record_id = int(current_record['id'])
                display_val = current_record.iloc[1] if len(current_record) > 1 else record_id
                
                st.error(f"⚠️ Are you sure you want to delete **ID {record_id} ({display_val})**?")
                
                if st.button("🗑️ Confirm Delete", type="primary", use_container_width=True):
                    delete_query = f"DELETE FROM {config.MANAGEMENT_TABLE} WHERE id = :id"
                    success, message = db.execute_query(delete_query, {"id": record_id})
                    
                    if success:
                        st.success(f"✅ Record deleted successfully!")
                        time.sleep(1.5)
                            
                        if "text_search_del" in st.session_state:
                            del st.session_state["text_search_del"]

                        st.rerun()
                    else:
                        st.error(message)
            