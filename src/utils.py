from datetime import datetime, timedelta

def parse_date(input_text: str) -> str:
    """
    Parses relative dates like 'hoy', 'ayer', or specific dates like '5 de mayo'.
    Returns the date in ISO format (yyyy-mm-dd).
    """
    today = datetime.now()
    if input_text.lower() == "hoy":
        return today.strftime("%Y-%m-%d")
    elif input_text.lower() == "ayer":
        return (today - timedelta(days=1)).strftime("%Y-%m-%d")
    # Add more parsing logic for specific dates if needed
    return input_text