from flask import Flask, redirect, url_for, request, session, abort, flash, render_template, current_app
import requests
import secrets
from urllib.parse import urlencode
import sys
import os

# Add the src directory to the Python path to import config
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from config import config

# Validate Flask-specific environment variables
config.validate_flask_vars()

app = Flask(__name__)
# Set a secret key for session management
app.secret_key = config.FLASK_SECRET_KEY or secrets.token_urlsafe(32)

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
        'scope': ['https://www.googleapis.com/auth/userinfo.email']
    }
}

@app.route('/')
def hello_world():
    return render_template('index.html')

@app.route('/authorize/<provider>')
def oauth2_authorize(provider):
    provider_data = current_app.config['OAUTH2_PROVIDERS'].get(provider)
    if provider_data is None:
        abort(404)

    # generate a random string for the state parameter
    session['oauth2_state'] = secrets.token_urlsafe(16)

    # create a query string with all the OAuth2 parameters
    # Use 'scope' key instead of 'scopes' to match the config
    qs = urlencode({
        'client_id': provider_data['client_id'],
        'redirect_uri': url_for('oauth2_callback', provider=provider,
                                _external=True),
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
        return 'Provider not found', 404
    
    if 'error' in request.args:
        for k, v in request.args.items():
            if k.startswith('error'):
                flash(f'{k}: {v}')
        return redirect(url_for('index'))

    if request.args['state'] != session.get('oauth2_state'):
        abort(401)

    if 'code' not in request.args:
        abort(401)

    response = requests.post(provider_data['token_url'], data={
        'client_id': provider_data['client_id'],
        'client_secret': provider_data['client_secret'],
        'code': request.args['code'],
        'grant_type': 'authorization_code',
        'redirect_uri': url_for('oauth2_callback', provider=provider,
                                _external=True),
    }, headers={'Accept': 'application/json'})
    if response.status_code != 200:
        abort(401)
    oauth2_token = response.json().get('access_token')
    if not oauth2_token:
        abort(401)

    return oauth2_token
        
        