from datetime import datetime
import pandas as pd
import numpy as np
from typing import Dict, List

class SeasonalPatternAnalyzer:
    """Module voor het identificeren en analyseren van seizoenspatronen in onderdelengebruik"""
    
    def __init__(self):
        self.seasonal_data = {
            'part_level': {},
            'category_level': {},
            'global_level': {}
        }

    def analyze_parts_usage(self, usage_data: pd.DataFrame) -> Dict:
        """
        Analyseer seizoenspatronen in onderdelengebruik
        
        Parameters:
        usage_data (pd.DataFrame): DataFrame met kolommen 'datum', 'onderdeel_id', 'aantal'
        
        Returns:
        Dict met seizoenspatronen per onderdeel
        """
        patterns = {}
        
        # Zorg dat datum in juist formaat staat
        usage_data['datum'] = pd.to_datetime(usage_data['datum'])
        
        # Groepeer per onderdeel en maand
        monthly_usage = usage_data.groupby([
            'onderdeel_id',
            usage_data['datum'].dt.month
        ])['aantal'].sum().reset_index()
        
        for onderdeel in monthly_usage['onderdeel_id'].unique():
            onderdeel_data = monthly_usage[monthly_usage['onderdeel_id'] == onderdeel]
            
            # Bereken seizoensindex
            gemiddeld_gebruik = onderdeel_data['aantal'].mean()
            seizoens_index = onderdeel_data['aantal'] / gemiddeld_gebruik
            
            # Identificeer pieken en dalen
            patterns[onderdeel] = {
                'piek_maanden': onderdeel_data[seizoens_index > 1.2]['datum'].tolist(),
                'dal_maanden': onderdeel_data[seizoens_index < 0.8]['datum'].tolist(),
                'seizoens_index': seizoens_index.tolist()
            }
            
        return patterns

    def get_seasonal_recommendations(self, part_id: str) -> Dict:
        """
        Geef aanbevelingen voor voorraadbeheer gebaseerd op seizoenspatronen
        
        Parameters:
        part_id (str): ID van het onderdeel
        
        Returns:
        Dict met aanbevelingen
        """
        if part_id not in self.seasonal_data['part_level']:
            return {"error": "Geen seizoensdata beschikbaar voor dit onderdeel"}
            
        pattern = self.seasonal_data['part_level'][part_id]
        
        return {
            "voorraad_advies": {
                "piek_periodes": "Verhoog voorraad voor maanden: " + 
                    ", ".join([str(m) for m in pattern['piek_maanden']]),
                "dal_periodes": "Verlaag voorraad voor maanden: " + 
                    ", ".join([str(m) for m in pattern['dal_maanden']])
            },
            "seizoens_index": pattern['seizoens_index']
        }

    def analyze_patterns_all_levels(self, usage_data: pd.DataFrame) -> Dict:
        """
        Analyseer seizoenspatronen op alle niveaus: per onderdeel, per categorie en globaal
        
        Parameters:
        usage_data (pd.DataFrame): DataFrame met kolommen 'datum', 'onderdeel_id', 'categorie', 'aantal'
        
        Returns:
        Dict met seizoenspatronen voor alle niveaus
        """
        # Part level analyse
        part_patterns = self.analyze_parts_usage(usage_data)
        self.seasonal_data['part_level'] = part_patterns

        # Categorie niveau
        category_usage = usage_data.groupby([
            'categorie',
            pd.Grouper(key='datum', freq='M')
        ])['aantal'].sum().reset_index()
        
        category_patterns = self.analyze_parts_usage(category_usage.rename(
            columns={'categorie': 'onderdeel_id'}
        ))
        self.seasonal_data['category_level'] = category_patterns

        # Globaal niveau
        global_usage = usage_data.groupby([
            pd.Grouper(key='datum', freq='M')
        ])['aantal'].sum().reset_index()
        global_usage['onderdeel_id'] = 'GLOBAL'
        
        global_patterns = self.analyze_parts_usage(global_usage)
        self.seasonal_data['global_level'] = global_patterns

        return self.seasonal_data

    def get_multi_level_recommendations(self, part_id: str) -> Dict:
        """
        Geef aanbevelingen op basis van alle analyseniveaus
        
        Parameters:
        part_id (str): ID van het onderdeel
        
        Returns:
        Dict met aanbevelingen van alle niveaus
        """
        part_category = self.get_part_category(part_id)  # Deze functie moet je nog implementeren
        
        recommendations = {
            'onderdeel_specifiek': self.get_seasonal_recommendations(part_id),
            'categorie_trend': self.get_category_recommendations(part_category),
            'globale_trend': self.get_global_recommendations()
        }
        
        return self.combine_recommendations(recommendations)

    def combine_recommendations(self, recommendations: Dict) -> Dict:
        """
        Combineer aanbevelingen van verschillende niveaus tot één gewogen advies
        """
        # Geef meer gewicht aan onderdeel-specifieke patronen
        weights = {
            'onderdeel': 0.6,
            'categorie': 0.3,
            'globaal': 0.1
        }
        
        # Combineer de inzichten
        combined_advice = {
            'gewogen_advies': self.calculate_weighted_advice(recommendations, weights),
            'detail_niveau': recommendations
        }
        
        return combined_advice 