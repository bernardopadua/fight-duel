from rest_framework.authentication import get_authorization_header
from rest_framework.request import Request
from django.http import HttpRequest

import time, base64, json, hmac, hashlib
from typing import Any

class JWTError(Exception):
    pass

class JWTExpiredError(Exception):
    pass

def encode_base64(data: dict[str, Any]) -> str:
    encoded_data = json.dumps(data, separators=(',', ':'), sort_keys=True)
    return base64.urlsafe_b64encode(encoded_data.encode()).decode().rstrip('=')

def encode_base64_bytes(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip('=')

def decode_base64(data: str) -> dict[str, Any]:
    remainder = len(data) % 4
    if remainder > 0:
        data += '=' * (4 - remainder)
    return json.loads(base64.urlsafe_b64decode(data).decode())

def sign_token(encoded_header: str, encoded_payload: str, secret_key: str) -> bytes:
    token_signature = hmac.new(
        key=secret_key.encode(),
        msg=f"{encoded_header}.{encoded_payload}".encode(),
        digestmod=hashlib.sha256
    ).digest()

    return token_signature

def create_token(user_id: int, secret_key: str, time_expires: int = 3600) -> str:
    payload = {
        "userId": user_id,
        "exp": int(time.time()) + time_expires,
        "iat": int(time.time())
    }

    header = {
        "alg": "HS256",
        "typ": "JWT"
    }

    encoded_header = encode_base64(header)
    encoded_payload = encode_base64(payload)

    token_signature = sign_token(encoded_header, encoded_payload, secret_key)

    return f"{encoded_header}.{encoded_payload}.{encode_base64_bytes(token_signature)}"

def decode_token(token: str, secret_key: str) -> dict[str, Any]:
    header, payload, signature = token.split('.')
    token_signature = sign_token(header, payload, secret_key)

    if not hmac.compare_digest(encode_base64_bytes(token_signature), signature):
        raise JWTError("Invalid JWT signature")
    
    payload = decode_base64(payload)

    if payload.get("exp", 0) < time.time():
        #must refresh jwt token
        raise JWTExpiredError("JWT token expired")

    return payload

def get_token_from_request(request: Request | HttpRequest | None) -> str | None:
    if not request:
        return None
    
    token: str | None = None

    auth_header = get_authorization_header(request).split()
    if auth_header and len(auth_header) >= 2 and auth_header[0] == b'Bearer':
        token = auth_header[1].decode()
    else:
        token = request.COOKIES.get("Authorization-JWT", None)

    return token

def get_expiration_from_request(request: Request | HttpRequest) -> int:
    token = get_token_from_request(request)
    if not token:
        return 0

    header, payload, signature = token.split('.')
    return decode_base64(payload).get("exp", 0)