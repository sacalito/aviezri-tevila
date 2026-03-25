from imports import *

AUTH_TOKEN = "FeGHtFHiQmukbZXB4ygUZiJPqeiKD6318Q0xZjzbAKT2L1MC72IB8ed2hIZ9J6jX"

def require_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return {'message': 'No token provided'}, 401
        
        try:
            token_type, token = auth_header.split()
            if token_type.lower() != 'bearer':
                return {'message': 'Invalid token type'}, 401
            if token != AUTH_TOKEN:
                return {'message': 'Invalid token'}, 401
        except ValueError:
            return {'message': 'Invalid token format'}, 401

        return f(*args, **kwargs)
    return decorated