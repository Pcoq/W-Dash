import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from io import BytesIO
import pandas as pd
from utils.excel_utils import to_excel


def render_financial_analytics(orders_df, invoices_df):
    st.header("Financiële Analyse")
    
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
    
    # Filter data by date range
    filtered_orders = orders_df[
        (orders_df['created_at'].dt.date >= start_date) &
        (orders_df['created_at'].dt.date <= end_date)
    ]
    
    # Fill NaN/None values with 0 before calculations
    filtered_orders['total_labour_cost'] = filtered_orders['total_labour_cost'].fillna(0)
    filtered_orders['total_parts_cost'] = filtered_orders['total_parts_cost'].fillna(0)
    
    # Calculate total revenue for each order
    filtered_orders['total_revenue'] = filtered_orders['total_labour_cost'] + filtered_orders['total_parts_cost']
    
    # Revenue metrics
    st.subheader("Omzet Overzicht")
    col1, col2, col3, col4 = st.columns(4)
    
    total_revenue = filtered_orders['total_revenue'].sum()
    total_labour = filtered_orders['total_labour_cost'].sum()
    total_parts = filtered_orders['total_parts_cost'].sum()
    avg_order_value = filtered_orders['total_revenue'].mean()
    
    with col1:
        st.metric("Totale Omzet", f"€{total_revenue:,.2f}")
    with col2:
        st.metric("Arbeidskosten", f"€{total_labour:,.2f}")
    with col3:
        st.metric("Onderdelen", f"€{total_parts:,.2f}")
    with col4:
        st.metric("Gemiddelde Order Waarde", f"€{avg_order_value:,.2f}")
    
    # Revenue trend
    daily_revenue = filtered_orders.groupby(
        filtered_orders['created_at'].dt.date
    ).agg({
        'total_revenue': 'sum',
        'total_labour_cost': 'sum',
        'total_parts_cost': 'sum'
    }).reset_index()
    
    # Export knop voor dagelijkse omzet data
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("Dagelijkse Omzet Trend")
    with col2:
        excel_data = to_excel(daily_revenue)
        st.download_button(
            label="Export",
            data=excel_data,
            file_name=f'daily_revenue_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.xlsx',
            mime='application/vnd.ms-excel'
        )
    
    fig_revenue = go.Figure()
    
    # Add traces for total, labour and parts revenue
    fig_revenue.add_trace(go.Scatter(
        x=daily_revenue['created_at'],
        y=daily_revenue['total_revenue'],
        name='Totale Omzet',
        line=dict(color='#1f77b4', width=2)
    ))
    
    fig_revenue.add_trace(go.Scatter(
        x=daily_revenue['created_at'],
        y=daily_revenue['total_labour_cost'],
        name='Arbeidskosten',
        line=dict(color='#00cc66', width=1, dash='dot')
    ))
    
    fig_revenue.add_trace(go.Scatter(
        x=daily_revenue['created_at'],
        y=daily_revenue['total_parts_cost'],
        name='Onderdelen',
        line=dict(color='#0066cc', width=1, dash='dot')
    ))
    
    fig_revenue.update_layout(
        title="Dagelijkse Omzet Trend",
        xaxis_title="Datum",
        yaxis_title="Omzet (€)",
        hovermode='x unified'
    )
    
    st.plotly_chart(fig_revenue, use_container_width=True)
    
    # Revenue by category with split
    revenue_by_category = filtered_orders.groupby('category').agg({
        'total_labour_cost': 'sum',
        'total_parts_cost': 'sum'
    }).reset_index()
    
    revenue_by_category['total_revenue'] = (
        revenue_by_category['total_labour_cost'] + 
        revenue_by_category['total_parts_cost']
    )
    
    # Export knop voor omzet per categorie data
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("Omzetverdeling per Service Categorie")
    with col2:
        excel_data = to_excel(revenue_by_category)
        st.download_button(
            label="Export",
            data=excel_data,
            file_name=f'revenue_by_category_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.xlsx',
            mime='application/vnd.ms-excel'
        )
    
    fig_category = px.bar(
        revenue_by_category,
        x='category',
        y=['total_labour_cost', 'total_parts_cost'],
        labels={
            'value': 'Omzet (€)',
            'category': 'Service Categorie',
            'variable': 'Omzettype',
            'total_labour_cost': 'Arbeidskosten',
            'total_parts_cost': 'Onderdelen'
        },
        barmode='stack',
        color_discrete_map={
            'total_labour_cost': '#00cc66',
            'total_parts_cost': '#0066cc'
        }
    )
    
    st.plotly_chart(fig_category, use_container_width=True)
    
    # Export knop voor alle financiële data
    st.sidebar.markdown("---")
    excel_data = to_excel(filtered_orders)
    st.sidebar.download_button(
        label="Export",
        data=excel_data,
        file_name=f'financial_data_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.xlsx',
        mime='application/vnd.ms-excel'
    )
