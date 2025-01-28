import streamlit as st
import pandas as pd
from utils.database import load_orders_data, load_parts_data
from utils.excel_utils import to_excel

def render_export_tool():
    st.header("Export Tool")
    
    # Kies export type
    export_type = st.radio(
        "Selecteer Export Type",
        ["Onderdelen", "Klant & Machine"]
    )
    
    # Laad data op basis van type
    if export_type == "Onderdelen":
        df = load_parts_data()
        # Converteer part_description naar hoofdletters
        df['part_description'] = df['part_description'].str.upper()
        # Bereken turnover per onderdeel
        df['turnover'] = df['part_price'] * df['part_quantity']
    else:
        df = load_orders_data()
        # Bereken totale orderprijs
        df['total_order_cost'] = df['total_labour_cost'].fillna(0) + df['total_parts_cost'].fillna(0)
    
    # Converteer created_at naar datetime
    df['created_at'] = pd.to_datetime(df['created_at'])
    
    # Filter sectie
    st.subheader("Filters")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Jaar filter
        years = sorted([year for year in df['created_at'].dt.year.unique() if pd.notna(year)], reverse=True)
        selected_year = st.selectbox(
            "Jaar",
            ["Alle"] + list(years)
        )
        
        # Klant filter
        clients = sorted([client for client in df['client_name'].unique() if pd.notna(client)])
        selected_client = st.selectbox(
            "Klant",
            ["Alle"] + list(clients)
        )
    
    with col2:
        # Maand filter
        months = list(range(1, 13))
        month_names = ["Januari", "Februari", "Maart", "April", "Mei", "Juni", 
                      "Juli", "Augustus", "September", "Oktober", "November", "December"]
        month_dict = dict(zip(months, month_names))
        selected_month = st.selectbox(
            "Maand",
            ["Alle"] + list(month_names)
        )
        
        # Machine model filter
        models = sorted([model for model in df['machine_model'].unique() if pd.notna(model)])
        selected_model = st.selectbox(
            "Machine Model",
            ["Alle"] + list(models)
        )
    
    with col3:
        # Category filter
        categories = sorted([cat for cat in df['category'].unique() if pd.notna(cat)])
        selected_category = st.selectbox(
            "Categorie",
            ["Alle"] + list(categories)
        )
        
        # Status filter
        statuses = sorted([status for status in df['status'].unique() if pd.notna(status)])
        selected_status = st.selectbox(
            "Status",
            ["Alle"] + list(statuses)
        )
    
    # Pas filters toe
    filtered_df = df.copy()
    
    if selected_year != "Alle":
        filtered_df = filtered_df[filtered_df['created_at'].dt.year == selected_year]
    
    if selected_month != "Alle":
        selected_month_num = months[month_names.index(selected_month)]
        filtered_df = filtered_df[filtered_df['created_at'].dt.month == selected_month_num]
    
    if selected_client != "Alle":
        filtered_df = filtered_df[filtered_df['client_name'] == selected_client]
    
    if selected_model != "Alle":
        filtered_df = filtered_df[filtered_df['machine_model'] == selected_model]
    
    if selected_category != "Alle":
        filtered_df = filtered_df[filtered_df['category'] == selected_category]
        
    if selected_status != "Alle":
        filtered_df = filtered_df[filtered_df['status'] == selected_status]
    
    # Definieer toegestane attributen per type
    parts_attributes = {
        "Onderdeelnummer": "part_number",
        "Onderdeelomschrijving": "part_description",
        "Prijs": "part_price",
        "Merk": "part_brand",
        "Aantal gebruikt": "part_quantity",
        "Omzet": "turnover"
    }
    
    client_machine_attributes = {
        "Klantnaam": "client_name",
        "Order nummer": "number",
        "Machine model": "machine_model",
        "Order omschrijving": "description",
        "Defect datum": "defect_date",
        "Categorie": "category",
        "Totaal order prijs": "total_order_cost",
        "Status": "status"
    }
    
    # Selecteer attributen op basis van type
    attributes = parts_attributes if export_type == "Onderdelen" else client_machine_attributes
    
    # Container voor kolom selecties
    st.subheader("Selecteer kolommen voor export")
    
    # Maak 7 kolom selecties
    selected_columns = []
    cols = st.columns(7)
    for i, col in enumerate(cols):
        with col:
            selected = st.selectbox(
                f"Kolom {i+1}",
                ["Geen"] + list(attributes.keys()),
                key=f"col_{i}"
            )
            if selected != "Geen":
                selected_columns.append(attributes[selected])
    
    if not selected_columns:
        st.warning("Selecteer ten minste één kolom om te exporteren")
        return
    
    # Filter alleen de geselecteerde kolommen en pas aggregatie toe indien nodig
    if export_type == "Onderdelen" and any(col in selected_columns for col in ['part_quantity', 'turnover']):
        # Bepaal de groepeer kolommen (alle kolommen behalve de aggregatie kolommen)
        group_columns = [col for col in selected_columns if col not in ['part_quantity', 'turnover']]
        
        if group_columns:
            # Maak een dict met aggregatie functies
            agg_dict = {}
            if 'part_quantity' in selected_columns:
                agg_dict['part_quantity'] = 'sum'
            if 'turnover' in selected_columns:
                agg_dict['turnover'] = 'sum'
                
            # Groepeer en aggregeer
            export_df = filtered_df.groupby(group_columns, as_index=False).agg(agg_dict)
        else:
            # Als alleen aggregatie kolommen zijn geselecteerd
            export_df = pd.DataFrame({
                col: [filtered_df[col].sum()] for col in selected_columns
            })
    elif 'total_order_cost' in selected_columns:
        # Bestaande logica voor total_order_cost
        group_columns = [col for col in selected_columns if col != 'total_order_cost']
        
        if group_columns:
            export_df = filtered_df.groupby(group_columns, as_index=False)['total_order_cost'].sum()
        else:
            export_df = filtered_df[['total_order_cost']].copy()
    else:
        # Geen aggregatie nodig
        export_df = filtered_df[selected_columns].copy()
    
    # Verwijder duplicaten
    export_df = export_df.drop_duplicates()
    
    # Sorteer de data
    if export_type == "Onderdelen":
        export_df = export_df.sort_values(by=['part_number'] if 'part_number' in selected_columns else selected_columns[0])
    else:
        # Sorteer op klantnaam en dan ordernummer als ze beschikbaar zijn
        sort_cols = []
        if 'client_name' in selected_columns:
            sort_cols.append('client_name')
        if 'number' in selected_columns:
            sort_cols.append('number')
        if not sort_cols:
            sort_cols = selected_columns[:1]
        export_df = export_df.sort_values(by=sort_cols)
    
    # Preview van de data
    st.subheader("Preview")
    st.dataframe(export_df.head(5), use_container_width=True)
    
    # Toon aantal records
    st.text(f"Aantal records: {len(export_df)}")
    
    # Export knop
    excel_data = to_excel(export_df)
    st.download_button(
        label="Export naar Excel",
        data=excel_data,
        file_name=f'export_{export_type.lower().replace(" & ", "_")}_{pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
        mime='application/vnd.ms-excel'
    ) 