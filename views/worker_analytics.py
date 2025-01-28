import streamlit as st
import plotly.express as px
from utils.data_processing import process_worker_productivity
import pandas as pd
from datetime import datetime, timedelta
from utils.excel_utils import to_excel

def render_worker_analytics(worker_labours_df, orders_df):
    st.header("Medewerker Analyse")
    
    # Convert dates to datetime
    orders_df['created_at'] = pd.to_datetime(orders_df['created_at'])
    worker_labours_df['created_at'] = pd.to_datetime(worker_labours_df['created_at'])
    
    # Date range filter
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Datum",
            datetime.now() - timedelta(days=30)
        )
    with col2:
        end_date = st.date_input(
            "Eind Datum",
            datetime.now()
        )
    
    # Filter both datasets by date range
    filtered_orders = orders_df[
        (orders_df['created_at'].dt.date >= start_date) &
        (orders_df['created_at'].dt.date <= end_date)
    ]
    
    filtered_labours = worker_labours_df[
        (worker_labours_df['created_at'].dt.date >= start_date) &
        (worker_labours_df['created_at'].dt.date <= end_date)
    ]
    
    # Worker productivity metrics
    productivity = process_worker_productivity(filtered_labours)
    
    # Worker filters
    workers = sorted(productivity['worker_name'].unique())
    selected_workers = st.multiselect("Selecteer Medewerkers", workers)
    
    if selected_workers:
        filtered_productivity = productivity[productivity['worker_name'].isin(selected_workers)]
    else:
        filtered_productivity = productivity
    
    # Productiviteit sectie
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(f"Productiviteit per Medewerker ({start_date.strftime('%d-%m-%Y')} - {end_date.strftime('%d-%m-%Y')})")
    
    # Tasks by worker
    fig_tasks = px.bar(
        filtered_productivity,
        x='worker_name',
        y='total_tasks',
        labels={
            'worker_name': 'Medewerker',
            'total_tasks': 'Aantal Taken'
        }
    )
    st.plotly_chart(fig_tasks, use_container_width=True)
    
    # Average rate by worker
    fig_rate = px.bar(
        filtered_productivity,
        x='worker_name',
        y='avg_rate',
        labels={
            'worker_name': 'Medewerker',
            'avg_rate': 'Gemiddeld Uurtarief (€)'
        }
    )
    st.plotly_chart(fig_rate, use_container_width=True)
    
    # Worker details
    if selected_workers:
        st.subheader("Medewerker Details")
        for worker in selected_workers:
            worker_df = filtered_labours[filtered_labours['worker_name'] == worker]
            if not worker_df.empty:
                st.write(f"### {worker}")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Totaal Taken", len(worker_df))
                with col2:
                    st.metric("Gemiddeld Uurtarief", 
                             f"€{worker_df['price_per_hour'].mean():.2f}")
                with col3:
                    st.metric("Unieke Orders", 
                             len(worker_df['order_number'].unique()))
