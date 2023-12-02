# DKMS Customer API
Magic offers a Wallet-as-a-Service solution, enabling web or mobile application developers to seamlessly integrate web3 wallets into their apps with a familiar web2 user experience. This is achieved through a variety of passwordless authentication mechanisms. The cornerstone of Magic’s offering is the patented Delegated Key Management Infrastructure (DKMS), detailed further [here](https://magic.link/docs/home/security/product-security#hardware-security-modules-hs-ms).

This repository introduces a novel shared security model for application developers seeking greater control over how Magic manages user private keys at runtime. Specifically, Magic introduces a shared security model where customers can deploy a cloud-native, elastic infrastructure to encrypt segments of the private key, divided using the Shamir Secret Sharing Algorithm. This infrastructure seamlessly integrates with Magic’s flagship DKMS, fortifying the entire offering. We refer to this enhanced architecture as Split-Key DKMS.

Below is a conceptual diagram illustrating how this model operates. For more in-depth information on the Split-Key DKMS offering, refer to **this link**.

<img width="953" alt="architecture" src="https://github.com/magiclabs/dkms-customer-api/assets/78329433/1c320985-13d7-41d5-be13-78c83484274c">

# **Getting Started**

Below outlines the expected workflow for developers participating in the Split-Key DKMS offering:

1. Opt-in for Split-Key DKMS when opening your developer account with Magic. Note that, currently, this feature is in invite-only mode; therefore, please contact customer service to enable this functionality.
2. Fork this repository, make necessary modifications, and deploy it to your AWS account. The tech stack is optimized for AWS Serverless Architecture, ensuring easy scalability.
3. Register the endpoints with Magic to receive callbacks for encryption and decryption at runtime when users sign up and perform transactions.

## **Requirements**

- Sign up for a cloud vendor; currently, we support Amazon Web Services (AWS).

## **License**

- We have open-sourced this repository under the Apache 2.0 license, making it suitable for modification to fit the unique requirements of your production environment. View the license [here](https://github.com/magiclabs/dkms-customer-api/blob/master/LICENSE).

## **Maintenance and Support for Versions**

- Currently we support AWS as the default cloud providers, we are looking to integrate this offering with other cloud providers such as Google Cloud and Microsoft Azure

## **Installation**

We use AWS CDK for this repository. The following commands will help you deploy the CDK to your AWS account.

```jsx
make install
make synth
make diff
make deploy
```

## **Configuration**

- The reference implementation of the CDK comes with a bring-your-own KMS model for encrypting and decrypting your share of the key.
- You are welcome to customize the configuration further to suit your needs, such as using an external HSM in place of AWS KMS.

# **Getting Help**

- Reach out to Magic customer support for assistance.

# **More Resources**

## **Documentation**

- [AWS CDK API v2 Documentation](https://docs.aws.amazon.com/cdk/api/v2/)
