import bcrypt

def generate_hash(password: str) -> str:
    """Genereer een bcrypt hash voor een wachtwoord"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

if __name__ == "__main__":
    password = input("Voer het admin wachtwoord in: ")
    hashed = generate_hash(password)
    print("\nGebruik deze SQL query om de admin gebruiker aan te maken:")
    print("\nINSERT INTO app_users (email, password_hash, role)")
    print(f"VALUES ('admin@example.com', '{hashed}', 'admin');") 