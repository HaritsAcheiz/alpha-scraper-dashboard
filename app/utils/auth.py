import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

def get_authenticator():
    """Loads config and returns the authenticator object."""
    with open('config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)

    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
        auto_hash = False
    )
    return authenticator

# def require_login():
#     """
#     Checks if user is logged in. 
#     Returns the authenticator object so it can be reused.
#     """
#     authenticator = get_authenticator() # <--- Created ONCE here
    
#     if st.session_state.get("authentication_status") is not True:
#         st.warning("Please log in to access this page.")
#         st.switch_page("Login.py")
#         st.stop()
    
#     return authenticator # <--- Return it!

def require_login():
    """
    Checks if user is logged in. 
    Returns the authenticator object so it can be reused.
    """
    authenticator = get_authenticator()
    
    # 🔴 CRITICAL FIX: This reads the cookie to restore the session!
    # We use 'unrendered' so it checks the cookie but doesn't draw a login box.
    try:
        authenticator.login('unrendered')
    except Exception as e:
        st.error(e)
    
    # Now that the session is restored from the cookie, we can check the status
    if st.session_state.get("authentication_status") is not True:
        st.warning("Please log in to access this page.")
        st.switch_page("Login.py")
        st.stop()
    
    return authenticator

# ⚠️ CHANGED: Now accepts 'authenticator' as an argument
def sidebar_logout(authenticator):
    """Adds a logout button to the sidebar"""
    if st.session_state.get("authentication_status"):
        authenticator.logout('Logout', 'sidebar')
        st.sidebar.write(f"User: *{st.session_state.get('name')}*")