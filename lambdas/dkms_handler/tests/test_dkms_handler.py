import base64
import json
import os
from unittest.mock import patch
from http import HTTPStatus

import index


def test_lambda_dkms_healthz():
    event = {
        "rawPath": "/healthz",
        "requestContext": {"http": {"method": "GET"}},
    }
    context = None

    response = index.handler(event, context)
    assert response == {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Credentials": True,
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "OPTIONS,GET,POST",
            "Access-Control-Allow-Origin": "*",
        },
        "body": '{"data": {}, "error_code": "", "message": "", "status": "OK"}',
    }


def test_router_healthz():
    with patch("index.return_handler") as mock_return_handler:
        event = {
            "rawPath": "/healthz",
            "requestContext": {"http": {"method": "GET"}},
        }
        index.router(event)
        mock_return_handler.assert_called_once_with(status=HTTPStatus.OK)


def test_router_encrypt(user_jwt):
    with patch("index.encrypt") as mock_encrypt:
        event = {
            "rawPath": "/encrypt",
            "requestContext": {"http": {"method": "POST"}},
            "headers": {
                "Content-Type": "application/json",
                "authorization": f"Bearer {user_jwt}",
            },
            "body": "test_data",
        }
        index.router(event)
        mock_encrypt.assert_called_once_with(
            "test_data",
            os.getenv("DKMS_KMS_KEY_ID"),
            encryption_context={"ewi": "abcd1234"},
        )


def test_router_decrypt(user_jwt):
    with patch("index.decrypt") as mock_decrypt:
        event = {
            "rawPath": "/decrypt",
            "requestContext": {"http": {"method": "POST"}},
            "headers": {
                "Content-Type": "application/json",
                "authorization": f"Bearer {user_jwt}",
            },
            "body": "test_data",
        }
        index.router(event)
        mock_decrypt.assert_called_once_with(
            "test_data",
            os.getenv("DKMS_KMS_KEY_ID"),
            encryption_context={"ewi": "abcd1234"},
        )


def test_router_invalid_path():
    with patch("index.return_handler") as mock_return_handler:
        event = {
            "rawPath": "/invalid",
            "headers": {"Content-Type": "application/json"},
            "requestContext": {"http": {"method": "GET"}},
        }
        index.router(event)
        mock_return_handler.assert_called_once_with(
            message=f"path /invalid not found",
            status=HTTPStatus.NOT_FOUND,
            error_code="INVALID_PATH",
        )


def test_encrypt_with_no_body():
    with patch("index.return_handler") as mock_return_handler:
        result = index.encrypt(None, "mock_kms_key_id", encryption_context={})
        mock_return_handler.assert_called_once_with(
            status=HTTPStatus.BAD_REQUEST, message="no body", error_code="INVALID_INPUT"
        )


def test_encrypt_with_invalid_json():
    with patch("index.return_handler") as mock_return_handler:
        result = index.encrypt("invalid json", "mock_kms_key_id", encryption_context={})
        mock_return_handler.assert_called_once_with(
            status=HTTPStatus.BAD_REQUEST,
            message="invalid json in body",
            error_code="INVALID_INPUT",
        )


def test_encrypt_with_no_plaintext():
    with patch("index.return_handler") as mock_return_handler:
        result = index.encrypt(json.dumps({}), "mock_kms_key_id", encryption_context={})
        mock_return_handler.assert_called_once_with(
            status=HTTPStatus.BAD_REQUEST,
            message="no plaintext provided",
            error_code="INVALID_INPUT",
        )


def test_encrypt_success():
    kms_response_mock = {"CiphertextBlob": b"encrypted"}
    with patch("index.return_handler") as mock_return_handler, patch(
        "index.kms_client.encrypt", return_value=kms_response_mock
    ) as mock_encrypt:
        result = index.encrypt(
            json.dumps({"plaintext": "secret"}),
            "mock_kms_key_id",
            encryption_context={"ewi": "abcd1234"},
        )
        mock_encrypt.assert_called_once_with(
            KeyId="mock_kms_key_id",
            EncryptionContext={"ewi": "abcd1234"},
            Plaintext="secret",
        )
        mock_return_handler.assert_called_once()  # Assert it was called, but not concerned with the exact args here


def test_decrypt_with_no_body():
    with patch("index.return_handler") as mock_return_handler:
        result = index.decrypt(None, "mock_kms_key_id", encryption_context={})
        mock_return_handler.assert_called_once_with(
            status=HTTPStatus.BAD_REQUEST, message="no body", error_code="INVALID_INPUT"
        )


def test_decrypt_with_invalid_json():
    with patch("index.return_handler") as mock_return_handler:
        result = index.decrypt("invalid json", "mock_kms_key_id", encryption_context={})
        mock_return_handler.assert_called_once_with(
            status=HTTPStatus.BAD_REQUEST,
            message="invalid json in body",
            error_code="INVALID_INPUT",
        )


def test_decrypt_with_no_ciphertext():
    with patch("index.return_handler") as mock_return_handler:
        result = index.decrypt(json.dumps({}), "mock_kms_key_id", encryption_context={})
        mock_return_handler.assert_called_once_with(
            status=HTTPStatus.BAD_REQUEST,
            message="no ciphertext provided",
            error_code="INVALID_INPUT",
        )


def test_decrypt_success():
    ciphertext = "encrypted data"
    encoded_ciphertext = base64.b64encode(ciphertext.encode("utf-8")).decode("utf-8")
    body = json.dumps({"ciphertext": encoded_ciphertext})
    kms_response_mock = {"Plaintext": b"decrypted data"}

    with patch("index.return_handler") as mock_return_handler, patch(
        "index.kms_client.decrypt", return_value=kms_response_mock
    ) as mock_decrypt:
        result = index.decrypt(
            body, "mock_kms_key_id", encryption_context={"ewi": "abcd1234"}
        )
        mock_decrypt.assert_called_once_with(
            KeyId="mock_kms_key_id",
            EncryptionContext={"ewi": "abcd1234"},
            CiphertextBlob=ciphertext.encode("utf-8"),
        )
        mock_return_handler.assert_called_once()  # Assert it was called, but not concerned with the exact args here


def test_return_handler_success():
    with patch("index.logger") as mock_logger:
        response = index.return_handler(data={"key": "value"}, status=HTTPStatus.OK)

        # Check if the response is correctly structured
        assert response["statusCode"] == HTTPStatus.OK.value
        assert response["headers"]["Content-Type"] == "application/json"
        assert json.loads(response["body"]) == {
            "data": {"key": "value"},
            "error_code": "",
            "message": "",
            "status": "OK",
        }

        # Check if the log is correct
        mock_logger.info.assert_called_once_with(
            {
                "data": "omitted",
                "error_code": "",
                "message": "",
                "status": "OK",
                "statusCode": 200,
            }
        )


def test_return_handler_error():
    with patch("index.logger") as mock_logger:
        response = index.return_handler(
            error_code="ERROR_CODE",
            message="Error message",
            status=HTTPStatus.BAD_REQUEST,
        )

        # Check if the response is correctly structured
        assert response["statusCode"] == HTTPStatus.BAD_REQUEST.value
        assert json.loads(response["body"]) == {
            "data": {},
            "error_code": "ERROR_CODE",
            "message": "Error message",
            "status": "BAD_REQUEST",
        }

        # Check if the log is correct
        mock_logger.info.assert_called_once_with(
            {
                "data": "omitted",
                "error_code": "ERROR_CODE",
                "message": "Error message",
                "status": "BAD_REQUEST",
                "statusCode": 400,
            }
        )


def test_authenticate_jwt(user_jwt):
    event = {
        "rawPath": "/encrypt",
        "requestContext": {"http": {"method": "POST"}},
        "headers": {
            "Content-Type": "application/json",
            "authorization": f"Bearer {user_jwt}",
        },
        "body": "test_data",
    }
    payload = index.authenticate(event)
    assert payload == {"sub": "test_user", "ewi": "abcd1234"}


def test_options_request_healthz():
    event = {
        "rawPath": "/healthz",
        "requestContext": {"http": {"method": "OPTIONS"}},
    }
    context = None

    response = index.handler(event, context)
    assert response == {
        "headers": {
            "Access-Control-Allow-Credentials": True,
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "OPTIONS,GET,POST",
            "Access-Control-Allow-Origin": "*",
        },
        "statusCode": 200,
    }


def test_options_request_encrypt():
    event = {
        "rawPath": "/encrypt",
        "requestContext": {"http": {"method": "OPTIONS"}},
    }
    context = None

    response = index.handler(event, context)
    assert response == {
        "headers": {
            "Access-Control-Allow-Credentials": True,
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "OPTIONS,GET,POST",
            "Access-Control-Allow-Origin": "*",
        },
        "statusCode": 200,
    }
