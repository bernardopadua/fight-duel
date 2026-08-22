import time, base64, json, hmac, hashlib
from typing import Any

class JWTError(Exception):
    pass

class JWTExpiredError(Exception):
    pass

def encodeBase64(data: dict[str, Any]) -> str:
    encoded_data = json.dumps(data, separators=(',', ':'), sort_keys=True)
    return base64.urlsafe_b64encode(encoded_data.encode()).decode().rstrip('=')

def encodeBase64Bytes(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip('=')

def decodeBase64(data: str) -> dict[str, Any]:
    remainder = len(data) % 4
    if remainder > 0:
        data += '=' * (4 - remainder)
    return json.loads(base64.urlsafe_b64decode(data).decode())

def signToken(encodedHeader: str, encodedPayload: str, secretKey: str) -> bytes:
    tokenSignature = hmac.new(
        key=secretKey.encode(),
        msg=f"{encodedHeader}.{encodedPayload}".encode(),
        digestmod=hashlib.sha256
    ).digest()

    return tokenSignature

def createToken(userId: int, secretKey: str, timeExpires: int = 3600) -> str:
    payload = {
        "userId": userId,
        "exp": int(time.time()) + timeExpires,
        "iat": int(time.time())
    }

    header = {
        "alg": "HS256",
        "typ": "JWT"
    }

    encodedHeader = encodeBase64(header)
    encodedPayload = encodeBase64(payload)

    tokenSignature = signToken(encodedHeader, encodedPayload, secretKey)

    return f"{encodedHeader}.{encodedPayload}.{encodeBase64Bytes(tokenSignature)}"

def decodeToken(token: str, secretKey: str) -> dict[str, Any]:
    header, payload, signature = token.split('.')
    tokenSignature = signToken(header, payload, secretKey)

    if not hmac.compare_digest(encodeBase64Bytes(tokenSignature), signature):
        raise JWTError("Invalid JWT signature")
    
    payload = decodeBase64(payload)

    if payload.get("exp", 0) < time.time():
        #must refresh jwt token
        raise JWTExpiredError("JWT token expired")

    return payload
