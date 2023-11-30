import base64
import boto3
import json
import jwt
import logging
import os
import traceback
import urllib.request
from http import HTTPStatus

logger = logging.getLogger()
logger.setLevel(logging.INFO)

kms_key_id = os.getenv("DKMS_KMS_KEY_ID", None)
assert kms_key_id is not None, "DKMS_KMS_KEY_ID environment variable must be set"
kms_client = boto3.client("kms")

jwks_url = os.getenv("JWKS_URL", None)
assert jwks_url is not None, "JWKS_URL environment variable must be set"
jwks_client = jwt.PyJWKClient(jwks_url)


class AuthenticationError(Exception):
    """Raised when authentication fails."""

    pass


def handler(event, context) -> dict:
    """Process an API Gateway event and return a response."""

    log_event = event.copy()
    log_event["body"] = "omitted"  # Do not log potentially sensitive data
    logger.info(log_event)
    try:
        return router(event)
    except AuthenticationError as e:
        return return_handler(
            message="Access Denied",
            status=HTTPStatus.UNAUTHORIZED,
            error_code="ACCESS_DENIED",
        )
    except Exception as e:
        logger.info(traceback.format_exc())
        return return_handler(
            message="an unknown error occurred",
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
            error_code="UNKNOWN_ERROR",
        )


def authenticate(event) -> dict:
    """Authenticate the request."""
    auth_header = event["headers"].get("authorization", None)
    logger.info(auth_header)
    if not auth_header:
        raise AuthenticationError("No Authorization header provided")

    token = auth_header.split("Bearer ")[1]
    signing_key = jwks_client.get_signing_key_from_jwt(token)
    payload = jwt.decode(token, signing_key.key, algorithms=["RS256"])
    logger.info(payload)
    assert payload.get("ewi"), "No ewi provided in JWT"
    return payload


def router(event) -> dict:
    """Route the API request to the correct handler."""
    http_method = event["requestContext"]["http"]["method"]
    path = event["rawPath"]

    if http_method == "GET" and path == "/healthz":
        return return_handler(status=HTTPStatus.OK)
    elif http_method == "POST" and path == "/encrypt":
        payload = authenticate(event)
        return encrypt(
            event["body"],
            kms_key_id,
            encryption_context={"ewi": payload.get("ewi")},
        )
    elif http_method == "POST" and path == "/decrypt":
        payload = authenticate(event)
        return decrypt(
            event["body"],
            kms_key_id,
            encryption_context={"ewi": payload.get("ewi")},
        )

    return return_handler(
        message=f"path {path} not found",
        status=HTTPStatus.NOT_FOUND,
        error_code="INVALID_PATH",
    )


def encrypt(body: str, kms_key_id: str, encryption_context: dict) -> dict:
    """Handle an encrypt request."""
    if body is None:
        return return_handler(
            status=HTTPStatus.BAD_REQUEST, message="no body", error_code="INVALID_INPUT"
        )
    try:
        parsed_body = json.loads(body)
    except json.decoder.JSONDecodeError:
        return return_handler(
            status=HTTPStatus.BAD_REQUEST,
            message="invalid json in body",
            error_code="INVALID_INPUT",
        )
    if parsed_body.get("plaintext") is None:
        return return_handler(
            status=HTTPStatus.BAD_REQUEST,
            message="no plaintext provided",
            error_code="INVALID_INPUT",
        )

    response = kms_client.encrypt(
        KeyId=kms_key_id,
        EncryptionContext=encryption_context,
        Plaintext=parsed_body.get("plaintext"),
    )
    encrypted_response = base64.b64encode(response["CiphertextBlob"]).decode("utf-8")
    return return_handler(status=HTTPStatus.OK, data={"ciphertext": encrypted_response})


def decrypt(body: str, kms_key_id: str, encryption_context: dict) -> dict:
    """Handle a decrypt request."""
    if body is None:
        return return_handler(
            status=HTTPStatus.BAD_REQUEST, message="no body", error_code="INVALID_INPUT"
        )
    try:
        parsed_body = json.loads(body)
    except json.decoder.JSONDecodeError:
        return return_handler(
            status=HTTPStatus.BAD_REQUEST,
            message="invalid json in body",
            error_code="INVALID_INPUT",
        )
    if parsed_body.get("ciphertext") is None:
        return return_handler(
            status=HTTPStatus.BAD_REQUEST,
            message="no ciphertext provided",
            error_code="INVALID_INPUT",
        )

    decoded_payload = base64.b64decode(parsed_body["ciphertext"])
    response = kms_client.decrypt(
        KeyId=kms_key_id,
        EncryptionContext=encryption_context,
        CiphertextBlob=decoded_payload,
    )
    decrypted_data = response["Plaintext"].decode("utf-8")
    return return_handler(status=HTTPStatus.OK, data={"plaintext": decrypted_data})


def return_handler(
    data: dict = {},
    error_code: str = "",
    message: str = "",
    status: HTTPStatus = HTTPStatus.OK,
) -> dict:
    """Return a standard data structure for API Gateway responses"""
    logger.info(
        {
            "data": "omitted",  # Do not log potentially sensitive data
            "error_code": error_code,
            "message": message,
            "status": status.name,
            "statusCode": status.value,
        }
    )
    return {
        "statusCode": status.value,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(
            {
                "data": data,
                "error_code": error_code,
                "message": message,
                "status": status.name,
            }
        ),
    }
