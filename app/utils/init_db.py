import streamlit as st
from database.db_manager import DatabaseManager

def get_manager(target: str) -> DatabaseManager:
    """
    Factory function to get the correct DB manager.
    target: 'dashboard_db' or 'management_db' (keys in secrets.toml)
    """
    session_key = f"db_mgr_{target}"
    
    if session_key not in st.session_state:
        st.session_state[session_key] = DatabaseManager(target)
        
    return st.session_state[session_key]