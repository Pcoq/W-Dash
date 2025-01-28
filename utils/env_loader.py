import os
from pathlib import Path
from typing import Optional

def load_env_var(key: str, default: Optional[str] = None) -> str:
    """
    Laad een environment variable, eerst uit .env als die bestaat,
    anders uit os.environ. Als beide niet bestaan, return default of raise error.
    """
    # Eerst proberen we de variable direct uit os.environ te halen
    value = os.environ.get(key)
    
    if value is None:
        # Als dat niet lukt, proberen we .env te laden
        try:
            from dotenv import load_dotenv
            env_path = Path(__file__).parent.parent / '.env'
            load_dotenv(dotenv_path=env_path)
            value = os.environ.get(key)
        except ImportError:
            # dotenv is niet geïnstalleerd of .env bestaat niet
            pass
    
    if value is None and default is not None:
        return default
    
    if value is None:
        raise ValueError(f"Environment variable {key} is not set")
        
    return value 