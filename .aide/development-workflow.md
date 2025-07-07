# Development Workflow Cheat Sheet

This document provides a quick reference for common commands used to run, test, and interact with the services in the Tracerail platform.

## `tracerail-action-center` (Frontend)

This is the main user interface for Agents.

-   **Start the development server:**
    ```bash
    npm start
    ```
    This will launch the React application, typically on `http://localhost:3002`.

-   **Generate the API contract:**
    ```bash
    npm run test:pact
    ```
    This runs the consumer-side Pact test, which generates the `pact.json` contract file that defines the frontend's expectations of the API.

## `tracerail-task-bridge` (Backend API)

This is the FastAPI service that acts as the provider for our frontend.

-   **Verify the API against the contract:**
    ```bash
    make test-pact
    ```
    This runs the provider-side Pact verification test. It will start a live instance of the API and check if its responses match the rules defined in the contract file. This is a full end-to-end integration test that requires a running Temporal server.

## `tracerail-core` (Core Logic & Workflows)

This library contains our core domain models and Temporal workflow definitions. It is not typically "run" on its own, but we have scripts to interact with its components during development.

**Prerequisite:** A Temporal development server must be running. You can start one with Docker:
```bash
docker run --rm -it -p 7233:7233 --name temporal-dev temporalio/auto-setup:latest
```

-   **Run the Temporal Worker:**
    This process hosts our workflow code and listens for tasks. It must be running in its own terminal.
    ```bash
    poetry run python -m tracerail.worker
    ```

-   **Start a new workflow instance:**
    This script creates a new "Case" by starting an instance of our `FlexibleCaseWorkflow`.
    ```bash
    poetry run python -m tracerail.start_workflow
    ```
