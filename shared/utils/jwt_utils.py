import jwt

def decode_jwt_token(token: str) -> dict:
    """
    Decode JWT token without verification (since we trust LiteFarm API)
    Returns the payload containing user information
    """
    try:
        # Decode without verification since we trust the source
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload
    except jwt.InvalidTokenError as e:
        print(f"JWT decode error: {e}")
        return {}