---
layout: post
title: "Service Principal Connector Template"
date: 2026-05-20 10:00:00 -0000
categories: [Power Platform, Custom Connectors]
tags: [Azure AD, Service Principal, OAuth2, API Development]
---

## Overview

The Service Principal Connector Template is a ready-to-use solution for authenticating to any API secured with Azure Active Directory (Azure AD) using the OAuth 2.0 client credentials flow. This template is not limited to Microsoft Graph—it works with any API registered in Azure AD that supports service principal authentication.

### Key Features
- **OAuth 2.0 Client Credentials Flow**: Obtain tokens for service principal authentication.
- **Customizable**: Update the OAuth2 resource/scope and endpoints for your target API.
- **Secure**: Follow best practices for managing secrets and authentication.

## How to Use

1. **Register Your API in Azure AD**:
   - Register your API as an "App registration" in Azure AD.
   - Create a second app registration for the connector (client) and grant it permissions to the API.
   - For detailed steps, see [Create a custom connector for a web API](https://learn.microsoft.com/connectors/custom-connectors/create-web-api-connector#set-up-microsoft-entra-id-authentication).

2. **Update the Connector's OAuth2 Settings**:
   - Set the resource URL or scope to your API's App ID URI (e.g., `api://{your-api-client-id}/.default`).
   - For Microsoft Graph, use `https://graph.microsoft.com/.default`.

3. **Customize the OpenAPI Definition and Script**:
   - Modify `apiDefinition.swagger.json` to define your API endpoints.
   - Update `script.csx` for request/response transformations.

## Detailed Setup Instructions

### Registering Your API in Azure AD
1. Navigate to the Azure portal and go to **Azure Active Directory** → **App registrations**.
2. Register your API as an "App registration" and note the **Application (client) ID**.
3. Create a second app registration for the connector (client) and grant it permissions to the API.
4. Use the following PowerShell command to create a service principal:

```powershell
Connect-AzureAD -TenantId <your-tenant-id>
New-AzureADServicePrincipal -AppId <your-app-id>
```

For detailed steps, see [Create a custom connector for a web API](https://learn.microsoft.com/connectors/custom-connectors/create-web-api-connector#set-up-microsoft-entra-id-authentication).

### Configuring OAuth 2.0 in the Connector
- Use the client credentials (service principal) flow.
- Set the resource URL or scope to your API's App ID URI (e.g., `api://{your-api-client-id}/.default`).
- For Microsoft Graph, use `https://graph.microsoft.com/.default`.

### Using Azure Key Vault for Secrets Management
- Store client secrets securely in Azure Key Vault:

```powershell
$secretValue = ConvertTo-SecureString -String '<client-secret>' -AsPlainText -Force
Set-AzKeyVaultSecret -VaultName <vault-name> -Name <secret-name> -SecretValue $secretValue
```

- Rotate secrets regularly using Azure Key Vault's rotation policies:

```powershell
Set-AzKeyVaultKeyRotationPolicy -VaultName <vault-name> -KeyName <key-name> -ExpiresIn (New-TimeSpan -Days 720) -KeyRotationLifetimeAction @{Action="Rotate";TimeAfterCreate= (New-TimeSpan -Days 540)}
```

For more details, see [Azure Key Vault secret rotation](https://learn.microsoft.com/azure/key-vault/secrets/tutorial-rotation-dual).

### Testing the Connector
- Use Postman or a similar tool to test the OAuth 2.0 flow and API endpoints.
- Verify that tokens are issued and API calls succeed with the service principal credentials.

## Example Code Snippets

### Creating a Service Principal with Azure CLI
```azurecli
az ad sp create-for-rbac -n "my-service-principal" --role Contributor --scopes /subscriptions/{SubID}
```

### Authenticating a CosmosClient with Service Principal in Node.js
```javascript
const { CosmosClient } = require("@azure/cosmos");
const { ClientSecretCredential } = require("@azure/identity");

const credential = new ClientSecretCredential(
    process.env.AZURE_TENANT_ID,
    process.env.AZURE_CLIENT_ID,
    process.env.AZURE_CLIENT_SECRET
);

const client = new CosmosClient({
    endpoint: process.env.COSMOS_ENDPOINT,
    aadCredentials: credential
});
```

For more examples, see [Azure Service Principal Documentation](https://learn.microsoft.com/azure/active-directory/develop/).

## Files in the Template

- `apiDefinition.swagger.json`: OpenAPI definition for your connector.
- `apiProperties.json`: Connector properties and OAuth configuration.
- `script.csx`: C# script for handling request/response transformations.

## Additional Guidance

### Security Best Practices
- Store secrets in Azure Key Vault when possible.
- Rotate client secrets regularly and update the connector before expiration.
- Use managed identity for Azure-hosted connectors to avoid client secrets.

### Adaptation Notes
- This template is not limited to Microsoft Graph. For other APIs, use their App ID URI or scope.
- Ensure your API supports service principal authentication.

## Resources

- [Service Principal Connector Template on GitHub](https://github.com/troystaylor/SharingIsCaring/tree/main/Service%20Principal%20Connector%20Template)
- [Authenticate your API and connector with Microsoft Entra ID](https://learn.microsoft.com/connectors/custom-connectors/azure-active-directory-authentication)
- [Manage authentication within Service Connector](https://learn.microsoft.com/azure/service-connector/how-to-manage-authentication)

This template simplifies the process of creating secure, scalable connectors for APIs secured with Azure AD. Start building your custom connector today!

## Connecting to APIs via Azure API Management (APIM)

Azure API Management (APIM) acts as a gateway for your APIs, providing centralized management, security, and monitoring. You can use the Service Principal Connector Template to connect to APIs through APIM, including third-party services like Salesforce.

### Setting Up APIM
1. **Import Your API**:
   - In the Azure portal, navigate to your APIM instance.
   - Import your API definition (e.g., OpenAPI/Swagger) into APIM.

2. **Configure Policies**:
   - Add policies to handle authentication, rate limiting, and other requirements.
   - Example: Validate Azure AD tokens:
     ```xml
     <validate-jwt header-name="Authorization" failed-validation-httpcode="401" failed-validation-error-message="Unauthorized">
       <openid-config url="https://login.microsoftonline.com/{tenant-id}/v2.0/.well-known/openid-configuration" />
       <required-claims>
         <claim name="aud">
           <value>api://{your-api-client-id}</value>
         </claim>
       </required-claims>
     </validate-jwt>
     ```

3. **Test the API**:
   - Use tools like Postman to test the API through APIM.
   - Verify that APIM forwards requests to the backend API.

## Connecting to Salesforce via APIM

You can use APIM as a gateway to connect to Salesforce APIs. This approach centralizes management and enhances security.

### Steps to Integrate Salesforce via APIM

1. **Create an External Client App in Salesforce**:
   - Go to **Setup** → **App Manager** → **New External Client App**.
   - Enable OAuth settings and specify the required scopes (e.g., `api`, `refresh_token`).
   - Note the client ID and client secret.

2. **Import Salesforce API into APIM**:
   - Use Salesforce's OpenAPI definition or manually define the endpoints in APIM.
   - Example endpoint: `/services/data/v52.0/sobjects/Account`.

3. **Add Authentication Policies in APIM**:
   - Add a policy to include the Salesforce token in the `Authorization` header:
     ```xml
     <set-header name="Authorization" exists-action="override">
       <value>Bearer @{context.Variables["salesforceToken"]}</value>
     </set-header>
     ```

4. **Update the Connector**:
   - Set the OAuth2 resource/scope in the connector to Salesforce's token URL: `https://login.salesforce.com/services/oauth2/token`.
   - Use the client credentials flow to obtain tokens.

5. **Test the Integration**:
   - Use the connector to call Salesforce APIs through APIM.
   - Verify that APIM forwards the requests to Salesforce with the correct token.

### Note on External Client Apps
Salesforce's External Client Apps replace Connected Apps for enhanced security and better integration capabilities. Ensure you configure the app with the correct permissions and scopes for your use case.

### Benefits of Using APIM with Salesforce
- **Centralized Management**: Manage all APIs, including Salesforce, from a single platform.
- **Enhanced Security**: Enforce additional security policies, such as IP whitelisting and rate limiting.
- **Monitoring and Analytics**: Gain insights into API usage and performance.

For more details, see [Azure API Management Documentation](https://learn.microsoft.com/azure/api-management/).