"""
Database operations and connection management
"""
import streamlit as st
import pandas as pd
import psycopg2
from typing import Tuple, Optional


class DatabaseManager:
    """Handles all database operations"""
    
    def __init__(self, config: dict):
        self.config = config
        self._connection = None
    
    @st.cache_resource
    def get_connection(_self):
        """Create and return PostgreSQL connection"""
        try:
            conn = psycopg2.connect(**_self.config)
            return conn
        except Exception as e:
            st.error(f"❌ Database connection failed: {e}")
            return None
    
    @st.cache_data(ttl=60)
    def fetch_data(_self, query: str) -> pd.DataFrame:
        """Fetch data from database with caching"""
        conn = _self.get_connection()
        if conn:
            try:
                # Use SQLAlchemy connection string to avoid pandas warning
                from sqlalchemy import create_engine
                engine = create_engine(f"postgresql://{_self.config['user']}:{_self.config['password']}@{_self.config['host']}:{_self.config['port']}/{_self.config['database']}")
                df = pd.read_sql_query(query, engine)
                return df
            except Exception as e:
                st.error(f"❌ Error loading data: {e}")
                return pd.DataFrame()
        return pd.DataFrame()
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> Tuple[bool, str]:
        """Execute INSERT, UPDATE, DELETE queries"""
        conn = self.get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                conn.commit()
                cursor.close()
                st.cache_data.clear()
                return True, "✅ Operation successful!"
            except Exception as e:
                conn.rollback()
                return False, f"❌ Error: {e}"
        return False, "❌ No database connection"
    
    def get_table_info(self, table_name: str) -> pd.DataFrame:
        """Get column information, handling schema-qualified names (e.g., 'schema.table')"""
        # Split schema and table if a dot exists
        if "." in table_name:
            schema, table = table_name.split(".", 1)
        else:
            schema, table = 'public', table_name

        query = f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = '{schema.lower()}' 
            AND table_name = '{table.lower()}'
            ORDER BY ordinal_position
        """
        return self.fetch_data(query)
    
    def get_all_data(self, table_name: str) -> pd.DataFrame:
        """Get all records from table"""
        return self.fetch_data(f"SELECT * FROM {table_name}")
    
    def insert_record(self, table_name: str, data: dict) -> Tuple[bool, str]:
        """Insert new record"""
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        return self.execute_query(query, tuple(data.values()))
    
    def update_record(self, table_name: str, pk_column: str, pk_value, data: dict) -> Tuple[bool, str]:
        """Update existing record"""
        set_clause = ", ".join([f"{col} = %s" for col in data.keys()])
        query = f"UPDATE {table_name} SET {set_clause} WHERE {pk_column} = %s"
        params = tuple(list(data.values()) + [pk_value])
        return self.execute_query(query, params)
    
    def delete_record(self, table_name: str, pk_column: str, pk_value) -> Tuple[bool, str]:
        """Delete record"""
        query = f"DELETE FROM {table_name} WHERE {pk_column} = %s"
        return self.execute_query(query, (pk_value,))