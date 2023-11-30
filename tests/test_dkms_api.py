import aws_cdk as cdk
import aws_cdk.assertions as assertions

from deploy.dkms_api import DKMSCustomerAPIStack


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

test_jwks_url = "https://example.com/.well-known/jwks.json"


def test_dkms_api_stack():
    app = cdk.App()
    env_name = "test"
    stack = DKMSCustomerAPIStack(
        app,
        f"dkms-customer-api-{env_name}",
        env_name=env_name,
        jwks_url=test_jwks_url,
        cors_allow_origins="*",
    )
    template = assertions.Template.from_stack(stack)
    template.resource_count_is("AWS::KMS::Key", 1)
    template.has_resource_properties(
        "AWS::Lambda::Function",
        {
            "Runtime": "python3.11",
            "Handler": "index.handler",
            "Timeout": 30,
            "MemorySize": 128,
        },
    )
    template.has_resource_properties(
        "AWS::ApiGatewayV2::Api",
        {
            "Name": "dkms-customer-api-test",
            "ProtocolType": "HTTP",
        },
    )


def test_dkms_api_stack_all_options():
    app = cdk.App()
    env_name = "test"
    stack = DKMSCustomerAPIStack(
        app,
        f"dkms-customer-api-{env_name}",
        env_name=env_name,
        jwks_url=test_jwks_url,
        cors_allow_origins="*",
        domain_name="example.com",
        acm_cert_arn="arn:aws:acm:us-west-2:01234567890:certificate/f278cd4d-e846-4063-bb00-bd15c382bb41",
    )
    template = assertions.Template.from_stack(stack)
