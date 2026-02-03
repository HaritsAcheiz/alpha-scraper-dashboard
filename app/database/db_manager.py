import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# Global cache for engines - creates one pool per unique connection string
@st.cache_resource
def get_engine(connection_name: str) -> Engine:
    """
    Creates a connection pool for the specific database.
    pool_pre_ping=True automatically handles lost connections.
    """
    try:
        # Load config from secrets.toml
        db_conf = st.secrets["connections"][connection_name]
        
        # Construct URL: postgresql+psycopg2://user:pass@host:port/dbname
        url = f"{db_conf['dialect']}+psycopg2://{db_conf['username']}:{db_conf['password']}@{db_conf['host']}:{db_conf['port']}/{db_conf['database']}"
        
        return create_engine(
            url,
            pool_size=5,        # Baseline connections to keep open
            max_overflow=10,    # Allow bursts of traffic
            pool_pre_ping=True  # Vital for preventing "server closed connection" errors
        )
    except Exception as e:
        st.error(f"❌ Failed to initialize connection pool for {connection_name}: {e}")
        return None

class DatabaseManager:
    def __init__(self, connection_name: str):
        self.connection_name = connection_name

    def _get_engine(self):
        return get_engine(self.connection_name)

    def fetch_data(self, query: str, params: dict = None) -> pd.DataFrame:
        """Safe Read: Pandas automatically manages the connection open/close"""
        engine = self._get_engine()
        if not engine: return pd.DataFrame()
        
        try:
            return pd.read_sql_query(query, engine, params=params)
        except Exception as e:
            st.error(f"❌ Read Error ({self.connection_name}): {e}")
            return pd.DataFrame()

    def execute_query(self, query: str, params: dict = None) -> tuple[bool, str]:
        """Safe Write: Transactional execution"""
        engine = self._get_engine()
        if not engine: return False, "No connection"

        try:
            with engine.begin() as conn: # Automatically commits or rollbacks
                conn.execute(text(query), params or {})
            return True, "✅ Success"
        except Exception as e:
            return False, f"❌ Write Error: {e}"