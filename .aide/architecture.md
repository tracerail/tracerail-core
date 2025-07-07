# Architecture Principles

This document summarizes the key architectural decisions that have been made for the Tracerail platform. For a detailed explanation of the context and consequences of each decision, please refer to the full Architecture Decision Records (ADRs) located in the `../docs/adr` directory.

## 1. Core Platform Structure

*   **Decision:** The platform is built using a **Multi-Repo Structure**. Each service (frontend, backend, core library) lives in its own dedicated Git repository.
*   **Rationale:** This enables clear ownership boundaries, independent deployment pipelines, and focused codebases.
*   **Reference:** [ADR-003: Use a Multi-Repo Structure for Platform Services](./../docs/adr/003-use-multi-repo-structure.md)

## 2. Business Logic and Workflows

*   **Decision:** We use a **Generic Workflow Engine** (`FlexibleCaseWorkflow`) that executes business processes based on **Process Definitions stored as code**.
*   **Rationale:** This makes our business logic highly dynamic and flexible. New processes can be defined, versioned, tested, and deployed as version-controlled artifacts (e.g., YAML files) without changing the core application code.
*   **Reference:** [ADR-007: Store Process Definitions as Version-Controlled Code Artifacts](./../docs/adr/007-store-process-definitions-as-code.md)

## 3. Data and State Management

*   **Decision:** For any **active Case**, the **Temporal Workflow Execution is the System of Record**, not a traditional database.
*   **Rationale:** This eliminates data synchronization problems between a workflow engine and a separate database, ensuring the state is always consistent.
*   **Reference:** [ADR-002: Use Temporal as System of Record for Live Cases](./../docs/adr/002-use-temporal-as-sot-for-live-cases.md)

## 4. Reporting and Analytics

*   **Decision:** We use a **hybrid data source strategy** for different reporting needs.
*   **Rationale:**
    *   **Live operational dashboards** (for Agents) will query the **Temporal Visibility Store** for real-time data on active workflows.
    *   **Historical analytical dashboards** (for Managers) will query a **dedicated external analytics database**, which will be populated by data from both the Visibility store and the Archival store.
*   **Reference:** [ADR-006: Define Data Sources for Different Reporting Needs](./../docs/adr/006-define-data-sources-for-reporting-needs.md)

## 5. User Interface Architecture

*   **Decision:** We build **separate, dedicated UIs for different user personas**.
*   **Rationale:** This allows us to create highly-optimized user experiences for each role. The `tracerail-action-center` is a "cockpit" for Agents, while a future `tracerail-dashboard-ui` will be an analytics platform for Managers.
*   **Reference:** [ADR-005: Use Separate UIs for Different User Personas](./../docs/adr/005-use-separate-uis-for-personas.md)

*   **Decision:** The primary UI for Agents is a **Case-Centric, three-pane layout**.
*   **Rationale:** This professional layout provides at-a-glance context (Details Panel), a full history (Activity Stream), and a clear task queue (Case List), which is far more efficient than a simple chat interface.
*   **Reference:** [ADR-004: Adopt a Case-Centric User Experience Model](./../docs/adr/004-adopt-case-centric-ux-model.md)

## 6. Service Integration and Testing

*   **Decision:** We use **Consumer-Driven Contract Testing with Pact** to ensure API compatibility.
*   **Rationale:** This allows us to guarantee that the frontend and backend will work together correctly without relying on slow and brittle end-to-end integration tests, enabling independent deployment.
*   **Reference:** [ADR-001: Use Consumer-Driven Contract Testing with Pact](./../docs/adr/001-use-contract-testing-with-pact.md)