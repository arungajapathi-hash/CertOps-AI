SYNTHETIC DATA — For demonstration purposes only

# AZ-204: Developing Solutions for Microsoft Azure

## Develop Azure compute solutions

Overview
Azure compute services are the foundation for cloud applications. In AZ-204, candidates must understand how to build and deploy serverless and container-based applications using Azure Functions, App Service, and Kubernetes. The ability to choose the right compute pattern for a given scenario is critical to designing reliable solutions.

Key concepts
- Azure Functions triggers and bindings
- App Service deployment models and scaling
- Containers and Azure Kubernetes Service (AKS)
- Durable Functions for long-running tasks
- Function security and authentication

Exam tips
- Know the difference between consumption and premium plans.
- Understand when to use functions versus App Service.
- Practice writing function bindings for storage and HTTP triggers.

## Develop for Azure storage

Overview
Storage is used to persist data, support messaging workflows, and host static content. AZ-204 emphasizes working with Blob, Queue, Table, and Cosmos DB for scalable storage operations. Candidates should be able to integrate storage into compute solutions and choose the correct service for performance and cost.

Key concepts
- Blob storage tiers and access patterns
- Table storage and Cosmos DB key/value models
- Queue storage for background processing
- File storage and mounting options
- Data retention and lifecycle management

Exam tips
- Review storage authentication options and connection strings.
- Know how to use Azure Storage SDKs in .NET and Python.
- Recognize when to choose Blob storage versus Cosmos DB.

## Implement Azure security

Overview
Security is a major part of AZ-204. Developers need to protect data, secure identities, and manage access to resources. This includes using Managed Identities, role-based access control, and encrypting sensitive payloads across transport and storage layers.

Key concepts
- Managed identities for Azure resources
- RBAC roles and least privilege access
- Key Vault secrets and certificate management
- OAuth flows with Azure AD
- Secure API authentication patterns

Exam tips
- Memorize the steps to secure a function app with managed identity.
- Understand how to protect a REST API with Azure AD.
- Review Key Vault integration for secrets and certificates.

## Monitor, troubleshoot and optimize

Overview
Monitoring and diagnostics give developers visibility into production behavior. AZ-204 covers Application Insights, logging patterns, alerting, and performance tuning. You should know how to instrument applications and analyze telemetry to resolve issues quickly.

Key concepts
- Application Insights telemetry and query tools
- Azure Monitor alerts and dashboards
- Distributed tracing for microservices
- Log retention and Live Metrics
- Performance tuning and cost optimization

Exam tips
- Know the difference between metrics and logs.
- Practice writing Kusto queries for common diagnostics.
- Understand how to configure alert rules and action groups.

## Connect to and consume Azure services

Overview
Integration with Azure services is a consistent theme in AZ-204. Developers must connect applications to APIs, event hubs, service bus, and external systems. This includes designing secure API contracts and managing service endpoints.

Key concepts
- API Management and API connectors
- Event Grid, Event Hubs, and Service Bus patterns
- HTTP APIs and RESTful service design
- Service endpoints and service principals
- Cross-service authentication and authorization

Exam tips
- Make sure you can explain event-driven versus request/response designs.
- Practice configuring Service Bus topics and subscriptions.
- Learn the common use cases for API Management.
