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
pip install -r [requirements.txt](http://_vscodecontentref_/20)
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

### 6. Test the Bot

Test each of the following scenarios in Telegram:
- Send the `/start` command
- Send the `/help` command 
- Send a regular message like "Gasté 50 dólares en fertilizante"
- Test the missing field handling

If you encounter any new errors, please share the error messages so I can help you resolve them!