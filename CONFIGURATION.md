# Configuration Guide

## Environment Variables Setup

This application uses a centralized configuration system via `src/config.py` that loads environment variables from a `.env` file.

### Setup Steps

1. **Copy the example environment file:**

   ```bash
   cp .env.example .env
   ```

2. **Edit the `.env` file with your actual values:**

   ```bash
   # Telegram Bot Configuration
   TELEGRAM_API_KEY=your_actual_telegram_bot_token

   # AI Service Configuration
   AI_API_KEY=your_actual_openai_api_key
   MODEL_NAME=gpt-3.5-turbo

   # LiteFarm API Configuration
   URL_LITEFARM=https://your-actual-litefarm-api-url.com

   # Flask Web Server Configuration (optional, only needed for web interface)
   FLASK_SECRET_KEY=your_actual_flask_secret_key
   GOOGLE_CLIENT_ID=your_actual_google_oauth_client_id
   GOOGLE_CLIENT_SECRET=your_actual_google_oauth_client_secret
   ```

### Required Variables

The following environment variables are **required** for the main bot functionality:

- `TELEGRAM_API_KEY`: Your Telegram bot token from @BotFather
- `AI_API_KEY`: Your OpenAI (or compatible) API key
- `MODEL_NAME`: The AI model to use (e.g., "gpt-3.5-turbo", "gpt-4")

### Optional Variables

The following variables are **optional** and only needed for specific features:

- `URL_LITEFARM`: LiteFarm API URL (required for expense tracking)
- `FLASK_SECRET_KEY`: Secret key for Flask sessions (auto-generated if not provided)
- `GOOGLE_CLIENT_ID`: Google OAuth client ID (required for web login)
- `GOOGLE_CLIENT_SECRET`: Google OAuth client secret (required for web login)

### Configuration Validation

The application automatically validates that required environment variables are set when starting up. If any required variables are missing, you'll see a clear error message indicating which variables need to be configured.

### Security Notes

- Never commit your `.env` file to version control
- The `.env` file is already included in `.gitignore`
- Use strong, unique values for secret keys
- Rotate API keys regularly for security

## Usage in Code

All configuration is centralized in `src/config.py`. To use configuration values in your code:

```python
from config import config

# Access configuration values
api_key = config.AI_API_KEY
bot_token = config.TELEGRAM_API_KEY
```

This centralized approach ensures:

- Consistent environment variable handling across all modules
- Easy validation of required variables
- Clear documentation of all configuration options
- Reduced code duplication
