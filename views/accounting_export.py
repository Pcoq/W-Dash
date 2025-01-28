import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
from utils.excel_utils import to_excel

def render_accounting_export(orders_df):
    st.header("Boekhouding Record Export")
    
    # Bepaal min en max datum uit de dataset
    min_date = orders_df['defect_date'].min().date()
    max_date = orders_df['defect_date'].max().date()
    
    # Datumbereik selectie
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start datum",
            value=max_date - timedelta(days=30),  # Standaard laatste 30 dagen
            min_value=min_date,
            max_value=max_date
        )
    with col2:
        end_date = st.date_input(
            "Eind datum",
            value=max_date,
            min_value=min_date,
            max_value=max_date
        )
    
    # Filter data op geselecteerd datumbereik
    mask = (orders_df['defect_date'].dt.date >= start_date) & (orders_df['defect_date'].dt.date <= end_date)
    filtered_df = orders_df[mask]
    
    # Selecteer alleen de gewenste kolommen
    export_columns = ['defect_date', 'number', 'client_name', 'machine_vin', 'invoice_number']
    export_df = filtered_df[export_columns]
    
    # Toon aantal records
    st.write(f"Aantal records voor periode {start_date.strftime('%d-%m-%Y')} t/m {end_date.strftime('%d-%m-%Y')}: {len(export_df):,}")
    
    if st.button("Export naar Excel"):
        excel_data = to_excel(export_df)
        st.download_button(
            label="Export naar Excel",
            data=excel_data,
            file_name=f'export_boekhouding_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.xlsx',
            mime='application/vnd.ms-excel'
        )