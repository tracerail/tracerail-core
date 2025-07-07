# ADR-007: Store Process Definitions as Version-Controlled Code Artifacts

*   **Status:** Accepted
*   **Date:** 2024-08-22

## Context

Our platform's core architecture is based on a generic workflow engine (`GenericCaseWorkflow`) that executes business processes based on a given definition. This allows for dynamic and multi-tenant workflows. A critical decision is where and how to store these process definitions.

An initial proposal was to store them as JSON documents in a database. However, this approach presents significant challenges for a modern CI/CD environment:
*   **Lack of Version Control:** Storing behavior in a database makes it difficult to track changes, review updates, or revert to a previous version of a process.
*   **Difficult Environment Promotion:** Moving a new or updated process definition from a staging environment to a production environment would require a manual, error-prone database migration script rather than a standard, automated deployment process.
*   **Poor Testability:** It is difficult to write automated, repeatable tests against business logic that exists only as a row in a database table.

We needed a solution that treats our business processes as first-class, testable, and deployable code artifacts.

## Decision

We will adopt a **"Process Definitions as Code"** strategy.

1.  **Storage:** All process definitions will be created as structured text files (e.g., YAML for human readability). These files will be stored in a dedicated Git repository (e.g., `tracerail-processes`). This repository becomes the single source of truth for all business process logic.

2.  **CI/CD Pipeline:** The `tracerail-processes` repository will have its own dedicated CI/CD pipeline. When a change is committed, this pipeline will be responsible for:
    *   **Linting and Schema Validation:** Ensuring the definition file is well-formed.
    *   **Automated Testing:** Running tests to validate the logic of the process (e.g., checking for valid state transitions).
    *   **Publishing as a Versioned Artifact:** On a successful build of the main branch, the pipeline will "deploy" the process definition by publishing it as a versioned artifact (e.g., `expense_approval_v1.2.0.yaml`) to a dedicated artifact store (e.g., an S3 bucket).

3.  **Workflow Invocation:** The `GenericCaseWorkflow` will be initiated with a `process_name` and `process_version`. Its first step will be to call an Activity that fetches the specific, versioned process definition artifact from the artifact store.

## Consequences

### Positive

*   **Enables CI/CD for Business Logic:** This is the primary advantage. Changes to business processes can now be promoted through environments using a fully automated, safe, and repeatable pipeline, just like any other software component.
*   **Full Git-Based Version Control:** Every change to a process is a Git commit. This provides a full audit trail, the ability to use pull requests for peer review, and the safety of being able to easily revert to any previous version.
*   **High Testability:** Process definitions can be pulled directly from the Git repository into unit and integration tests, allowing us to validate our core business logic with high confidence before deployment.
*   **True Decoupling:** The `GenericCaseWorkflow` engine is completely decoupled from the specific business processes it runs. The engine can be updated and deployed independently, as long as it can still interpret the schema of the definition files.

### Negative

*   **Increased Infrastructure Overhead:** This approach requires us to manage an additional Git repository, a dedicated CI/CD pipeline for processes, and an artifact store (e.g., an S3 bucket).
*   **New "Deployment" Workflow:** The team must manage a new type of deployment—the deployment of business process artifacts. This adds a step to the overall release process.
*   **Potential for Delays:** A new version of a process is not "live" until its artifact has been successfully published by its pipeline. This introduces a short, but non-zero, delay compared to updating a database row.