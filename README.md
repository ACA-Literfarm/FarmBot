## FarmBot

A Python chatbot for LiteFarm via Telegram using AI with DeepSeek

## Prerequisites

Before setting up the bot, ensure you have:

1. **LiteFarm API Running**: The LiteFarm API must be running locally on the `develop` branch
2. **Telegram Bot Token**: Create a bot through [@BotFather](https://t.me/BotFather) on Telegram
3. **Python 3.8+**: Make sure you have Python 3.8 or higher installed

## Getting Started

Follow these steps to set up and run the project:

### 1. Create a Python Virtual Environment

```sh
python3 -m venv env
```

### 2. Activate the Virtual Environment

- On Linux/macOS:
  ```sh
  source env/bin/activate
  ```
- On Windows:
  ```sh
  .\env\Scripts\activate
  ```

### 3. Install Dependencies

```sh
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root with the following configuration:

```properties
# Telegram Bot Configuration
TELEGRAM_API_KEY=your_telegram_bot_token_here

# AI Service Configuration
AI_API_KEY=your_openai_api_key_here
MODEL_NAME=gpt-4o

# Google OAuth Configuration (for web authentication)
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here

# Server Configuration
LINK_SERVER=http://localhost:5000
URL_LITEFARM=http://localhost:5001
```

#### Environment Variables Explanation:

- **TELEGRAM_API_KEY**: Your Telegram bot token obtained from [@BotFather](https://t.me/BotFather)
- **AI_API_KEY**: Your OpenAI API key for AI-powered responses
- **MODEL_NAME**: The AI model to use (e.g., `gpt-4o`, `gpt-3.5-turbo`)
- **GOOGLE_CLIENT_ID**: Google OAuth client ID for web authentication
- **GOOGLE_CLIENT_SECRET**: Google OAuth client secret for web authentication
- **LINK_SERVER**: URL for the web authentication server (default: `http://localhost:5000`)
- **URL_LITEFARM**: URL for the LiteFarm API server (default: `http://localhost:5001`)

#### Required API Keys:

1. **Telegram Bot Token**:

   - Message [@BotFather](https://t.me/BotFather) on Telegram
   - Create a new bot with `/newbot`
   - Copy the provided token

2. **OpenAI API Key**:

   - Sign up at [OpenAI Platform](https://platform.openai.com/)
   - Navigate to API Keys section
   - Create a new API key

3. **Google OAuth Credentials** (for web interface):
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable Google+ API
   - Create OAuth 2.0 credentials

### 5. Run the Bot

```sh
python3 src/main.py
```

## How to Use the Bot

### Basic Commands

Once the bot is running, you can interact with it on Telegram using these commands:

- `/start` - Initialize the bot and get a welcome message
- `/help` - Display available commands and usage instructions
- `/skip` - Skip the current operation or question

### Using the Bot

1. **Start a conversation**: Send `/start` to begin interacting with the bot
2. **Ask questions**: Send any message related to farming, crop management, or LiteFarm functionality
3. **Get AI assistance**: The bot uses DeepSeek AI to provide intelligent responses about farming practices
4. **LiteFarm integration**: The bot can interact with your LiteFarm data when properly configured

### Example Interactions

- "Hoy le vendi a Melvin 10 bolsas de cafe por 10 dolares"
- "How compre un 9RX 710 de john deere por un millon de dolares"
- "Compre 50 bolsas de MOVENTO por 1000 dolares"

## Important Notes

- **LiteFarm API Dependency**: This bot requires the LiteFarm API to be running locally on the `develop` branch for full functionality
- **Internet Connection**: Required for AI responses and Telegram communication
- **Bot Token**: Ensure your Telegram bot token is correctly set in the `.env` file
