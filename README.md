# WPM Dashboard

Een Streamlit dashboard voor het analyseren van WPM (Werkplaats Management) data.

## Features

- Klanten analyse
- Parts analyse
- Machine analyse
- Medewerker analyse
- Financiële analyse
- Boekhouding export
- KPI Dashboard
- Export tool

## Installatie

1. Clone de repository:
```bash
git clone https://github.com/yourusername/wpm-dashboard.git
cd wpm-dashboard
```

2. Maak een virtual environment aan:
```bash
python -m venv venv
source venv/bin/activate  # Op Windows: venv\Scripts\activate
```

3. Installeer de dependencies:
```bash
pip install -r requirements.txt
```

4. Maak een `.env` bestand aan:
```bash
cp .env.example .env
```
En vul de juiste waardes in voor jouw omgeving.

## Configuratie

1. Database configuratie:
   - Maak een Supabase project aan
   - Gebruik de database pooler connection details
   - Vul deze in in je `.env` bestand

2. Dashboard wachtwoord:
   - Stel een wachtwoord in voor dashboard toegang in `.env`

## Gebruik

Start de applicatie:
```bash
streamlit run main.py
```

De app is nu beschikbaar op `http://localhost:8501`

## Development

- Gebruik Python 3.12 of hoger
- Volg de PEP 8 style guide
- Voeg tests toe voor nieuwe functionaliteit
- Update de documentatie bij wijzigingen

## License

MIT License - Zie LICENSE bestand voor details 