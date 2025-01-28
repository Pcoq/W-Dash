import streamlit as st

# Page config moet eerst komen
st.set_page_config(
    page_title="Bedrijfs Analyse Dashboard",
    page_icon="📊",
    layout="wide"
)

# Daarna pas de andere imports
import pandas as pd
from utils.database import load_all_data
from views.client_analytics import render_client_analytics
from views.machine_analytics import render_machine_analytics
from views.worker_analytics import render_worker_analytics
from views.financial_analytics import render_financial_analytics
from utils.auth import check_password
from streamlit.web.server.server import Server
import socket

# Load custom CSS
with open('assets/custom.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Check password
if not check_password():
    st.stop()

# Sidebar navigation
st.sidebar.markdown('<p class="westtrac-title">Westtrac</p>', unsafe_allow_html=True)
st.sidebar.markdown("### Menu")

# Initialize states
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Klanten"

# Navigation items without icons
nav_items = [
    "Klanten",
    "Parts",
    "Machines",
    "Medewerkers",
    "Financieel",
    "Boekhouding Record Export",
    "KPI Dashboard",
    "Export Tool"
]

# Create navigation with radio buttons
selected = st.sidebar.radio(
    "Navigation",
    nav_items,
    label_visibility="collapsed",
    index=nav_items.index(st.session_state.current_page)
)

if selected != st.session_state.current_page:
    st.session_state.current_page = selected
    st.rerun()

page = st.session_state.current_page

# Main content area with loading state
with st.spinner('Data wordt geladen...'):
    # Laad alle data
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
        
    if not st.session_state.data_loaded:
        orders_df, worker_labours_df, parts_df, used_parts_df = load_all_data()
        st.session_state.orders_df = orders_df
        st.session_state.worker_labours_df = worker_labours_df
        st.session_state.parts_df = parts_df
        st.session_state.used_parts_df = used_parts_df
        st.session_state.data_loaded = True
    else:
        orders_df = st.session_state.orders_df
        worker_labours_df = st.session_state.worker_labours_df
        parts_df = st.session_state.parts_df
        used_parts_df = st.session_state.used_parts_df

    # Render selected dashboard
    if st.session_state.current_page == "Klanten":
        render_client_analytics(orders_df)
    elif st.session_state.current_page == "Machines":
        render_machine_analytics(orders_df)
    elif st.session_state.current_page == "Medewerkers":
        render_worker_analytics(worker_labours_df, orders_df)
    elif st.session_state.current_page == "Financieel":
        render_financial_analytics(orders_df, None)
    elif st.session_state.current_page == "Boekhouding Record Export":
        from views.accounting_export import render_accounting_export
        render_accounting_export(orders_df)
    elif st.session_state.current_page == "Parts":
        from views.parts_analysis import render_parts_analysis
        render_parts_analysis(parts_df, used_parts_df)
    elif st.session_state.current_page == "KPI Dashboard":
        from views.kpi_dashboard import render_kpi_dashboard
        render_kpi_dashboard()
    elif st.session_state.current_page == "Export Tool":
        from views.export_tool import render_export_tool
        render_export_tool()

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("### Data Laatst Bijgewerkt")
st.sidebar.text(pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"))

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

# Health check endpoint
@st.cache_resource
def setup_healthcheck():
    if not is_port_in_use(8501):
        st.success("Application is healthy")
        return True
    return False

setup_healthcheck()



