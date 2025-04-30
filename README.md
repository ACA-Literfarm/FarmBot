## FarmBot

A Python chatbot for LiteFarm via Telegram using AI with DeepSeek

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
pip install -r dependencies.txt
```

### 4. Set the Telegram API Key

Create a `.env` file in the project root with the following content:

```
TELEGRAM_API_KEY=your_telegram_bot_token_here
```

Replace `your_telegram_bot_token_here` with your actual Telegram bot token.

### 5. Run the Bot

```sh
python3 src/main.py
```
