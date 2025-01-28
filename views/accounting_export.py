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
    
    # Toon aantal records
    st.write(f"Aantal records voor {selected_year}: {len(filtered_df):,}")
    
    # Export knop
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("⬇️ Exporteer Records"):
            from utils.excel_utils import to_excel
            excel_data = to_excel(filtered_df)
            st.download_button(
                label="📥 Download Excel bestand",
                data=excel_data,
                file_name=f"boekhouding_export_{selected_year}.xlsx",
                mime="application/vnd.ms-excel"
            )