import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
from utils.excel_utils import to_excel

def render_accounting_export(orders_df):
    st.header("Boekhouding Record Export")
    
    # Filter op jaar
    years = orders_df['defect_date'].dt.year.unique()
    years = sorted(years, reverse=True)  # Meest recente jaren eerst
    selected_year = st.selectbox("Selecteer Jaar", years)
    
    # Filter data op geselecteerd jaar
    filtered_df = orders_df[orders_df['defect_date'].dt.year == selected_year]
    
    # Selecteer alleen de gewenste kolommen
    export_columns = ['defect_date', 'number', 'client_name', 'machine_vin', 'invoice_number']
    export_df = filtered_df[export_columns]
    
    # Toon aantal records
    st.write(f"Aantal records voor {selected_year}: {len(export_df):,}")
    
    if st.button("Export naar Excel"):
        excel_data = to_excel(export_df)
        st.download_button(
            label="Export naar Excel",
            data=excel_data,
            file_name=f'export_boekhouding_{pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
            mime='application/vnd.ms-excel'
        )