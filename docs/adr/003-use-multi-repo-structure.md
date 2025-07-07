# ADR-003: Use a Multi-Repo Structure for Platform Services

*   **Status:** Accepted
*   **Date:** 2024-08-22

## Context

The Tracerail platform is being developed as a service-oriented system composed of several distinct, logical components. The primary components identified so far are: a frontend application (`tracerail-action-center`), a backend API service (`tracerail-task-bridge`), and a shared business logic library (`tracerail-core`).

We faced a foundational decision on how to structure our source code control:
1.  **Monorepo:** A single, large repository containing the code for all services.
2.  **Multi-repo (or Polyrepo):** Multiple, smaller repositories, with each repository dedicated to a single service or component.

The key driver for this decision is our desire to enable independent team workflows, establish clear ownership boundaries, and facilitate decoupled CI/CD pipelines in the future.

## Decision

We have decided to adopt a **multi-repo structure** for the Tracerail platform.

Each primary service or logical component will reside in its own dedicated Git repository. The initial set of repositories includes:
*   `tracerail-action-center`: The frontend user interface for Agents.
*   `tracerail-task-bridge`: The backend API service that bridges requests to our workflow engine.
*   `tracerail-core`: A shared Python library containing our core business domain models and logic.

Future components, such as the `tracerail-dashboard-ui`, will also be created in their own separate repositories. Dependencies between these repositories (e.g., the task bridge depending on the core library) will be explicitly managed via each project's dependency management configuration (e.g., `pyproject.toml`).

## Consequences

### Positive

*   **Clear Ownership and Autonomy:** Each repository has a clear purpose and can be owned by a specific team or individual, who can manage its development lifecycle independently.
*   **Decoupled CI/CD:** This structure is a prerequisite for building independent deployment pipelines. We can build, test, and deploy the frontend without triggering a backend deployment, and vice versa.
*   **Focused Codebases:** Developers can clone and work within a smaller, more focused repository. This leads to faster local Git operations, simpler IDE setups, and reduced cognitive overhead.
*   **Independent Versioning and Releasing:** Each service can be versioned, released, and rolled back independently of the others.

### Negative

*   **Dependency Management Complexity:** We must explicitly manage dependencies between our own repositories. This was demonstrated when we had to add `tracerail-core` as a local path dependency to `tracerail-task-bridge`. This adds a layer of configuration that would not be present in a monorepo.
*   **Code Discovery Challenges:** Understanding the full system requires navigating multiple repositories. Discovering shared code or tracing a feature end-to-end can be more difficult.
*   **Cross-Repository Changes:** Making a single logical change that spans multiple repositories (e.g., a breaking change in `tracerail-core` that requires updates in the `task-bridge`) is more complex. It requires coordinating pull requests across multiple repositories instead of a single atomic commit.
*   **Potential for Code Duplication:** Without careful management, common utility code or configurations might be duplicated across repositories.