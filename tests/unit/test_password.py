import pytest
from app.security.password import verify_password, get_password_hash

def test_password_hashing():
    password = "supersecretpassword123!"
    hashed = get_password_hash(password)
    
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False
