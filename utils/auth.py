import os
import streamlit as st
from utils.user_management import login_user

def check_password():
    """Returns `True` if the user is logged in."""
    
    def login_attempt():
        """Handles login attempt"""
        result = login_user(
            st.session_state.email,
            st.session_state.password
        )
        if result['success']:
            st.session_state.user = result['user']
            st.session_state.authenticated = True
            del st.session_state.password
            # Redirect to main app
            st.rerun()
        else:
            st.session_state.authenticated = False
            st.error("😕 Ongeldige inloggegevens")

    if 'authenticated' not in st.session_state:
        # First run, show login form
        st.markdown('<p class="westtrac-title" style="text-align: center;">Westtrac IQ</p>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.text_input("Email", key="email")
            st.text_input("Wachtwoord", type="password", key="password")
            if st.button("Inloggen"):
                login_attempt()
        return False
        
    return st.session_state.authenticated