import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from io import BytesIO
from utils.excel_utils import to_excel

def render_client_analytics(orders_df, client_turnover_df=None):
    st.header("Klant Analyse")
    
    # Convert defect_date to datetime if it's not already
    orders_df['defect_date'] = pd.to_datetime(orders_df['defect_date'])
    
    # Filters row
    col1, col2, col3, col4, col5 = st.columns(5)  # Voeg een vijfde kolom toe voor de nulfactuur filter
    
    with col1:
        # Year filter
        years = orders_df['defect_date'].dt.year.unique()
        years = sorted(years, reverse=True)  # Meest recente jaren eerst
        selected_year = st.selectbox("Selecteer Jaar", years)
    
    with col2:
        # Client filter
        clients = orders_df[orders_df['defect_date'].dt.year == selected_year]['client_name'].unique()
        selected_client = st.multiselect("Selecteer Klanten", clients)
    
    with col3:
        # Machine filter
        machines = orders_df[orders_df['defect_date'].dt.year == selected_year]['machine_model'].unique()
        selected_machines = st.multiselect("Selecteer Machines", machines)
    
    with col4:
        # Service category filter
        service_categories = orders_df['category'].unique()
        selected_categories = st.multiselect("Selecteer Service Categorieën", service_categories)
    
    with col5:
        # Nulfacturen includeren filter
        zero_invoice_filter = st.selectbox("Nulfacturen Includeren", options=["Ja", "Nee"], index=0)
    
    # Apply filters
    filtered_df = orders_df[orders_df['defect_date'].dt.year == selected_year]
    
    if selected_client:
        filtered_df = filtered_df[filtered_df['client_name'].isin(selected_client)]
    
    if selected_machines:
        filtered_df = filtered_df[filtered_df['machine_model'].isin(selected_machines)]
    
    if selected_categories:
        filtered_df = filtered_df[filtered_df['category'].isin(selected_categories)]
    
    # Pas de nulfactuurfilter toe
    if zero_invoice_filter == "Nee":
        filtered_df = filtered_df[filtered_df['zero_invoice'] == False]
    
    # If we have turnover data, add it to the analysis
    if client_turnover_df is not None:
        st.subheader("Klant Omzet Overzicht (Onderdelen Verkoop)")
        
        # Group turnover data by client
        client_turnover = (
            client_turnover_df.groupby('client_name')
            .agg({
                'total_price_with_discount': 'sum',
                'total_base_price': 'sum',
                'total_manual_discount': 'sum',
                'total_extra_discount': 'sum',
                'total_client_discount': 'sum'
            })
            .reset_index()
            .sort_values('total_price_with_discount', ascending=False)
            .head(30)
        )
        
        # Create columns for metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Totale Verkoop Omzet", 
                f"€{client_turnover['total_price_with_discount'].sum():,.2f}"
            )
        with col2:
            st.metric(
                "Totale Korting", 
                f"€{(client_turnover['total_manual_discount'] + client_turnover['total_extra_discount'] + client_turnover['total_client_discount']).sum():,.2f}"
            )
        with col3:
            st.metric(
                "Gemiddelde Order Waarde", 
                f"€{client_turnover['total_price_with_discount'].mean():,.2f}"
            )
        
        # Create bar chart for client turnover
        fig_turnover = px.bar(
            client_turnover,
            x='client_name',
            y='total_price_with_discount',
            title='Top 30 Klanten op Onderdelen Verkoop',
            labels={
                'client_name': 'Klant',
                'total_price_with_discount': 'Omzet (€)'
            }
        )
        
        fig_turnover.update_traces(
            text=client_turnover['total_price_with_discount'].apply(lambda x: f'€{x:,.2f}'),
            textposition='outside'
        )
        
        st.plotly_chart(fig_turnover, use_container_width=True)
    
    # Orders by client chart - Top 30
    orders_by_client = (
        filtered_df.groupby('client_name')
        .size()
        .reset_index(name='count')
        .sort_values('count', ascending=False)
        .head(30)
    )
    
    # Export knop voor orders data
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(f"Top 30 Klanten op Aantal Orders ({selected_year})")
    
    fig_orders = px.bar(
        orders_by_client,
        x='client_name', 
        y='count',
        labels={'count': 'Aantal Orders', 'client_name': 'Klant'}
    )
    st.plotly_chart(fig_orders, use_container_width=True)
    
    # Revenue by client chart - Top 30
    revenue_df = (
        filtered_df.groupby('client_name')
        .agg({
            'total_labour_cost': 'sum',
            'total_parts_cost': 'sum'
        })
        .assign(total_cost=lambda x: x['total_labour_cost'] + x['total_parts_cost'])
        .reset_index()
        .sort_values('total_cost', ascending=False)
        .head(30)
    )
    
    # Export knop voor revenue data
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(f"Top 30 Klanten op Totale Kosten ({selected_year})")
    
    fig_revenue = px.bar(
        revenue_df,
        x='client_name',
        y=['total_labour_cost', 'total_parts_cost'],
        labels={
            'value': 'Kosten (€)',
            'client_name': 'Klant',
            'variable': 'Kostentype',
            'total_labour_cost': 'Arbeidskosten',
            'total_parts_cost': 'Onderdelen'
        },
        barmode='stack',
        color_discrete_map={
            'total_labour_cost': '#00cc66',
            'total_parts_cost': '#0066cc'
        }
    )
    
    # Voeg percentages toe aan de hover data
    fig_revenue.update_traces(
        hovertemplate="<br>".join([
            "Klant: %{x}",
            "Kosten: €%{y:,.2f}",
            "Percentage van Totaal: %{customdata:.1f}%"
        ])
    )
    
    # Bereken percentages voor hover data
    total_costs = revenue_df['total_cost']
    labour_pcts = (revenue_df['total_labour_cost'] / total_costs * 100).round(1)
    parts_pcts = (revenue_df['total_parts_cost'] / total_costs * 100).round(1)
    
    # Update hover data voor beide traces
    fig_revenue.data[0].customdata = labour_pcts
    fig_revenue.data[1].customdata = parts_pcts
    
    st.plotly_chart(fig_revenue, use_container_width=True)
    
    # Client service history
    st.subheader("Klant Service Historie")
    for client in selected_client:
        client_df = filtered_df[filtered_df['client_name'] == client]
        st.write(f"### {client}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Totaal Orders", len(client_df))
        with col2:
            st.metric("Gemiddelde Arbeidskosten", 
                     f"€{client_df['total_labour_cost'].mean():.2f}")
        with col3:
            st.metric("Garantie Claims", 
                     len(client_df[client_df['warranty_number'].notna()]))
        
        # Voeg totale kosten toe
        total_labour_cost = client_df['total_labour_cost'].sum()
        total_parts_cost = client_df['total_parts_cost'].sum()
        total_cost = total_labour_cost + total_parts_cost
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Totale Kosten", f"€{total_cost:.2f}")
        with col2:
            st.metric("Totale Arbeidskosten", f"€{total_labour_cost:.2f}")
        with col3:
            st.metric("Totale Onderdelen Kosten", f"€{total_parts_cost:.2f}")
            
        # Laatste orders overzicht
        st.write("#### Laatste Orders")
        latest_orders = client_df.sort_values('defect_date', ascending=False)[
            ['defect_date', 'number', 'machine_model', 'machine_vin', 'category', 'id']
        ].head(10)  # Toon laatste 10 orders
        
        # Format de datum kolom
        latest_orders['defect_date'] = latest_orders['defect_date'].dt.strftime('%Y-%m-%d')
        
        # Voeg link kolom toe
        latest_orders['Link'] = latest_orders['id'].apply(lambda x: f"https://wpm.westtrac-portal.be/orders/{x}")
        
        # Hernoem kolommen voor weergave
        latest_orders = latest_orders.rename(columns={
            'defect_date': 'Datum',
            'number': 'Order Nr',
            'machine_model': 'Machine',
            'machine_vin': 'VIN',
            'category': 'Categorie'
        })
        
        # Verwijder de id kolom
        latest_orders = latest_orders.drop(columns=['id'])
        
        st.dataframe(
            latest_orders,
            column_config={
                "Datum": st.column_config.TextColumn("Datum", width=100),
                "Order Nr": st.column_config.TextColumn("Order Nr", width=100),
                "Machine": st.column_config.TextColumn("Machine", width=200),
                "VIN": st.column_config.TextColumn("VIN", width=200),
                "Categorie": st.column_config.TextColumn("Categorie", width=150),
                "Link": st.column_config.LinkColumn("Link", display_text="Open Order", width=100, help="Klik om de order te bekijken in WPM"),
            },
            hide_index=True,
            use_container_width=True
        )
    
    # Verdelen op servicecategorie
    st.subheader("Verdeling op Service Categorie")
    service_category_df = (
        filtered_df.groupby('category')
        .agg({
            'total_labour_cost': 'sum',
            'total_parts_cost': 'sum'
        })
        .assign(total_cost=lambda x: x['total_labour_cost'] + x['total_parts_cost'])
        .reset_index()
        .sort_values('total_cost', ascending=False)
    )
    
    # Maak een staafdiagram voor de verdeling
    fig_service_category = px.bar(
        service_category_df,
        x='category',
        y='total_cost',
        labels={'total_cost': 'Totale Kosten (€)', 'category': 'Service Categorie'},
        color='total_cost',
        color_continuous_scale=px.colors.sequential.Viridis
    )
    
    # Voeg bedragen toe aan de grafiekkolommen
    fig_service_category.update_traces(texttemplate='%{y:,.2f}', textposition='outside')
    
    st.plotly_chart(fig_service_category, use_container_width=True)