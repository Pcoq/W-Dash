import pandas as pd
import streamlit as st
import plotly.express as px
from utils.excel_utils import to_excel
from datetime import datetime
from typing import Dict, List
from analytics.seasonal_patterns import SeasonalPatternAnalyzer

def apply_filters(df, year, customers, categories, zero_invoice_filter):
    """Helper functie om filters toe te passen"""
    filtered_df = df[df['defect_date'].dt.year == year]
    
    if customers:
        filtered_df = filtered_df[filtered_df['client_name'].isin(customers)]
    
    if categories:
        filtered_df = filtered_df[filtered_df['category'].isin(categories)]
    
    if zero_invoice_filter == "Nee":
        filtered_df = filtered_df[filtered_df['zero_invoice'] == False]
    
    return filtered_df

def render_parts_analysis(parts_df, used_parts_df):
    # Cache wissen aan het begin van de functie    
    st.header("Onderdelen Analyse")
    
    # Convert defect_date to datetime if it's not already
    parts_df['defect_date'] = pd.to_datetime(parts_df['defect_date'])
    
    # Gemeenschappelijke filters bovenaan
    # Year filter
    years = parts_df['defect_date'].dt.year.unique()
    years = sorted(years, reverse=True)  # Meest recente jaren eerst
    selected_year = st.selectbox("Selecteer Jaar", years)
    
    # Filters row
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Customer filter
        customers = parts_df[parts_df['defect_date'].dt.year == selected_year]['client_name'].unique()
        selected_customer = st.multiselect("Selecteer Klanten", customers)
    
    with col2:
        # Service category filter
        service_categories = parts_df['category'].unique()
        selected_categories = st.multiselect("Selecteer Service Categorieën", service_categories)
    
    with col3:
        # Nulfacturen includeren filter
        zero_invoice_filter = st.selectbox("Nulfacturen Includeren", options=["Ja", "Nee"], index=0)
    
    # Verander de tabs definitie naar 2 tabs
    tab1, tab2 = st.tabs(["Algemene Analyse", "Onderdeel Zoeken"])
    
    # Pas filters toe
    filtered_df = apply_filters(parts_df, selected_year, selected_customer, selected_categories, zero_invoice_filter)
    
    with tab1:
        # Maak een enkele kolom voor de grafieken
        st.subheader(f"Top 30 Meest Gebruikte Onderdelen ({selected_year})")
        
        # Top 30 meest voorkomende onderdelen, filter outliers
        top_parts = (
            filtered_df.groupby('part_number', as_index=False)
                .agg(count=('part_quantity', 'sum'), description=('part_description', 'first'))
        )
        
        # Filter out occurrences greater than 1 million
        top_parts = top_parts[top_parts['count'] <= 1_000_000]
        
        # Sort by count in descending order and take the top 30
        top_parts = top_parts.sort_values(by='count', ascending=False).head(30)
        
        # Convert part_number to string
        top_parts['part_number'] = top_parts['part_number'].astype(str)
        
        # Visualiseer de top onderdelen
        fig_parts = px.bar(
            top_parts,
            x='part_number',
            y='count',
            labels={'count': 'Aantal Voorkomen', 'part_number': 'Onderdelen'},
            title='Top 30 Meest Voorkomende Onderdelen',
            text='count'
        )
        
        fig_parts.update_traces(
            hovertemplate="<b>Onderdelen:</b> %{x}<br><b>Aantal Voorkomen:</b> %{y}<br><b>Beschrijving:</b> %{customdata}<extra></extra>",
            customdata=top_parts['description'],
            texttemplate='%{text}',
            textposition='outside'
        )
        
        fig_parts.update_yaxes(tickformat=',')
        fig_parts.update_xaxes(type='category')
        
        st.plotly_chart(fig_parts, use_container_width=True)

        # Nieuwe visualisatie voor totale inkomsten van onderdelen
        st.subheader(f"Top 30 Onderdelen op Totale Inkomsten ({selected_year})")
        
        # Bereken totale inkomsten
        filtered_df['total_income'] = filtered_df['part_quantity'] * filtered_df['part_price']
        
        # Top 30 onderdelen op basis van totale inkomsten
        top_income_parts = (
            filtered_df.groupby('part_number', as_index=False)
                .agg(total_income=('total_income', 'sum'), description=('part_description', 'first'))
        )
        
        # Sort by total income in descending order and take the top 30
        top_income_parts = top_income_parts.sort_values(by='total_income', ascending=False).head(30)
        top_income_parts['part_number'] = top_income_parts['part_number'].astype(str)
        
        # Visualiseer de top onderdelen op basis van totale inkomsten
        fig_income_parts = px.bar(
            top_income_parts,
            x='part_number',
            y='total_income',
            labels={'total_income': 'Totale Inkomsten (€)', 'part_number': 'Onderdelen'},
            title='Top 30 Onderdelen op Totale Inkomsten',
            text='total_income'
        )
        
        fig_income_parts.update_traces(
            hovertemplate="<b>Onderdelen:</b> %{x}<br><b>Totale Inkomsten:</b> €%{y:.2f}<br><b>Beschrijving:</b> %{customdata}<extra></extra>",
            customdata=top_income_parts['description'],
            texttemplate='€%{text:.2f}',
            textposition='outside'
        )
        
        fig_income_parts.update_yaxes(tickformat=',')
        fig_income_parts.update_xaxes(type='category')
        
        st.plotly_chart(fig_income_parts, use_container_width=True)

    with tab2:
        st.subheader("Zoek Onderdeel")
        
        # Zoekbalk voor part number
        search_query = st.text_input("Zoek op onderdeelnummer", "")
        
        if search_query:
            # Filter op part number binnen de al gefilterde dataset
            part_filtered_df = filtered_df[filtered_df['part_number'].str.contains(search_query, case=False, na=False)]
            
            if not part_filtered_df.empty:
                # Bereken totalen en gemiddelden
                total_quantity = part_filtered_df['part_quantity'].sum()
                avg_price = part_filtered_df['part_price'].mean()
                
                # Toon onderdeel informatie
                info_col1, info_col2, info_col3, info_col4 = st.columns(4)
                with info_col1:
                    st.metric("Onderdeelnummer", part_filtered_df['part_number'].iloc[0])
                with info_col2:
                    st.metric("Omschrijving", part_filtered_df['part_description'].iloc[0])
                with info_col3:
                    st.metric("Gemiddelde Prijs", f"€{avg_price:,.2f}")
                with info_col4:
                    st.metric("Totaal Gebruikt", f"{total_quantity:,.0f}")
                
                # Toon de data in een tabel
                st.subheader("Details per Categorie")
                
                # Groepeer per categorie en tel de part_quantity
                usage_by_category = (
                    part_filtered_df.groupby('category')
                    .agg({
                        'part_quantity': 'sum',
                        'part_price': lambda x: (x * part_filtered_df.loc[x.index, 'part_quantity']).sum()
                    })
                    .reset_index()
                    .rename(columns={
                        'category': 'Categorie',
                        'part_quantity': 'Aantal',
                        'part_price': 'Totale Kost'
                    })
                )
                
                # Styling voor de tabel
                styled_df = (
                    usage_by_category.style
                    .format({
                        'Aantal': '{:,.0f}',
                        'Totale Kost': '€{:,.2f}'
                    })
                    .set_properties(**{
                        'background-color': '#f8f9fa',
                        'color': '#262730',
                        'border-color': '#dee2e6',
                        'padding': '0.5rem'
                    })
                    .set_table_styles([
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
                )
                
                # Toon de resultaten
                st.dataframe(styled_df, use_container_width=True)
                
                # Toon overzicht van ordernummers en datums
                st.subheader("Overzicht van Ordernummers en Datums")
                order_overview = part_filtered_df[['number', 'defect_date', 'client_name', 'category', 'part_quantity', 'id']].drop_duplicates()
                order_overview = order_overview.rename(columns={
                    'number': 'Ordernummer', 
                    'defect_date': 'Datum', 
                    'client_name': 'Klant', 
                    'category': 'Categorie', 
                    'part_quantity': 'Aantal'
                })

                # Sorteer op datum DESC voordat we het formaat aanpassen
                order_overview = order_overview.sort_values(by='Datum', ascending=False)

                # Pas daarna het datumformaat aan
                order_overview['Datum'] = order_overview['Datum'].dt.strftime('%Y-%m-%d')

                # Maak een kolom met de volledige URL
                order_overview['Link'] = order_overview['id'].apply(lambda x: f"https://wpm.westtrac-portal.be/orders/{x}")

                # Verwijder de id kolom omdat die niet getoond hoeft te worden
                order_overview = order_overview.drop(columns=['id'])

                # Styling voor de tabel
                styled_order_overview = (
                    order_overview.style
                    .format({
                        'Aantal': '{:,.0f}'
                    })
                    .set_properties(**{
                        'background-color': '#f8f9fa',
                        'color': '#262730',
                        'border-color': '#dee2e6',
                        'padding': '0.5rem'
                    })
                    .set_table_styles([
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
                )

                # Toon de tabel
                st.dataframe(
                    styled_order_overview,
                    use_container_width=True,
                    column_config={
                        "Link": st.column_config.LinkColumn("Link", display_text="Open Order")
                    }
                )
                
            else:
                st.warning(f"Geen onderdelen gevonden met nummer: {search_query} voor de geselecteerde filters")

class PartsAnalysisView:
    def __init__(self):
        self.seasonal_analyzer = SeasonalPatternAnalyzer()
        
    def analyze_seasonal_patterns(self, parts_df: pd.DataFrame, start_date: datetime, end_date: datetime = None) -> Dict:
        """
        Voer een complete seizoensanalyse uit voor alle onderdelen
        """
        # Gebruik de bestaande parts_df in plaats van nieuwe data op te halen
        usage_data = self.prepare_usage_data(parts_df, start_date, end_date)
        
        # Voer analyse uit op alle niveaus
        analysis_results = self.seasonal_analyzer.analyze_patterns_all_levels(usage_data)
        
        return self.format_analysis_results(analysis_results)
    
    def prepare_usage_data(self, parts_df: pd.DataFrame, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Bereid de data voor uit het bestaande DataFrame
        """
        # Maak een kopie om SettingWithCopyWarning te voorkomen
        usage_data = parts_df.copy()
        
        # Filter op datum
        mask = (usage_data['defect_date'] >= pd.Timestamp(start_date))
        if end_date:
            mask &= (usage_data['defect_date'] <= pd.Timestamp(end_date))
        
        usage_data = usage_data[mask]
        
        # Hernoem kolommen naar verwacht formaat
        usage_data = usage_data.rename(columns={
            'part_number': 'onderdeel_id',
            'category': 'categorie',
            'defect_date': 'datum',
            'part_quantity': 'aantal'
        })
        
        return usage_data[['onderdeel_id', 'categorie', 'datum', 'aantal']]
    
    def get_part_recommendations(self, part_id: str) -> Dict:
        """
        Haal seizoensaanbevelingen op voor specifiek onderdeel
        """
        return self.seasonal_analyzer.get_multi_level_recommendations(part_id)
    
    def format_analysis_results(self, analysis_results: Dict) -> Dict:
        """
        Format de analyseresultaten voor weergave
        """
        formatted_results = {
            'onderdeel_niveau': {
                'aantal_onderdelen': len(analysis_results['part_level']),
                'details': self.format_level_results(analysis_results['part_level'])
            },
            'categorie_niveau': {
                'aantal_categorien': len(analysis_results['category_level']),
                'details': self.format_level_results(analysis_results['category_level'])
            },
            'globaal_niveau': {
                'details': analysis_results['global_level'].get('GLOBAL', {})
            }
        }
        
        return formatted_results
    
    def format_level_results(self, level_data: Dict) -> Dict:
        """
        Format resultaten per niveau
        """
        formatted = {}
        for key, data in level_data.items():
            formatted[key] = {
                'pieken': [self.format_month(m) for m in data['piek_maanden']],
                'dalen': [self.format_month(m) for m in data['dal_maanden']],
                'seizoens_index': data['seizoens_index']
            }
        return formatted
    
    def format_month(self, month: int) -> str:
        """
        Format maandnummer naar Nederlandse maandnaam
        """
        months = {
            1: 'januari', 2: 'februari', 3: 'maart', 
            4: 'april', 5: 'mei', 6: 'juni',
            7: 'juli', 8: 'augustus', 9: 'september', 
            10: 'oktober', 11: 'november', 12: 'december'
        }
        return months.get(month, str(month))
    
    def get_seasonal_dashboard_data(self) -> Dict:
        """
        Verzamel data voor het seizoenspatronen dashboard
        """
        current_date = datetime.now()
        year_ago = current_date.replace(year=current_date.year - 1)
        
        # Haal data op voor laatste jaar
        analysis_results = self.analyze_seasonal_patterns(parts_df, year_ago)
        
        # Verzamel dashboard statistieken
        dashboard_data = {
            'algemene_statistieken': {
                'aantal_onderdelen_geanalyseerd': len(analysis_results['onderdeel_niveau']['details']),
                'aantal_categorien': len(analysis_results['categorie_niveau']['details'])
            },
            'huidige_seizoenstrends': self.get_current_season_trends(analysis_results),
            'aankomende_pieken': self.get_upcoming_peaks(analysis_results),
            'voorraadadviezen': self.generate_stock_recommendations(analysis_results)
        }
        
        return dashboard_data