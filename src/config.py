"""
Configuration module for FarmBot application.
Centralizes all environment variable access using dotenv.
"""
import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables from .env file
load_dotenv(override=True)


class Config:
    """Configuration class that holds all environment variables."""
    
    # Telegram Bot Configuration
    TELEGRAM_API_KEY: Optional[str] = os.getenv("TELEGRAM_API_KEY")
    
    # AI Service Configuration
    AI_API_KEY: Optional[str] = os.getenv("AI_API_KEY")
    MODEL_NAME: Optional[str] = os.getenv("MODEL_NAME")
    
    # API Service Configuration
    URL_LITEFARM: Optional[str] = os.getenv("URL_LITEFARM")
    
    # Flask Web Server Configuration
    FLASK_SECRET_KEY: Optional[str] = os.getenv("FLASK_SECRET_KEY")
    GOOGLE_CLIENT_ID: Optional[str] = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: Optional[str] = os.getenv("GOOGLE_CLIENT_SECRET")
    LINK_SERVER: Optional[str] = os.getenv("LINK_SERVER")
    
    @classmethod
    def validate_required_vars(cls) -> None:
        """Validate that all required environment variables are set."""
        required_vars = {
            "TELEGRAM_API_KEY": cls.TELEGRAM_API_KEY,
            "AI_API_KEY": cls.AI_API_KEY,
            "MODEL_NAME": cls.MODEL_NAME,
        }
        
        missing_vars = [var for var, value in required_vars.items() if not value]
        
        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}. "
                "Please check your .env file or environment settings."
            )
    
    @classmethod
    def validate_flask_vars(cls) -> None:
        """Validate that Flask-specific environment variables are set."""
        required_vars = {
            "GOOGLE_CLIENT_ID": cls.GOOGLE_CLIENT_ID,
            "GOOGLE_CLIENT_SECRET": cls.GOOGLE_CLIENT_SECRET,
        }
        
        missing_vars = [var for var, value in required_vars.items() if not value]
        
        if missing_vars:
            raise ValueError(
                f"Missing required Flask environment variables: {', '.join(missing_vars)}. "
                "Please check your .env file or environment settings."
            )


# Create a global config instance (singleton pattern)
config = Config()
