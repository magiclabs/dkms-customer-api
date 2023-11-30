import json
import os
import requests

BASE_URL = os.getenv("BASE_URL")
assert (
    BASE_URL is not None
), "BASE_URL environment variable must be set to a value like 'https://oon4ztxwte.execute-api.us-west-2.amazonaws.com/'"

JWT = os.getenv("JWT")
assert JWT is not None, "JWT environment variable must be set"


def test_healthz():
    url = f"{BASE_URL}/healthz"
    response = requests.get(url)
    assert response.status_code == 200
    assert response.json() == {
        "data": {},
        "error_code": "",
        "message": "",
        "status": "OK",
    }


def test_encrypt(plaintext: str) -> str:
    url = f"{BASE_URL}/encrypt"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {JWT}"}
    data = json.dumps({"plaintext": plaintext})
    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    assert "ciphertext" in response.json()["data"]
    return response.json()["data"]["ciphertext"]


def test_decrypt(ciphertext: str) -> str:
    url = f"{BASE_URL}/decrypt"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {JWT}"}
    data = json.dumps({"ciphertext": ciphertext})
    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    assert "plaintext" in response.json()["data"]
    return response.json()["data"]["plaintext"]


if __name__ == "__main__":
    test_healthz()
    input = "abracadabra"
    ciphertext = test_encrypt(input)
    output = test_decrypt(ciphertext)
    assert input == output
    print(f"Success: {input} -> {ciphertext} -> {output}")
