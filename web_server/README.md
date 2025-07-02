# LiteFarm OAuth Web Server

This Flask web server provides Google OAuth authentication integration with the LiteFarm API for testing purposes.

## Features

- Google OAuth 2.0 authentication
- Integration with LiteFarm API `/google` endpoint
- Comprehensive test results display
- Error handling and user feedback

## Setup

### 1. Environment Variables

Make sure you have the following environment variables set in your `.env` file:

```bash
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your_google_oauth_client_id
GOOGLE_CLIENT_SECRET=your_google_oauth_client_secret

# LiteFarm API Configuration
URL_LITEFARM=http://localhost:5001

# Flask Configuration (optional)
FLASK_SECRET_KEY=your_flask_secret_key
```

### 2. Google OAuth Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API
4. Create OAuth 2.0 credentials
5. Add your redirect URI: `http://localhost:5000/callback/google`

### 3. Install Dependencies

```bash
pip install flask requests python-dotenv
```

## Running the Server

```bash
cd web_server
python login-server.py
```

The server will start on `http://localhost:5000`

## Testing the Integration

1. **Start the LiteFarm API server** on `localhost:5001` (or update `URL_LITEFARM` in your `.env`)

2. **Access the web interface** at `http://localhost:5000`

3. **Click "Continuar con Google"** to start the OAuth flow

4. **Authenticate with Google** - you'll be redirected to Google's OAuth consent screen

5. **View test results** - after successful authentication, you'll see a comprehensive test results page showing:
   - Google user information retrieved
   - OAuth tokens received
   - LiteFarm API request details
   - LiteFarm API response
   - Overall integration status

## API Integration Details

### LiteFarm API Endpoint

The web server sends a POST request to the LiteFarm API's Google login endpoint:

- **URL**: `{LITEFARM_URL}/google`
- **Method**: POST
- **Headers**: 
  - `Content-Type: application/json`
  - `Authorization: Bearer {google_id_token_or_access_token}`
- **Body**: 
  ```json
  {
    "language_preference": "en"
  }
  ```

### Expected LiteFarm Response

Based on the provided LiteFarm `loginWithGoogle` function, the expected response should be:

```json
{
  "id_token": "jwt_token_here",
  "user": {
    "user_id": "user_uuid",
    "email": "user@example.com",
    "first_name": "John",
    "language_preference": "en",
    "full_name": "John Doe"
  },
  "isSignUp": false,
  "isInvited": false
}
```

## Test Results Page

The test results page displays:

1. **Google User Information**: User details retrieved from Google OAuth
2. **Google OAuth Tokens**: Access token and ID token from Google
3. **LiteFarm API Request**: Details of the request sent to LiteFarm
4. **LiteFarm API Response**: Complete response from LiteFarm API
5. **Test Summary**: Overall success/failure status

## Troubleshooting

### Common Issues

1. **Google OAuth Error**: Make sure your redirect URI is correctly configured in Google Cloud Console
2. **LiteFarm API Error**: Ensure the LiteFarm API is running on the specified URL
3. **Missing Environment Variables**: Check that all required environment variables are set

### Debug Mode

The server runs in debug mode by default. Check the console output for detailed error messages.

## File Structure

```
web_server/
├── login-server.py              # Main Flask application
├── templates/
│   ├── index.html              # Login page
│   ├── error.html              # Error display page
│   └── oauth_test_results.html # Test results page
├── static/                     # Static assets (CSS, JS, images)
└── README.md                   # This file
```

## Security Notes

- This implementation is for **testing purposes only**
- In production, implement proper CSRF protection
- Use HTTPS for OAuth flows
- Store secrets securely
- Implement proper session management 