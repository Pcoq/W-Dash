import streamlit as st
import pandas as pd
from utils.database import load_orders_data, load_worker_labours, load_parts_data
from utils.excel_utils import to_excel

def render_kpi_dashboard():
    st.header("KPI Dashboard")

    # Load data
    orders_df, worker_labours_df, parts_df = load_orders_data(), load_worker_labours(), load_parts_data()

    # Convert dates to datetime
    orders_df['created_at'] = pd.to_datetime(orders_df['created_at'])
    # Drop duplicates before converting to datetime
    worker_labours_df = worker_labours_df.drop_duplicates(subset=['id', 'created_at'])
    worker_labours_df['created_at'] = pd.to_datetime(worker_labours_df['created_at'])

    # Year filter
    years = orders_df['created_at'].dt.year.unique()
    years = sorted(years, reverse=True)
    selected_year = st.selectbox("Selecteer Jaar", years)

    # Filter data op jaar
    orders_year = orders_df[orders_df['created_at'].dt.year == selected_year]
    worker_labours_year = worker_labours_df[worker_labours_df['created_at'].dt.year == selected_year]

    # Maak een dataframe voor de matrix
    months = range(1, 13)
    metrics_data = {
        'Metric': [
            'Aantal beschikbare uren werkplaats',
            'Aantal betaalde uren werkplaats',
            'Aantal externe werkorders',
            'Aantal interne werkorders',
            'Aantal garantie werkorders',
            'Totaal aantal werkorders',
            'Aantal gewerkte uren op externe werkorders',
            'Aantal gewerkte uren op interne werkorders',
            'Aantal gewerkte uren op garantie werkorders',
            'Aantal gewerkte uren op niet productieve activiteiten',
            'Totaal aantal productieve uren',
            'Aantal verkochte uren - extern',
            'Aantal verkochte uren - intern',
            'Aantal verkochte uren - garantie',
            'Totaal aantal verkochte uren',
            'Totale omzet werkplaats uit arbeid',
            'Omzet werkplaats extern werk',
            'Omzet werkplaats intern werk',
            'Omzet werkplaats garantie werk',
            'Totaal bedrag openstaande werkorders (O.H.W.)',
            'Totaal aantal openstaande werkorders'
        ]
    }

    # Voeg kolommen toe voor elke maand
    for month in months:
        month_data = orders_year[orders_year['created_at'].dt.month == month]
        month_labour = worker_labours_year[worker_labours_year['created_at'].dt.month == month]
        
        # Filter op de juiste categorieën
        extern_data = month_data[month_data['category'].isin(['repair', 'sales'])]
        intern_data = month_data[month_data['category'] == 'internal order']
        garantie_data = month_data[month_data['category'] == 'warranty']
        
        # Bereken gewerkte uren per categorie
        extern_hours = month_labour[
            month_labour['order_id'].isin(extern_data['id'])
        ]['total_hours'].sum()
        
        intern_hours = month_labour[
            month_labour['order_id'].isin(intern_data['id'])
        ]['total_hours'].sum()
        
        garantie_hours = month_labour[
            month_labour['order_id'].isin(garantie_data['id'])
        ]['total_hours'].sum()
        
        total_hours = extern_hours + intern_hours + garantie_hours
        
        # Bereken metrics voor deze maand
        metrics_data[f'{month:02d}'] = [
            1474,  # Placeholder voor capaciteit
            None,  # Placeholder voor HR data
            len(extern_data),  # Aantal externe werkorders
            len(intern_data),  # Aantal interne werkorders
            len(garantie_data),  # Aantal garantie werkorders
            len(month_data),  # Totaal aantal werkorders
            extern_hours,  # Aantal gewerkte uren op externe werkorders
            intern_hours,  # Aantal gewerkte uren op interne werkorders
            garantie_hours,  # Aantal gewerkte uren op garantie werkorders
            None,  # Placeholder voor niet productieve activiteiten
            total_hours,  # Totaal aantal productieve uren
            extern_hours,  # Verkochte uren extern (zelfde als gewerkte uren)
            intern_hours,  # Verkochte uren intern
            garantie_hours,  # Verkochte uren garantie
            total_hours,  # Totaal verkochte uren
            extern_data['total_labour_cost'].sum() + intern_data['total_labour_cost'].sum() + garantie_data['total_labour_cost'].sum(),  # Totale omzet
            extern_data['total_labour_cost'].sum(),  # Omzet extern
            intern_data['total_labour_cost'].sum(),  # Omzet intern
            garantie_data['total_labour_cost'].sum(),  # Omzet garantie
            month_data[month_data['status'] != 'completed']['total_labour_cost'].sum(),  # Bedrag openstaande orders
            len(month_data[month_data['status'] != 'completed'])  # Aantal openstaande orders
        ]

    # Voeg cumulatief en gemiddelde kolommen toe
    df = pd.DataFrame(metrics_data)
    
    # Bereken cumulatief (som van alle maanden)
    df['Cum.'] = df.iloc[:, 1:13].sum(axis=1)
    
    # Bereken gemiddelde
    df['Gem.'] = df.iloc[:, 1:13].mean(axis=1)
    
    # Formattering voor de verschillende types metrics
    format_dict = {
        'Aantal': '{:.0f}',
        'uren': '{:.1f}',
        'omzet': '€{:,.2f}',
        'bedrag': '€{:,.2f}'
    }
    
    # Pas formatting toe
    styled_df = df.style.format(format_dict)
    
    # Voeg styling toe voor betere leesbaarheid
    styled_df = styled_df.set_properties(**{
        'background-color': '#f8f9fa',
        'color': '#262730',
        'border-color': '#dee2e6',
        'padding': '0.5rem'
    }).set_table_styles([
        {'selector': 'th', 'props': [
            ('background-color', '#e9ecef'),
            ('color', '#262730'),
            ('font-weight', 'bold'),
            ('padding', '0.5rem')
        ]},
        {'selector': 'td', 'props': [
            ('border', '1px solid #dee2e6')
        ]}
    ])

    # Toon de matrix
    st.dataframe(styled_df, use_container_width=True)

    # Export knop
    excel_data = to_excel(df)
    st.download_button(
        label="Export",
        data=excel_data,
        file_name=f'kpi_matrix_{selected_year}.xlsx',
        mime='application/vnd.ms-excel'
    )

# Call the function to render the dashboard
if __name__ == "__main__":
    render_kpi_dashboard() 