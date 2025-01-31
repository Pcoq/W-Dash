import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
from io import BytesIO
from utils.excel_utils import to_excel
import calendar

def get_previous_month_range():
    """Helper functie om start en eind datum van vorige maand te krijgen"""
    today = datetime.now().date()
    first_of_month = date(today.year, today.month, 1)
    last_month = first_of_month - timedelta(days=1)
    first_of_last_month = date(last_month.year, last_month.month, 1)
    last_of_last_month = date(last_month.year, last_month.month, calendar.monthrange(last_month.year, last_month.month)[1])
    return first_of_last_month, last_of_last_month

def render_accounting_export(orders_df):
    st.header("Boekhouding Record Export")
    
    # Bepaal min en max datum uit de dataset
    min_date = orders_df['defect_date'].min().date()
    max_date = orders_df['defect_date'].max().date()
    
    # Haal vorige maand range op
    default_start, default_end = get_previous_month_range()
    
    # Datumbereik selectie
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start datum",
            value=default_start,  # Start van vorige maand
            min_value=min_date,
            max_value=max_date
        )
    with col2:
        end_date = st.date_input(
            "Eind datum",
            value=default_end,  # Eind van vorige maand
            min_value=min_date,
            max_value=max_date
        )
    
    # Filter data op geselecteerd datumbereik
    mask = (orders_df['defect_date'].dt.date >= start_date) & (orders_df['defect_date'].dt.date <= end_date)
    filtered_df = orders_df[mask]
    
    # Selecteer alleen de gewenste kolommen
    export_columns = ['defect_date', 'number', 'client_name', 'machine_vin', 'category', 'invoice_number_from_invoice']
    export_df = filtered_df[export_columns].copy()
    
    # Format de datum kolom voor weergave en export
    export_df['defect_date'] = export_df['defect_date'].dt.date
    
    # Hernoem kolommen voor weergave
    export_df = export_df.rename(columns={
        'defect_date': 'Datum',
        'number': 'Order Nr',
        'client_name': 'Klant',
        'machine_vin': 'Machine VIN',
        'category': 'Categorie',
        'invoice_number_from_invoice': 'Factuur Nr'
    })
    
    # Toon aantal records
    st.write(f"Aantal records voor periode {start_date.strftime('%d-%m-%Y')} t/m {end_date.strftime('%d-%m-%Y')}: {len(export_df):,}")
    
    # Preview van de data
    st.subheader("Preview Export")
    
    # Toon de scrollbare tabel
    st.dataframe(
        export_df,
        column_config={
            "Datum": st.column_config.DateColumn("Datum", format="DD-MM-YYYY", width=100),
            "Order Nr": st.column_config.TextColumn("Order Nr", width=100),
            "Klant": st.column_config.TextColumn("Klant", width=200),
            "Machine VIN": st.column_config.TextColumn("Machine VIN", width=150),
            "Categorie": st.column_config.TextColumn("Categorie", width=150),
            "Factuur Nr": st.column_config.TextColumn("Factuur Nr", width=100)
        },
        hide_index=True,
        use_container_width=True,
        height=400  # Vaste hoogte voor scrollbaarheid
    )
    
    # Export knop
    if st.button("Export naar Excel"):
        # Reset index voor export
        export_data = export_df.copy()
        excel_data = to_excel(export_data)
        st.download_button(
            label="Download Excel bestand",
            data=excel_data,
            file_name=f'export_boekhouding_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.xlsx',
            mime='application/vnd.ms-excel'
        )