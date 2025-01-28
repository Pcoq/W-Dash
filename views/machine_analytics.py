import streamlit as st
import plotly.express as px
import pandas as pd
from io import BytesIO
from utils.excel_utils import to_excel

def render_machine_analytics(orders_df):
    st.header("Machine Analyse")
    
    # Convert defect_date to datetime if it's not already
    orders_df['defect_date'] = pd.to_datetime(orders_df['defect_date'])
    
    # Filters row
    col1, col2, col3, col4, col5, col6 = st.columns(6)  # Voeg een zesde kolom toe voor het klantfilter
    
    with col1:
        # Year filter
        years = orders_df['defect_date'].dt.year.unique()
        years = sorted(years, reverse=True)  # Meest recente jaren eerst
        selected_year = st.selectbox("Selecteer Jaar", years)
    
    with col2:
        # Customer filter
        customers = sorted([x for x in orders_df['client_name'].unique() if pd.notna(x)])
        selected_customer = st.multiselect("Selecteer Klanten", customers)
    
    with col3:
        # Brand filter
        brands = orders_df['machine_brand'].unique()
        selected_brand = st.multiselect("Selecteer Merken", brands)
    
    with col4:
        # Model filter
        if selected_brand:
            models = orders_df[orders_df['machine_brand'].isin(selected_brand)]['machine_model'].unique()
        else:
            models = orders_df['machine_model'].unique()
        selected_model = st.multiselect("Selecteer Modellen", models)
    
    with col5:
        # Service category filter
        service_categories = orders_df['category'].unique()
        selected_categories = st.multiselect("Selecteer Service Categorieën", service_categories)
    
    with col6:
        # Nulfacturen includeren filter
        zero_invoice_filter = st.selectbox("Nulfacturen Includeren", options=["Ja", "Nee"], index=0)
    
    # Apply filters
    filtered_df = orders_df[orders_df['defect_date'].dt.year == selected_year]
    
    if selected_customer:
        filtered_df = filtered_df[filtered_df['client_name'].isin(selected_customer)]
    
    if selected_brand:
        filtered_df = filtered_df[filtered_df['machine_brand'].isin(selected_brand)]
    
    if selected_model:
        filtered_df = filtered_df[filtered_df['machine_model'].isin(selected_model)]
    
    if selected_categories:
        filtered_df = filtered_df[filtered_df['category'].isin(selected_categories)]
    
    # Pas de nulfactuurfilter toe
    if zero_invoice_filter == "Nee":
        filtered_df = filtered_df[filtered_df['zero_invoice'] == False]
    
    # Orders by machine model - Top 30
    orders_by_model = (
        filtered_df.groupby(['machine_brand', 'machine_model'])
        .size()
        .reset_index(name='count')
        .sort_values('count', ascending=False)
        .head(30)
    )
    
    # Export knop voor orders data
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(f"Top 30 Machine Modellen op Aantal Orders ({selected_year})")
    with col2:
        excel_data = to_excel(orders_by_model)
        st.download_button(
            label="Export",
            data=excel_data,
            file_name=f'orders_by_machine_{selected_year}.xlsx',
            mime='application/vnd.ms-excel'
        )
    
    fig_orders = px.bar(
        orders_by_model,
        x='machine_model',
        y='count',
        color='machine_brand',
        labels={
            'count': 'Aantal Orders',
            'machine_model': 'Machine Model',
            'machine_brand': 'Merk'
        }
    )
    
    # Voeg bedragen toe aan de grafiekkolommen voor orders by machine
    fig_orders.update_traces(texttemplate='%{y:,.0f}', textposition='outside')
    
    st.plotly_chart(fig_orders, use_container_width=True)
    
    # Costs by machine model - Top 30
    costs_by_model = (
        filtered_df.groupby(['machine_brand', 'machine_model'])
        .agg({
            'total_labour_cost': 'sum',
            'total_parts_cost': 'sum'
        })
        .reset_index()
    )
    
    # Add total cost for sorting
    costs_by_model['total_cost'] = costs_by_model['total_labour_cost'] + costs_by_model['total_parts_cost']
    costs_by_model = costs_by_model.sort_values('total_cost', ascending=False).head(30)
    
    # Export knop voor costs data
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(f"Top 30 Machine Modellen op Totale Kosten ({selected_year})")
    with col2:
        excel_data = to_excel(costs_by_model)
        st.download_button(
            label="Export",
            data=excel_data,
            file_name=f'costs_by_machine_{selected_year}.xlsx',
            mime='application/vnd.ms-excel'
        )
    
    fig_costs = px.bar(
        costs_by_model,
        x='machine_model',
        y=['total_labour_cost', 'total_parts_cost'],
        color_discrete_map={
            'total_labour_cost': '#00cc66',
            'total_parts_cost': '#0066cc'
        },
        labels={
            'value': 'Kosten (€)',
            'machine_model': 'Machine Model',
            'variable': 'Kostentype',
            'total_labour_cost': 'Arbeidskosten',
            'total_parts_cost': 'Onderdelen'
        },
        barmode='stack'
    )
    
    # Voeg bedragen toe aan de grafiekkolommen voor kosten per machine
    if not costs_by_model.empty:  # Controleer of er gegevens zijn
        # Add hover data with percentages
        total_costs = costs_by_model['total_cost']
        labour_pcts = (costs_by_model['total_labour_cost'] / total_costs * 100).round(1)
        parts_pcts = (costs_by_model['total_parts_cost'] / total_costs * 100).round(1)
        
        fig_costs.update_traces(
            hovertemplate="<br>".join([
                "Model: %{x}",
                "Kosten: €%{y:,.2f}",
                "Percentage van Totaal: %{customdata:.1f}%"
            ])
        )
        
        fig_costs.data[0].customdata = labour_pcts
        fig_costs.data[1].customdata = parts_pcts
    else:
        st.warning("Geen gegevens beschikbaar voor de geselecteerde filters.")
    
    st.plotly_chart(fig_costs, use_container_width=True)
    
    # Machine overview metrics
    st.subheader("Machine Overzicht")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Totaal Machine Modellen", 
                 len(filtered_df[['machine_brand', 'machine_model']].drop_duplicates()))
    with col2:
        st.metric("Gemiddelde Kosten per Order", 
                 f"{filtered_df['total_labour_cost'].mean() + filtered_df['total_parts_cost'].mean():,.2f}")
    with col3:
        st.metric("Totaal Orders", 
                 len(filtered_df))
