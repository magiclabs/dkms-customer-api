import jwt
import json
from jwcrypto import jwk
import os
import pytest
from unittest.mock import patch, MagicMock

os.environ["DKMS_KMS_KEY_ID"] = "fc2039ff-c159-4467-9dee-39baebc10194"
os.environ["AWS_DEFAULT_REGION"] = "us-west-2"
os.environ[
    "JWKS_URL"
] = "https://example.com/.well-known/jwks.json"  # this can be anything because we mock the response in a fixture

# openssl genrsa -out private_key.pem 2048
test_private_key = """-----BEGIN PRIVATE KEY-----
MIIEvwIBADANBgkqhkiG9w0BAQEFAASCBKkwggSlAgEAAoIBAQDsKDYU4UiGp4fc
IIRqV431vWPVk1WT5x+q5OQj8E6F5l3uZvzlJpQ2NF3U0/GpUVyYjtyj8CLD4ZvV
pPA0tboSJkqH3jIm+mm0Hi4asQAEVaB6/bIoUQs59xRdp10kxgHENE0J5Zn0yCXz
TFHQ7pzOIvusuZ+8XILMTSag85bB/nLyOaK5Pxb9YCqqwptpwhff2tdXUo8Hm4xM
PolKANMcusarKWg4iYF3308SOQgeM5ZpD/7+yuME0LNSCV5c/NrMAfvvtiWsMY7w
4ucCVITp04N0vbE0irAVB2ucE+bLJUiy0/f9KrP+YkJrv/a2xnPfojUT+QiJ0Rfh
KgpjnH5xAgMBAAECggEAFXRpxWfaMPGTdDo4DXk62nKEWWjzQ2aiB+KXn3Q7jgqp
yfjtTNw+ZtZHGAjRUbKkmO+RuAse/XDHuZcsg31nFDMKXmGfaM8jP0vmoGIoQDyP
Qd0+jE8gl/mMjh2gZrDehDbEMPv9CrIMUJhEbpjfAhNHjh+nFXPKJkl0EvdOYP1S
PpC+LDBBo+JdhYCgQDgxUt4HTsqh09MnlB6ycWuMAC+XQ0ndoqJaOdeDh504fXsA
gBlj9VFC3QHQafMwuZ6E8SHtZyQV2RpZ8McV6NMjbsedCiIacPweAxrpA7xh9/Tx
WNW8BmfbQ6qI6psNlT6Mcru4Ed1+fktT1WXxpv2s4QKBgQD8uv7KyPpH7YAizVDj
PMooU2OMPtnK/BYj0wj1M5HeYl0NgJr6c561TdQ7CrYoFHRm1DGiMUUj/O8q10c6
BwmxLsUzf9fU3xBV2Ajp/Dr4ZoMqtejhWOjSw2r+/HPVbcjEvNZUAhkobkZ7/9g6
F2Q2WST7llx8mnRB8InGD1KkLQKBgQDvNlPV67FWwJb2agkpvEySdYioBLIup/xG
iZ89OuUMeTOGTonq3fEJugGPYVdbwFS6U4TXe9zvWNtd1luGExSA6WO27z7XwjM8
kwC90reXnAjlAqFdGNXC3dNITo9l4X4rI91FNfqDagW8ZbcOj44yHoRT0oFFhCM3
FJSc3IeZ1QKBgQDwgoQ3N0v3Z22psPppRlCcT79MmANryLrJHOxJbOpEWBd14g2a
iq1enNJ73ZW8Trr3oLgbQggqV2rDultuPYRbucaxW9hqHF3PU+gnxIHaIrRw0Ozu
h04KRS5tupIBapjFoW/WQqjucQNivfdoURptHiizxEP/0H0Sw3ZZpftfgQKBgQCO
v8fVv7nrQDCWSf6/1iuHtvXe9jZymzJz0YqiWnP3NpilzFaHPvypRkPKEVe1XBfz
vQVoJfVZK5h07gdeAiLZLu2fbDP/Q1eaDUuC+60tnyK7rw8mZDyj9gYwfxkZvi+x
hMx1kdm19F4J6FUOLmK3y/hBoTwdhNYS94gb94pAJQKBgQDq5cm5U3uhqmH3dx8h
JkcMGY+YESODC3H1MuX177AkkSm9gGg1HGSU9QR64SVUthm0AZSY7Nzyq8Tql0Ar
uAcEfSkqqLds9f8qCgx4dnA3RHz86Od0duQMmRomlPFvxoyMXuSpOFFa2FASdcdZ
2XkkxrNLuFc2AmJlYYPyiXOx1g==
-----END PRIVATE KEY-----
"""

# openssl rsa -in private_key.pem -pubout -out public_key.pem
test_public_key = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA7Cg2FOFIhqeH3CCEaleN
9b1j1ZNVk+cfquTkI/BOheZd7mb85SaUNjRd1NPxqVFcmI7co/Aiw+Gb1aTwNLW6
EiZKh94yJvpptB4uGrEABFWgev2yKFELOfcUXaddJMYBxDRNCeWZ9Mgl80xR0O6c
ziL7rLmfvFyCzE0moPOWwf5y8jmiuT8W/WAqqsKbacIX39rXV1KPB5uMTD6JSgDT
HLrGqyloOImBd99PEjkIHjOWaQ/+/srjBNCzUgleXPzazAH777YlrDGO8OLnAlSE
6dODdL2xNIqwFQdrnBPmyyVIstP3/Sqz/mJCa7/2tsZz36I1E/kIidEX4SoKY5x+
cQIDAQAB
-----END PUBLIC KEY-----
"""

key = jwk.JWK.from_pem(test_public_key.encode())
jwks_dict = key.export_public(as_dict=True)


@pytest.fixture(autouse=True)
def jwks_provider():
    """Mock the jwks provider."""
    with patch("urllib.request.urlopen") as mock_urlopen:
        # Mock response object to mimic the urlopen response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"keys": [jwks_dict]}).encode(
            "utf-8"
        )
        mock_response.__enter__.return_value = mock_response  # Handle context manager

        # Set this mock response as the return value of urlopen
        mock_urlopen.return_value = mock_response
        yield


@pytest.fixture
def user_jwt():
    """Generate and return a valid JWT signed by test_private_key."""
    yield jwt.encode(
        {"sub": "test_user", "ewi": "abcd1234"},
        test_private_key,
        algorithm="RS256",
        headers={"kid": jwks_dict["kid"]},
    )
