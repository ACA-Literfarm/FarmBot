from flask import Flask, redirect, url_for, request, session, abort, flash, render_template, current_app, jsonify
import requests
import secrets
from urllib.parse import urlencode
import sys
import os
import json
import jwt
import asyncio
from datetime import datetime, timezone, timedelta

# Add the project root directory to the Python path first
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, project_root)

# Add the src directory to the Python path to import config
sys.path.append(os.path.join(project_root, 'src'))
from config import config

# Import database and services
from shared.db.session import AsyncSessionLocal
from shared.services.user_service import UserService
from shared.services.chat_service import ChatSessionService
from shared.services.token_service import TokenService
from shared.repositories.user_repository import UserRepository
from shared.repositories.chat_repository import ChatSessionRepository
from shared.repositories.token_repository import TokenRepository
from shared.DTO.user.user_dto import CreateUserDTO
from shared.DTO.chat.chat_dto import ChatSessionCreateDTO
from shared.DTO.token.token_dto import TokenCreateDTO

# Validate Flask-specific environment variables
config.validate_flask_vars()

app = Flask(__name__)
# Set a secret key for session management
app.secret_key = config.FLASK_SECRET_KEY or secrets.token_urlsafe(32)

# Set the LiteFarm URL - default to localhost:5001 if not configured
LITEFARM_URL = config.URL_LITEFARM or "http://localhost:5001"

# Initialize services
def create_user_service():
    return UserService(lambda session: UserRepository(session))

def create_chat_service():
    return ChatSessionService(lambda session: ChatSessionRepository(session))

def create_token_service():
    return TokenService(lambda session: TokenRepository(session))
# Helper function to decode JWT token and extract user_id
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

# Helper function to save login data to database
async def save_login_data(chat_id: int, token: str, litefarm_user_id: str):
    """
    Save login data to database: user, chat session, and token
    """
    print(f"-----> Starting save_login_data with chat_id: {chat_id}, user_id: {litefarm_user_id}")
    try:
        async with AsyncSessionLocal() as db_session:
            user_service = create_user_service()
            chat_service = create_chat_service()
            token_service = create_token_service()
            
            # Create or get user
            user_dto = CreateUserDTO(litefarm_user_id=litefarm_user_id)
            user = await user_service.create_user(user_dto, db_session)
            print(f"-----> User created/retrieved: {user.litefarm_user_id}")
            
            # Create chat session (this will deactivate previous sessions)
            chat_dto = ChatSessionCreateDTO(
                litefarm_user_id=litefarm_user_id,
                telegram_chat_id=chat_id
            )
            chat_session = await chat_service.create_chat_session(chat_dto, db_session)
            print(f"-----> Chat session created: {chat_session.id}")
            
            # Calculate token expiration (assuming 24 hours)
            # TODO: change 
            expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
            
            # Save token to the token table in the database
            token_dto = TokenCreateDTO(
                chat_session_id=chat_session.id,
                token=token,
                expires_at=expires_at
            )
            token_obj = await token_service.create_token(token_dto, db_session)
            print(f"-----> Token created: {token_obj.id}")
            
            # Commit the transaction
            await db_session.commit()
            
            print(f"Successfully saved login data for chat_id: {chat_id}, user_id: {litefarm_user_id}")
            return True
            
    except Exception as e:
        print(f"Error saving login data: {e}")
        return False

app.config['OAUTH2_PROVIDERS'] = {
    'google': {
        'client_id': config.GOOGLE_CLIENT_ID,
        'client_secret': config.GOOGLE_CLIENT_SECRET,
        'authorize_url': 'https://accounts.google.com/o/oauth2/auth',
        'token_url': 'https://accounts.google.com/o/oauth2/token',
        'userinfo': {
            'url': 'https://www.googleapis.com/oauth2/v3/userinfo',
            'email': lambda json: json.get('email'),
            'first_name': lambda json: json.get('given_name'),
            'last_name': lambda json: json.get('family_name'),
        },
        'scope': ['https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile']
    }
}

@app.route('/login/<int:chat_id>')
def login_with_chat_id(chat_id):
    """Handle login with chat_id in URL path"""
    if chat_id is None:
        return render_template('not_allowed.html')
    # Store chat_id in session for later use
    session['telegram_chat_id'] = chat_id
    return render_template('index.html', chat_id=chat_id)


## post request to /login
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login_post():
    """Handle email/password login by forwarding to LiteFarm API"""
    try:
        # Get form data
        email = request.form.get('email')
        password = request.form.get('password')
        screen_width = request.form.get('screen_width', 1920)  # Default values
        screen_height = request.form.get('screen_height', 1080)
        
        # Validate required fields
        if not email or not password:
            return render_template('error.html', error='Email y contraseña son requeridos'), 400
        
        # Prepare request data in the format expected by LiteFarm API
        litefarm_data = {
            'user': {
                'email': email,
                'password': password
            },
            'screenSize': {
                'screen_width': int(screen_width),
                'screen_height': int(screen_height)
            }
        }
        
        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': request.headers.get('User-Agent', 'Mozilla/5.0 (Unknown)'),
            'Accept-Language': request.headers.get('Accept-Language', 'en-US,en;q=0.9')
        }
        
        # Add forwarded IP if available
        if request.headers.get('X-Forwarded-For'):
            headers['X-Forwarded-For'] = request.headers.get('X-Forwarded-For')
        
        # Send request to LiteFarm API
        response = requests.post(
            f'{LITEFARM_URL}/login',
            json=litefarm_data,
            headers=headers,
            timeout=30
        )
        
        # Handle response
        if response.status_code in [200, 201]:
            try:
                response_data = response.json()
                token = response_data.get('id_token')
                user_data = response_data.get('user')
                
                if token:
                    # Decode JWT token to get user_id
                    jwt_payload = decode_jwt_token(token)
                    litefarm_user_id = jwt_payload.get('user_id')
                    
                    # Get chat_id from session
                    chat_id = session.get('telegram_chat_id')
                    
                    # Save login data to database if we have both chat_id and user_id
                    if chat_id and litefarm_user_id:
                        # Run async function in sync context
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            success = loop.run_until_complete(
                                save_login_data(chat_id, token, litefarm_user_id)
                            )
                            if success:
                                print(f"Login data saved successfully for chat_id: {chat_id}")
                            else:
                                print(f"Failed to save login data for chat_id: {chat_id}")
                        finally:
                            loop.close()
                    
                    # Store data in session for the success page
                    session['login_success'] = {
                        'token': token,
                        'user': user_data,
                        'email': email,
                        'chat_id': chat_id,
                        'litefarm_user_id': litefarm_user_id
                    }
                    # Return JSON response for AJAX request
                    return jsonify({'success': True, 'redirect': url_for('login_success')})
                else:
                    return jsonify({'success': False, 'error': 'No se pudo obtener el token de autenticación'}), 500
            except json.JSONDecodeError:
                return jsonify({'success': False, 'error': 'Respuesta inválida del servidor'}), 500
        
        elif response.status_code == 401:
            return jsonify({'success': False, 'error': 'Credenciales incorrectas. Verifica tu email y contraseña.'}), 401
        
        elif response.status_code == 403:
            return jsonify({'success': False, 'error': 'Usuario no encontrado. Verifica tu email.'}), 403
        
        else:
            try:
                error_data = response.json()
                error_message = error_data.get('message', f'Error del servidor: {response.status_code}')
            except json.JSONDecodeError:
                error_message = f'Error del servidor: {response.status_code}'
            
            return jsonify({'success': False, 'error': error_message}), response.status_code
    
    except requests.exceptions.Timeout:
        return jsonify({'success': False, 'error': 'Tiempo de espera agotado. Intenta nuevamente.'}), 504
    
    except requests.exceptions.ConnectionError:
        return jsonify({'success': False, 'error': 'No se pudo conectar al servidor. Intenta más tarde.'}), 503
    
    except requests.exceptions.RequestException as e:
        return jsonify({'success': False, 'error': f'Error de red: {str(e)}'}), 500
    
    except Exception as e:
        # Log the error for debugging
        print(f"Unexpected error in login_post: {str(e)}")
        return jsonify({'success': False, 'error': 'Error interno del servidor. Intenta nuevamente.'}), 500

@app.route('/login/success')
def login_success():
    """Display the login success page"""
    login_data = session.get('login_success')
    if not login_data:
        return redirect(url_for('index'))
    
    # Clear the session data after use
    session.pop('login_success', None)
    
    return render_template('success.html', 
                         token=login_data.get('token'),
                         user=login_data.get('user'),
                         chat_id=login_data.get('chat_id'),
                         litefarm_user_id=login_data.get('litefarm_user_id'))

@app.route('/login', methods=['GET'])
def login_get():
    """Handle GET requests to /login - redirect to index or render with chat_id"""
    chat_id = request.args.get('chat_id') or request.args.get('user_id')
    if chat_id:
        # Store chat_id in session for later use
        session['telegram_chat_id'] = int(chat_id)
        return render_template('index.html', chat_id=chat_id)
    return redirect(url_for('index'))

@app.route('/authorize/<provider>')
def oauth2_authorize(provider):
    provider_data = current_app.config['OAUTH2_PROVIDERS'].get(provider)
    if provider_data is None:
        abort(404)

    # generate a random string for the state parameter
    session['oauth2_state'] = secrets.token_urlsafe(16)

    generated_redirect_uri = url_for('oauth2_callback', provider=provider, _external=True)
    print(f"-----> GENERATED REDIRECT URI FOR GOOGLE: {generated_redirect_uri}") # DEBUG LINE

    # create a query string with all the OAuth2 parameters
    # Use 'scope' key instead of 'scopes' to match the config
    qs = urlencode({
        'client_id': provider_data['client_id'],
        'redirect_uri': generated_redirect_uri,
        'response_type': 'code',
        'scope': ' '.join(provider_data['scope']),
        'state': session['oauth2_state'],
    })

    # redirect the user to the OAuth2 provider authorization URL
    return redirect(provider_data['authorize_url'] + '?' + qs)

@app.route('/callback/<provider>')
def oauth2_callback(provider):
    provider_data = current_app.config['OAUTH2_PROVIDERS'].get(provider)
    if not provider_data:
        return render_template('error.html', error='Provider not found'), 404
    
    if 'error' in request.args:
        error_messages = []
        for k, v in request.args.items():
            if k.startswith('error'):
                error_messages.append(f'{k}: {v}')
        return render_template('error.html', error='; '.join(error_messages))

    if request.args.get('state') != session.get('oauth2_state'):
        return render_template('error.html', error='Invalid state parameter'), 401

    if 'code' not in request.args:
        return render_template('error.html', error='Authorization code not received'), 401

    try:
        # Exchange authorization code for access token
        token_response = requests.post(provider_data['token_url'], data={
            'client_id': provider_data['client_id'],
            'client_secret': provider_data['client_secret'],
            'code': request.args['code'],
            'grant_type': 'authorization_code',
            'redirect_uri': url_for('oauth2_callback', provider=provider, _external=True),
        }, headers={'Accept': 'application/json'})
        
        if token_response.status_code != 200:
            return render_template('error.html', error=f'Failed to get access token: {token_response.text}'), 401
        
        token_data = token_response.json()
        oauth2_token = token_data.get('access_token')
        id_token = token_data.get('id_token')  # This is the JWT token from Google
        
        if not oauth2_token:
            return render_template('error.html', error='No access token received'), 401

        # Get user information from Google
        userinfo_response = requests.get(
            provider_data['userinfo']['url'],
            headers={'Authorization': f'Bearer {oauth2_token}'}
        )
        
        if userinfo_response.status_code != 200:
            return render_template('error.html', error='Failed to get user information'), 401
        
        user_info = userinfo_response.json()
        
        # Extract user details
        email = provider_data['userinfo']['email'](user_info)
        first_name = provider_data['userinfo']['first_name'](user_info)
        last_name = provider_data['userinfo']['last_name'](user_info)
        user_id = user_info.get('sub')  # Google's unique user ID
        
        # Prepare data for LiteFarm API (matching their loginWithGoogle endpoint)
        litefarm_data = {
            'language_preference': 'en'  # Default language preference
        }
        
        # Prepare headers with the Google JWT token
        litefarm_headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {id_token}' if id_token else f'Bearer {oauth2_token}'
        }
        
        # Send request to LiteFarm API
        litefarm_response = requests.post(
            f'{LITEFARM_URL}/login/google',
            json=litefarm_data,
            headers=litefarm_headers
        )
        
        print(f"-----> LiteFarm API Response Status: {litefarm_response.status_code}")
        print(f"-----> LiteFarm API Response Text: {litefarm_response.text}")
        print(f"-----> Chat ID from session: {session.get('telegram_chat_id')}")
        
        # Handle successful LiteFarm response
        if litefarm_response.status_code in [200, 201]:
            try:
                litefarm_json = litefarm_response.json()
                litefarm_token = litefarm_json.get('id_token')
                
                if litefarm_token:
                    # Decode JWT token to get user_id
                    jwt_payload = decode_jwt_token(litefarm_token)
                    litefarm_user_id = jwt_payload.get('user_id')
                    
                    print(f"-----> JWT Payload: {jwt_payload}")
                    print(f"-----> LiteFarm User ID: {litefarm_user_id}")
                    
                    # Get chat_id from session
                    chat_id = session.get('telegram_chat_id')
                    
                    print(f"-----> About to save data - Chat ID: {chat_id}, User ID: {litefarm_user_id}")
                    
                    # Save login data to database if we have both chat_id and user_id
                    if chat_id and litefarm_user_id:
                        # Run async function in sync context (Flask doesn't support async routes)
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            success = loop.run_until_complete(
                                save_login_data(chat_id, litefarm_token, litefarm_user_id)
                            )
                            if success:
                                print(f"Google login data saved successfully for chat_id: {chat_id}")
                            else:
                                print(f"Failed to save Google login data for chat_id: {chat_id}")
                        finally:
                            loop.close()
                    else:
                        print(f"-----> Cannot save data - Missing chat_id: {chat_id} or user_id: {litefarm_user_id}")
                    
                    # Store data in session for the success page
                    session['login_success'] = {
                        'token': litefarm_token,
                        'user': {
                            'email': email,
                            'first_name': first_name,
                            'last_name': last_name,
                            'user_id': litefarm_user_id
                        },
                        'email': email,
                        'chat_id': chat_id,
                        'litefarm_user_id': litefarm_user_id
                    }
                    
                    # Clear the OAuth state from session
                    session.pop('oauth2_state', None)
                    
                    # Redirect to success page instead of test results
                    return redirect(url_for('login_success'))
                    
            except (json.JSONDecodeError, ValueError):
                pass  # Fall through to test results display
        
        # Prepare result data for testing display
        result_data = {
            'google_user_info': {
                'user_id': user_id,
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'full_name': f'{first_name} {last_name}' if first_name and last_name else email
            },
            'google_tokens': {
                'access_token': oauth2_token,
                'id_token': id_token,
                'token_type': token_data.get('token_type', 'Bearer')
            },
            'litefarm_request': {
                'url': f'{LITEFARM_URL}/login/google',
                'headers': litefarm_headers,
                'data': litefarm_data
            },
            'litefarm_response': {
                'status_code': litefarm_response.status_code,
                'headers': dict(litefarm_response.headers),
                'response_text': litefarm_response.text
            }
        }
        
        # Try to parse LiteFarm response as JSON if possible
        try:
            litefarm_json = litefarm_response.json()
            result_data['litefarm_response']['json'] = litefarm_json
        except (json.JSONDecodeError, ValueError):
            result_data['litefarm_response']['json'] = None
        
        # Clear the OAuth state from session
        session.pop('oauth2_state', None)
        
        # Return the testing results
        return render_template('oauth_test_results.html', result=result_data)
        
    except requests.RequestException as e:
        return render_template('error.html', error=f'Network error: {str(e)}'), 500
    except Exception as e:
        return render_template('error.html', error=f'Unexpected error: {str(e)}'), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
        
        
        