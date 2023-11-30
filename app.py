import aws_cdk as cdk
from deploy.dkms_api import DKMSCustomerAPIStack

app = cdk.App()

# Set environment. Defaults to "prod".
# example: "cdk synth --context env_name=dev"
env_name = app.node.try_get_context("env_name") or "prod"

# Set jwks url. Defaults to Magic production.
# example: "cdk synth --context jwks_url=https://assets.auth.magic.link/split-key/.well-known/jwks.json"
jwks_url = (
    app.node.try_get_context("jwks_url")
    or "https://assets.auth.magic.link/split-key/.well-known/jwks.json"
)

# Set optional domain name for the API
domain_name = app.node.try_get_context("domain_name")
acm_cert_arn = app.node.try_get_context("acm_cert_arn")
# If a domain name is provided, an ACM certificate must also be provided
if domain_name is not None:
    assert (
        acm_cert_arn is not None
    ), "If a domain name is provided, an ACM certificate must also be provided"

# Set cors allow_origins. Defaults to Magic production.
# example: "cdk synth --context cors_allow_origins='*'"
cors_allow_origins = (
    app.node.try_get_context("cors_allow_origins") or "https://auth.magic.link"
)


DKMSCustomerAPIStack(
    app,
    f"dkms-customer-api-{env_name}",
    env_name=env_name,
    jwks_url=jwks_url,
    cors_allow_origins=cors_allow_origins,
    domain_name=domain_name,
    acm_cert_arn=acm_cert_arn,
)
app.synth()
