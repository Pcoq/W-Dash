from utils.user_management import create_user
import streamlit as st

def main():
    print("Creating admin user...")
    result = create_user(
        email="services@westtrac.com",
        password="wpmanalytics12",  # Je kunt dit later veranderen
        role="admin"
    )
    
    if result['success']:
        print("✅ Admin user created successfully!")
        print(f"Email: services@westtrac.com")
    else:
        print(f"❌ Error creating admin user: {result['error']}")

if __name__ == "__main__":
    main() 