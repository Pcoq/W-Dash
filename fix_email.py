from utils.user_management import supabase

def main():
    print("Fixing email address...")
    
    # Update the email address
    result = supabase.table('app_users').update({
        'email': 'services@westtrac.com'  # correct email
    }).eq('email', 'serices@westtrac.com').execute()  # incorrect email
    
    if result.data:
        print("✅ Email address corrected successfully!")
    else:
        print("❌ Error correcting email address")

if __name__ == "__main__":
    main() 