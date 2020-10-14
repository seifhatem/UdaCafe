import json
from flask import request, _request_ctx_stack, jsonify
from functools import wraps
from jose import jwt
from urllib.request import urlopen


AUTH0_DOMAIN = 'seifhatem.us.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'udacafe'

## AuthError Exception
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code

## Auth Header

def get_token_auth_header():
    authorization_header = request.headers.get('Authorization', None)
    if not authorization_header:
        raise AuthError({'code': 'missing_header','description': 'Please include the Authorization header in the request'}, 403)
    try:
        token = authorization_header.split()[1]
    except Exception:
        raise AuthError({'code': 'header_parse','description': 'Formatting Error with the request header'}, 403)
    return token

def check_permissions(permission, payload):
    if permission not in payload['permissions']:
        raise AuthError({'code': 'unauthorized','description': 'Sorry, you are not authorized to perform the requested action.'}, 403)
    return True

def verify_decode_jwt(token):
    try:
        live_keys = json.loads(urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json').read())
        parsed_header = jwt.get_unverified_header(token)
        rsa_key = {}

        for key in live_keys['keys']:
            if key['kid'] == parsed_header['kid']:
                rsa_key = {
                    'kty': key['kty'],
                    'kid': key['kid'],
                    'use': key['use'],
                    'n': key['n'],
                    'e': key['e']
                }
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=ALGORITHMS,
            audience=API_AUDIENCE,
            issuer='https://' + AUTH0_DOMAIN + '/'
        )
        return payload

    except jwt.ExpiredSignatureError:
        raise AuthError({'code': 'token_expired','description': 'Session expired'}, 403)
    except Exception:
        raise AuthError({'code': 'token_validation_failure','description': 'There was an error validating your token'}, 403)

def allowedPermissions():
    token = get_token_auth_header()
    payload = verify_decode_jwt(token)
    return jsonify(permissions=payload['permissions'])

def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            payload = verify_decode_jwt(token)
            check_permissions(permission, payload)
            return f(payload, *args, **kwargs)

        return wrapper
    return requires_auth_decorator
