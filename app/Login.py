import streamlit as st
import time
from utils.auth import get_authenticator

# Page Config
st.set_page_config(page_title="Login", layout="centered", initial_sidebar_state="collapsed")

# Hide Sidebar CSS
st.markdown("""<style>[data-testid="stSidebar"] {display: none;}</style>""", unsafe_allow_html=True)

st.title("🔐 Alpha Scraper Access")

# 1. Get the authenticator object
authenticator = get_authenticator()

# 2. Render the Login Widget
# ⚠️ CHANGE: Do not unpack variables here. Just call the function.
authenticator.login()

# 3. Handle the result using Session State
if st.session_state.get('authentication_status'):

    time.sleep(0.5)
    # Success!
    st.switch_page("pages/Dashboard.py")

elif st.session_state.get('authentication_status') is False:
    st.error('Username/password is incorrect')

elif st.session_state.get('authentication_status') is None:
    st.warning('Please enter your username and password')