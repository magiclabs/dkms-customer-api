from aws_cdk import (
    CfnOutput,
    Duration,
    RemovalPolicy,
    Stack,
    aws_lambda as lambda_,
    aws_kms as kms,
    aws_certificatemanager as acm,
)
from constructs import Construct

from aws_cdk.aws_lambda_python_alpha import PythonFunction
import aws_cdk.aws_apigatewayv2_alpha as apigwv2
from aws_cdk.aws_apigatewayv2_integrations_alpha import (
    HttpLambdaIntegration,
)


class DKMSCustomerAPIStack(Stack):
    """Deploy a stack containing an API endpoint for DKMS."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_name: str,
        jwks_url: str,
        cors_allow_origins: str,
        domain_name: str = None,
        acm_cert_arn: str = None,
        **kwargs,
    ) -> None:
        """Initialize the stack."""
        super().__init__(scope, construct_id, **kwargs)
        self.env_name = env_name
        self.jwks_url = jwks_url
        self.domain_name = domain_name
        self.acm_cert_arn = acm_cert_arn
        self.cors_allow_origins = cors_allow_origins

        # Create a KMS key
        self.kms_key = self.deploy_kms_key()

        # Create the lambda function that will handle API requests
        self.dkms_lambda = self.deploy_dkms_lambda()

        # Grant the lambda permission to use the kms key
        self.kms_key.grant_encrypt_decrypt(self.dkms_lambda)

        # Create an API Gateway V2 API
        self.dkms_api = self.deploy_dkms_api()

        # Output the API URL
        CfnOutput(
            self,
            id="dkms-customer-api-url",
            value=self.dkms_api.url,
            description="DKMS Customer API URL",
        )

    def deploy_kms_key(self) -> kms.Key:
        """Create a KMS key for encrypting and decrypting customer data."""
        return kms.Key(
            self,
            id="dkms-customer-key",
            alias=f"dkms-customer-key-{self.env_name}",
            description="Key for encrypting and decrypting customer data",
            removal_policy=RemovalPolicy.RETAIN,
        )

    def deploy_dkms_lambda(self) -> lambda_.Function:
        """Create a lambda function to handle API requests."""
        return PythonFunction(
            self,
            id=f"magic-dkms-customer-endpoint-{self.env_name}",
            function_name=f"magic-dkms-customer-endpoint-{self.env_name}",
            entry="lambdas/dkms_handler",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler",
            timeout=Duration.seconds(30),
            memory_size=128,
            environment={
                "DKMS_KMS_KEY_ID": self.kms_key.key_id,
                "JWKS_URL": self.jwks_url,
            },
        )

    def deploy_dkms_api(self) -> apigwv2.HttpApi:
        """Create an API Gateway V2 API for the DKMS customer endpoint."""
        default_domain_mapping = None
        if self.domain_name is not None:
            dn = apigwv2.DomainName(
                self,
                "dkms-customer-api-domain",
                domain_name=self.domain_name,
                certificate=acm.Certificate.from_certificate_arn(
                    self, "dkms-acm-cert", self.acm_cert_arn
                ),
            )
            default_domain_mapping = apigwv2.DomainMappingOptions(
                domain_name=dn,
            )

        dkms_default_integration = HttpLambdaIntegration(
            "magic-dkms-customer-endpoint-lambda",
            handler=self.dkms_lambda,
        )
        dkms_api = apigwv2.HttpApi(
            self,
            "dkms-customer-api",
            api_name=f"dkms-customer-api-{self.env_name}",
            default_domain_mapping=default_domain_mapping,
            cors_preflight=apigwv2.CorsPreflightOptions(
                allow_headers=["Authorization"],
                allow_methods=[
                    apigwv2.CorsHttpMethod.GET,
                    apigwv2.CorsHttpMethod.HEAD,
                    apigwv2.CorsHttpMethod.OPTIONS,
                    apigwv2.CorsHttpMethod.POST,
                ],
                allow_origins=[self.cors_allow_origins],
                max_age=Duration.days(10),
            ),
        )
        dkms_api.add_routes(
            path="/healthz",
            methods=[apigwv2.HttpMethod.GET],
            integration=dkms_default_integration,
        )
        dkms_api.add_routes(
            path="/encrypt",
            methods=[apigwv2.HttpMethod.POST],
            integration=dkms_default_integration,
        )
        dkms_api.add_routes(
            path="/decrypt",
            methods=[apigwv2.HttpMethod.POST],
            integration=dkms_default_integration,
        )
        return dkms_api
