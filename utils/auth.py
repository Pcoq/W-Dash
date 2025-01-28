import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if "password" not in st.session_state:
            st.session_state["password_correct"] = False
            return
            
        if st.session_state["password"] == os.environ.get("DASHBOARD_PASSWORD"):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.markdown(
            """
            <style>
            .stApp {
                background-color: white;
            }
            div[data-testid="stVerticalBlock"] > div:first-child {
                margin-top: 20vh !important;
            }
            </style>
            """, 
            unsafe_allow_html=True
        )
        
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.markdown('<p class="westtrac-title" style="text-align: center;">Westtrac</p>', unsafe_allow_html=True)
            st.text_input(
                "Wachtwoord", 
                type="password", 
                on_change=password_entered, 
                key="password"
            )
            if "password_correct" in st.session_state and not st.session_state["password_correct"]:
                st.error("😕 Wachtwoord incorrect")
        return False
    
    # Password correct.
    return st.session_state["password_correct"]