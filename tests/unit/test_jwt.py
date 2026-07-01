import pytest
import uuid
from datetime import timedelta
from app.security.jwt import create_access_token, decode_access_token

def test_jwt_creation_and_decoding():
    user_id = str(uuid.uuid4())
    token = create_access_token(subject=user_id)
    
    decoded = decode_access_token(token)
    assert decoded["sub"] == user_id
    assert "exp" in decoded

def test_jwt_expiration():
    user_id = str(uuid.uuid4())
    token = create_access_token(subject=user_id, expires_delta=timedelta(seconds=-10))
    
    with pytest.raises(ValueError, match="Token has expired"):
        decode_access_token(token)
