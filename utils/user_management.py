import streamlit as st
from supabase import create_client, Client
import bcrypt
from datetime import datetime
from utils.env_loader import load_env_var
from typing import List
import pandas as pd

# Initialize Supabase client
supabase: Client = create_client(
    load_env_var('SUPABASE_URL'),
    load_env_var('SUPABASE_KEY')
)

# Role permissions
ROLE_PERMISSIONS = {
    'admin': ['Klanten', 'Parts', 'Machines', 'Medewerkers', 'Financieel', 'Boekhouding Record Export', 'KPI Dashboard', 'Export Tool', 'Gebruikersbeheer'],
    'warehouse': ['Parts'],
    'user': ['Klanten', 'Parts', 'Machines', 'Medewerkers', 'Financieel']
}

def hash_password(password: str) -> str:
    """Hash een wachtwoord met bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verifieer een wachtwoord tegen de hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_user(email: str, password: str, role: str = 'user') -> dict:
    """Maak een nieuwe gebruiker aan (alleen voor admins)"""
    try:
        if role not in ROLE_PERMISSIONS:
            return {'success': False, 'error': f'Invalid role. Choose from: {", ".join(ROLE_PERMISSIONS.keys())}'}
            
        hashed_password = hash_password(password)
        user = supabase.table('app_users').insert({
            'email': email,
            'password_hash': hashed_password,
            'role': role,
            'created_at': datetime.now().isoformat(),
            'is_active': True
        }).execute()
        return {'success': True, 'user': user.data[0]}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def login_user(email: str, password: str) -> dict:
    """Log een gebruiker in"""
    try:
        # Check if user exists
        user_result = supabase.table('app_users').select('*').eq('email', email).eq('is_active', True).execute()
        
        if not user_result.data:
            return {'success': False, 'error': 'Invalid credentials'}
            
        user = user_result.data[0]
        
        # Verify password
        if not verify_password(password, user['password_hash']):
            return {'success': False, 'error': 'Invalid credentials'}
            
        # Update last login
        supabase.table('app_users').update({'last_login': datetime.now().isoformat()}).eq('id', user['id']).execute()
        
        return {'success': True, 'user': user}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def is_admin() -> bool:
    """Check of de huidige gebruiker een admin is"""
    if 'user' not in st.session_state:
        return False
    return st.session_state.user.get('role') == 'admin'

def get_user_role() -> str:
    """Haal de rol van de huidige gebruiker op"""
    if 'user' not in st.session_state:
        return 'user'
    return st.session_state.user.get('role', 'user')

def get_allowed_views() -> List[str]:
    """Haal de toegestane views op voor de huidige gebruiker"""
    role = get_user_role()
    return ROLE_PERMISSIONS.get(role, [])

def has_view_access(view_name: str) -> bool:
    """Check of de huidige gebruiker toegang heeft tot een specifieke view"""
    return view_name in get_allowed_views()

def change_password(user_id: str, current_password: str, new_password: str) -> dict:
    """Wijzig het wachtwoord van een gebruiker"""
    try:
        # Haal huidige gebruiker op
        user_result = supabase.table('app_users').select('*').eq('id', user_id).execute()
        if not user_result.data:
            return {'success': False, 'error': 'Gebruiker niet gevonden'}
            
        user = user_result.data[0]
        
        # Verifieer huidig wachtwoord
        if not verify_password(current_password, user['password_hash']):
            return {'success': False, 'error': 'Huidig wachtwoord is incorrect'}
            
        # Update wachtwoord
        hashed_password = hash_password(new_password)
        supabase.table('app_users').update({
            'password_hash': hashed_password
        }).eq('id', user_id).execute()
        
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def render_admin_panel():
    """Render het admin panel voor gebruikersbeheer"""
    st.title("Instellingen")
    
    # Wachtwoord wijzigen (voor alle gebruikers)
    st.header("Wachtwoord Wijzigen")
    with st.form("change_password"):
        current_password = st.text_input("Huidig wachtwoord", type="password")
        new_password = st.text_input("Nieuw wachtwoord", type="password")
        confirm_password = st.text_input("Bevestig nieuw wachtwoord", type="password")
        
        if st.form_submit_button("Wachtwoord Wijzigen"):
            if not current_password or not new_password or not confirm_password:
                st.error("Vul alle velden in")
            elif new_password != confirm_password:
                st.error("Nieuwe wachtwoorden komen niet overeen")
            else:
                result = change_password(
                    st.session_state.user['id'],
                    current_password,
                    new_password
                )
                if result['success']:
                    st.success("Wachtwoord succesvol gewijzigd!")
                else:
                    st.error(f"Error: {result['error']}")
    
    # Gebruikersbeheer (alleen voor admins)
    if is_admin():
        st.markdown("---")
        st.header("Gebruikersbeheer")
        
        # Gebruikers overzicht
        st.subheader("Gebruikers")
        users = supabase.table('app_users').select('email,role,last_login,is_active').execute()
        if users.data:
            # Convert data to pandas DataFrame voor betere formatting
            df = pd.DataFrame(users.data)
            
            # Format last_login datetime
            df['last_login'] = pd.to_datetime(df['last_login']).dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Rename columns for display
            df = df.rename(columns={
                'email': 'Email',
                'role': 'Rol',
                'last_login': 'Laatste Login',
                'is_active': 'Actief'
            })
            
            # Convert boolean to Ja/Nee
            df['Actief'] = df['Actief'].map({True: 'Ja', False: 'Nee'})
            
            st.dataframe(
                df,
                column_config={
                    "Email": st.column_config.TextColumn("Email", width="medium"),
                    "Rol": st.column_config.TextColumn("Rol", width="small"),
                    "Laatste Login": st.column_config.TextColumn("Laatste Login", width="medium"),
                    "Actief": st.column_config.TextColumn("Actief", width="small"),
                },
                hide_index=True
            )
        
        # Nieuwe gebruiker aanmaken
        st.subheader("Nieuwe Gebruiker Aanmaken")
        with st.form("create_user"):
            email = st.text_input("Email")
            password = st.text_input("Wachtwoord", type="password")
            role = st.selectbox("Rol", list(ROLE_PERMISSIONS.keys()))
            
            if st.form_submit_button("Aanmaken"):
                if email and password:
                    result = create_user(email, password, role)
                    if result['success']:
                        st.success(f"Gebruiker {email} succesvol aangemaakt!")
                    else:
                        st.error(f"Error: {result['error']}")
                else:
                    st.error("Vul alle velden in") 