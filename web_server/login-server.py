from flask import Flask, redirect, url_for, request, session, abort, render_template, current_app, jsonify
import requests
import secrets
from urllib.parse import urlencode
import sys
import os
import json
import asyncio
import logging
import re
from datetime import datetime, timezone, timedelta
from markupsafe import escape

# Configure logging to avoid sensitive data exposure
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root directory to the Python path first
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Add the src directory to the Python path to import config
sys.path.insert(0, os.path.join(project_root, 'src'))
from config import config

# Import database and services after path setup
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
from shared.utils.jwt_utils import decode_jwt_token

# Validate Flask-specific environment variables
config.validate_flask_vars()

app = Flask(__name__)
# Set a secret key for session management
app.secret_key = config.FLASK_SECRET_KEY or secrets.token_urlsafe(32)

# Security configurations
app.config.update(
    SESSION_COOKIE_SECURE=True if not config.DEBUG else False,  # HTTPS only in production
    SESSION_COOKIE_HTTPONLY=True,  # Prevent XSS access to session cookies
    SESSION_COOKIE_SAMESITE='Lax',  # CSRF protection
    PERMANENT_SESSION_LIFETIME=timedelta(hours=1),  # Session timeout
)

# Add security headers
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    if not config.DEBUG:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# Input validation functions
def validate_email(email):
    """Validate email format"""
    if not email or len(email) > 254:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_chat_id(chat_id):
    """Validate chat_id is a positive integer"""
    try:
        chat_id_int = int(chat_id)
        return 1 <= chat_id_int <= 9999999999  # Reasonable range for Telegram chat IDs
    except (ValueError, TypeError):
        return False

def sanitize_error_message(error_msg, is_debug=False):
    """Sanitize error messages to prevent information disclosure"""
    if is_debug:
        return escape(str(error_msg))
    
    # Generic error messages for production
    generic_errors = {
        'connection': 'Servicio temporalmente no disponible. Intenta más tarde.',
        'timeout': 'Tiempo de espera agotado. Intenta nuevamente.',
        'auth': 'Error de autenticación. Verifica tus credenciales.',
        'server': 'Error del servidor. Intenta más tarde.',
        'invalid': 'Datos inválidos. Verifica la información ingresada.'
    }
    
    error_lower = str(error_msg).lower()
    if 'connection' in error_lower or 'refused' in error_lower:
        return generic_errors['connection']
    elif 'timeout' in error_lower:
        return generic_errors['timeout']
    elif 'auth' in error_lower or 'credential' in error_lower:
        return generic_errors['auth']
    elif 'server' in error_lower or '50' in error_lower:
        return generic_errors['server']
    else:
        return generic_errors['invalid']

# Set the LiteFarm URL
LITEFARM_URL = config.URL_LITEFARM

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
# Initialize services
def create_user_service():
    return UserService(lambda session: UserRepository(session))

def create_chat_service():
    return ChatSessionService(lambda session: ChatSessionRepository(session))

def create_token_service():
    return TokenService(lambda session: TokenRepository(session))

# Helper function to save login data to database
async def save_login_data(chat_id: int, token: str, litefarm_user_id: str):
    """
    Save login data to database: user, chat session, and token
    """
    logger.info(f"Starting save_login_data for chat_id: {chat_id}")
    try:
        async with AsyncSessionLocal() as db_session:
            user_service = create_user_service()
            chat_service = create_chat_service()
            token_service = create_token_service()
            
            # Create or get user
            user_dto = CreateUserDTO(litefarm_user_id=litefarm_user_id)
            user = await user_service.create_user(user_dto, db_session)
            logger.info(f"User created/retrieved successfully")
            
            # Create chat session (this will deactivate previous sessions)
            # TODO: Think about multiple users per chat
            chat_dto = ChatSessionCreateDTO(
                litefarm_user_id=litefarm_user_id,
                telegram_chat_id=chat_id
            )
            chat_session = await chat_service.create_chat_session(chat_dto, db_session)
            logger.info(f"Chat session created successfully")
            
            # Calculate token expiration (assuming 24 hours)
            # TODO: change to specified hours in the future
            expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
            
            # Save token to the token table in the database
            token_dto = TokenCreateDTO(
                chat_session_id=chat_session.id,
                token=token,
                expires_at=expires_at
            )
            token_obj = await token_service.create_token(token_dto, db_session)
            logger.info(f"Token created successfully")
            
            # Commit the transaction
            await db_session.commit()
            
            logger.info(f"Successfully saved login data for chat_id: {chat_id}")
            return True
            
    except Exception as e:
        logger.error(f"Error saving login data: {sanitize_error_message(str(e), config.DEBUG)}")
        return False

@app.route('/login/<int:chat_id>')
def login_with_chat_id(chat_id):
    """Handle login with chat_id in URL path"""
    if not validate_chat_id(chat_id):
        return render_template('error.html', error='ID de chat inválido'), 400
    # Store chat_id in session for later use
    session['telegram_chat_id'] = chat_id
    session.permanent = True
    return render_template('index.html', chat_id=chat_id)

## post request to /login
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login_post():
    """Handle email/password login by forwarding to LiteFarm API"""
    try:
        # Get form data with input validation
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        # Validate required fields
        if not email or not password:
            return jsonify({'success': False, 'error': 'Email y contraseña son requeridos'}), 400
            
        # Validate email format
        if not validate_email(email):
            return jsonify({'success': False, 'error': 'Formato de email inválido'}), 400
            
        # Validate password length (basic validation)
        if len(password) < 1 or len(password) > 128:
            return jsonify({'success': False, 'error': 'Contraseña inválida'}), 400
        
        # Get screen dimensions with validation
        try:
            screen_width = max(320, min(int(request.form.get('screen_width', 1920)), 7680))
            screen_height = max(240, min(int(request.form.get('screen_height', 1080)), 4320))
        except (ValueError, TypeError):
            screen_width, screen_height = 1920, 1080
        
        # Prepare request data in the format expected by LiteFarm API
        litefarm_data = {
            'user': {
                'email': email,
                'password': password
            },
            'screenSize': {
                'screen_width': screen_width,
                'screen_height': screen_height
            }
        }
        
        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': request.headers.get('User-Agent', 'Mozilla/5.0 (Unknown)'),
            'Accept-Language': request.headers.get('Accept-Language', 'es-ES,es;q=0.9')
        }
        
        # Add forwarded IP if available (but sanitize it)
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            # Take only the first IP and validate format
            first_ip = forwarded_for.split(',')[0].strip()
            if re.match(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$', first_ip):
                headers['X-Forwarded-For'] = first_ip
        
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
                                logger.info(f"Login data saved successfully")
                            else:
                                logger.warning(f"Failed to save login data")
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
                error_message = sanitize_error_message(error_data.get('message', f'Error del servidor: {response.status_code}'), config.DEBUG)
            except json.JSONDecodeError:
                error_message = sanitize_error_message(f'Error del servidor: {response.status_code}', config.DEBUG)
            
            return jsonify({'success': False, 'error': error_message}), response.status_code
    
    except requests.exceptions.ConnectionError as e:
        error_msg = sanitize_error_message(str(e), config.DEBUG)
        return jsonify({'success': False, 'error': error_msg}), 503
    
    except requests.exceptions.Timeout:
        return jsonify({'success': False, 'error': 'Tiempo de espera agotado. Intenta nuevamente.'}), 504
    
    except requests.exceptions.RequestException as e:
        error_msg = sanitize_error_message(str(e), config.DEBUG)
        return jsonify({'success': False, 'error': error_msg}), 500
    
    except Exception as e:
        # Log the error for debugging
        logger.error(f"Unexpected error in login_post: {sanitize_error_message(str(e), True)}")
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
        if not validate_chat_id(chat_id):
            return render_template('error.html', error='ID de chat inválido'), 400
        # Store chat_id in session for later use
        session['telegram_chat_id'] = int(chat_id)
        session.permanent = True
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
    logger.info(f"Generated redirect URI for {provider}")

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
        return render_template('error.html', error='Proveedor de autenticación no encontrado'), 404
    
    if 'error' in request.args:
        error_type = request.args.get('error', '')
        error_description = request.args.get('error_description', '')
        
        # Translate common OAuth errors to Spanish
        if error_type == 'access_denied':
            error_message = 'Acceso denegado. Has cancelado la autorización.'
        elif error_type == 'invalid_request':
            error_message = 'Solicitud inválida. Por favor, intenta nuevamente.'
        elif error_type == 'unauthorized_client':
            error_message = 'Cliente no autorizado.'
        elif error_type == 'unsupported_response_type':
            error_message = 'Tipo de respuesta no soportado.'
        elif error_type == 'invalid_scope':
            error_message = 'Alcance inválido.'
        elif error_type == 'server_error':
            error_message = 'Error del servidor. Por favor, intenta más tarde.'
        elif error_type == 'temporarily_unavailable':
            error_message = 'Servicio temporalmente no disponible. Intenta más tarde.'
        else:
            error_message = f'Error de autenticación: {error_description or error_type}'
        
        return render_template('error.html', error=error_message)

    if request.args.get('state') != session.get('oauth2_state'):
        return render_template('error.html', error='Parámetro de estado inválido. Por favor, intenta iniciar sesión nuevamente.'), 401

    if 'code' not in request.args:
        return render_template('error.html', error='Código de autorización no recibido. Por favor, intenta nuevamente.'), 401

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
            error_msg = sanitize_error_message(f'Error al obtener el token de acceso: {token_response.text}', config.DEBUG)
            return render_template('error.html', error=error_msg), 401
        
        token_data = token_response.json()
        oauth2_token = token_data.get('access_token')
        id_token = token_data.get('id_token')  # This is the JWT token from Google
        
        if not oauth2_token:
            return render_template('error.html', error='No se recibió el token de acceso'), 401

        # Get user information from Google
        userinfo_response = requests.get(
            provider_data['userinfo']['url'],
            headers={'Authorization': f'Bearer {oauth2_token}'}
        )
        
        if userinfo_response.status_code != 200:
            return render_template('error.html', error='Error al obtener la información del usuario'), 401
        
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
        if config.DEBUG:
            print(f"-----> LiteFarm API Response Text: {litefarm_response.text}")
        logger.info(f"Chat ID from session available: {bool(session.get('telegram_chat_id'))}")
        
        # Handle successful LiteFarm response
        if litefarm_response.status_code in [200, 201]:
            try:
                litefarm_json = litefarm_response.json()
                litefarm_token = litefarm_json.get('id_token')
                
                if litefarm_token:
                    # Decode JWT token to get user_id
                    jwt_payload = decode_jwt_token(litefarm_token)
                    litefarm_user_id = jwt_payload.get('user_id')
                    
                    if config.DEBUG:
                        print(f"-----> JWT Payload: {jwt_payload}")
                    logger.info(f"LiteFarm User ID obtained successfully")
                    
                    # Get chat_id from session
                    chat_id = session.get('telegram_chat_id')
                    
                    logger.info(f"About to save data - Chat ID available: {bool(chat_id)}, User ID available: {bool(litefarm_user_id)}")
                    
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
                                logger.info(f"Google login data saved successfully")
                            else:
                                logger.warning(f"Failed to save Google login data")
                        finally:
                            loop.close()
                    else:
                        logger.warning("Cannot save data - Missing chat_id or user_id")
                    
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
                return render_template('error.html', error='Error al procesar la respuesta del servidor de autenticación'), 500
        
        # Handle failed LiteFarm response
        elif litefarm_response.status_code == 401:
            return render_template('error.html', error='Credenciales inválidas para LiteFarm. Tu cuenta de Google no está asociada con una cuenta de LiteFarm válida.'), 401
        elif litefarm_response.status_code == 403:
            return render_template('error.html', error='Acceso denegado a LiteFarm. Verifica que tu cuenta tenga los permisos necesarios.'), 403
        elif litefarm_response.status_code == 404:
            return render_template('error.html', error='Tu cuenta de Google no está registrada en LiteFarm. Por favor, crea una cuenta primero.'), 404
        elif litefarm_response.status_code >= 500:
            return render_template('error.html', error='Error del servidor de LiteFarm. Por favor, intenta más tarde.'), 500
        else:
            try:
                error_data = litefarm_response.json()
                error_message = sanitize_error_message(error_data.get('message', f'Error de autenticación con LiteFarm: {litefarm_response.status_code}'), config.DEBUG)
            except json.JSONDecodeError:
                error_message = sanitize_error_message(f'Error de autenticación con LiteFarm: {litefarm_response.status_code}', config.DEBUG)
            return render_template('error.html', error=error_message), litefarm_response.status_code
        
        # Prepare result data for testing display (fallback)
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
        
    except requests.exceptions.ConnectionError as e:
        error_msg = sanitize_error_message(str(e), config.DEBUG)
        return render_template('error.html', error=error_msg), 503
    except requests.exceptions.Timeout:
        return render_template('error.html', error='Tiempo de espera agotado al conectar con el servidor de autenticación. Intenta nuevamente.'), 504
    except requests.RequestException as e:
        error_msg = sanitize_error_message(str(e), config.DEBUG)
        return render_template('error.html', error=error_msg), 500
    except Exception as e:
        logger.error(f"Unexpected error in oauth2_callback: {sanitize_error_message(str(e), True)}")
        return render_template('error.html', error='Error inesperado durante la autenticación'), 500


if __name__ == '__main__':
    # Security: Don't run in debug mode in production
    debug_mode = config.DEBUG if hasattr(config, 'DEBUG') else False
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
        
        
        