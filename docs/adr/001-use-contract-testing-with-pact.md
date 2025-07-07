# ADR-001: Use Consumer-Driven Contract Testing with Pact

*   **Status:** Accepted
*   **Date:** 2024-08-22

## Context

The Tracerail platform is composed of multiple independent services, including a frontend (`tracerail-action-center`) and a backend API (`tracerail-task-bridge`). These services must communicate reliably over an HTTP API. A primary risk in this architecture is the potential for integration bugs, where the frontend's expectations of the API (the "consumer") diverge from the backend's actual implementation (the "provider").

Traditional end-to-end integration tests can mitigate this risk, but they are often slow, brittle, and require a fully deployed, integrated environment. This creates a bottleneck and hinders the ability of the frontend and backend teams to develop, test, and deploy their services independently.

We needed a testing strategy that could guarantee API compatibility without the overhead and coupling of full end-to-end tests.

## Decision

We will adopt **Consumer-Driven Contract Testing** as our primary method for ensuring API compatibility between our services. The chosen framework for implementing this is **Pact**.

The workflow is as follows:
1.  **Consumer-Side Test:** The consumer (e.g., `tracerail-action-center`) will write tests that define its expectations of the provider's API. These tests will use the Pact library to generate a contract file (`pact.json`). This contract precisely documents the required requests and the expected responses.
2.  **Contract Sharing:** Initially, this contract file will be committed to the consumer's source control repository and made available to the provider team. (This process will later be automated by a Pact Broker as part of our CI/CD strategy).
3.  **Provider-Side Verification:** The provider (e.g., `tracerail-task-bridge`) will use the contract file in its own test suite. The Pact library will replay the requests from the contract against a live instance of the provider and verify that its responses adhere to all the rules defined in the contract.

This process ensures that any change made by the provider that would break the consumer's expectations will cause a test to fail, preventing the change from being deployed.

## Consequences

### Positive

*   **Guaranteed API Compatibility:** We can be certain that the frontend and backend will work together for the tested interactions. This eliminates a major class of bugs.
*   **Enables Independent Development & Deployment:** Frontend and backend teams can work independently. The contract serves as the single source of truth, removing the need for a shared, integrated test environment for most development.
*   **Fast and Reliable Feedback:** Contract tests are fast to run and can be executed locally by developers and in CI pipelines, providing immediate feedback.
*   **Living Documentation:** The pact file acts as precise, executable documentation of how the API is actually being used by its consumers.

### Negative

*   **Increased Upfront Effort:** This introduces a new testing methodology and library that the team must learn and configure.
*   **Workflow Overhead:** The process of sharing and verifying contracts adds a new step to the development workflow.
*   **Not a Replacement for All Testing:** Contract testing validates the format and structure of API requests and responses, but it does not validate the provider's business logic in depth. It complements, but does not replace, unit tests and targeted end-to-end tests.