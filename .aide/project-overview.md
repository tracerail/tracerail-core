# Project Overview

This document provides a high-level overview of each repository within the Tracerail platform.

## Repositories

### 1. `tracerail-core`
-   **Purpose:** The central, foundational library for the entire platform. It contains the core business logic, domain models (e.g., the `Case` Pydantic models), and workflow definitions (e.g., the `FlexibleCaseWorkflow`). It is also the home for cross-cutting project documentation like Architecture Decision Records (ADRs).
-   **Technology:** Python, Poetry, Temporalio SDK.
-   **Key Consumers:** This library is imported as a dependency by other backend services, primarily `tracerail-task-bridge`.

### 2. `tracerail-task-bridge`
-   **Purpose:** A backend API service that acts as the "provider" in our system. It exposes a FastAPI-based HTTP API that other services can call. Its primary job is to translate these API requests into commands, queries, or signals for our Temporal workflows.
-   **Technology:** Python, FastAPI, Poetry, Temporalio SDK.
-   **Key Dependencies:** `tracerail-core`.

### 3. `tracerail-action-center`
-   **Purpose:** The primary frontend user interface for the "Agent" persona. This is a sophisticated, three-pane case management application where Agents view their work queues and act on individual Cases.
-   **Technology:** JavaScript, React, Create React App.
-   **Key Relationship:** This is the primary "consumer" of the `tracerail-task-bridge` API.

### 4. `tracerail-processes` (Future)
-   **Purpose:** A dedicated repository to hold the version-controlled definitions of our business processes (e.g., `expense_approval.yaml`).
-   **Technology:** YAML/JSON, Git.
-   **Key Relationship:** This repository will have its own CI/CD pipeline to validate and publish process definitions as versioned artifacts. The `FlexibleCaseWorkflow` will fetch these artifacts at runtime.

### 5. `tracerail-dashboard-ui` (Future)
-   **Purpose:** A dedicated frontend user interface for the "Manager" persona. It will focus on analytics, reporting, and high-level dashboards.
-   **Technology:** JavaScript, React (or another suitable framework).
-   **Key Relationship:** This will be another consumer of our backend APIs, likely querying a dedicated analytics database.