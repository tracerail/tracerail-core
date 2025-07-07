# ADR-005: Use Separate UIs for Different User Personas

*   **Status:** Accepted
*   **Date:** 2024-08-22

## Context

The Tracerail platform serves at least two distinct primary user personas with very different goals and needs:

1.  **The Agent:** This user's primary goal is to process and resolve individual cases efficiently. They need a "cockpit" view optimized for high-volume task execution, with deep detail on specific cases. Their workflow is transactional.

2.  **The Manager:** This user's primary goal is to understand team performance, monitor workload, and analyze trends across many cases. They need a "dashboard" view optimized for high-level oversight and data aggregation. Their workflow is analytical.

We faced a choice: should we build a single, monolithic user interface that attempts to serve both personas, or should we build separate, dedicated applications for each?

A single UI would require complex conditional logic, cluttered navigation (e.g., switching between "inbox mode" and "dashboard mode"), and would likely result in a user experience that is a poor compromise for both personas.

## Decision

We have decided to build and maintain **separate, dedicated frontend applications for each primary user persona.**

The initial two applications defined by this decision are:
*   `tracerail-action-center`: A UI built specifically for the **Agent** persona, focused on the case management workflow.
*   `tracerail-dashboard-ui`: A future UI to be built specifically for the **Manager** persona, focused on analytics, reporting, and team performance metrics.

This aligns with our multi-repo strategy (ADR-003) and ensures that each application can be developed, deployed, and optimized independently for its target audience.

## Consequences

### Positive

*   **Highly-Optimized User Experiences:** Each UI can be tailored precisely to the unique workflow and needs of its target persona, leading to higher efficiency and user satisfaction.
*   **Simpler and More Focused Codebases:** Each frontend application will have a clearer purpose, a smaller feature set, and less conditional logic, making it easier to develop, test, and maintain.
*   **Independent Development and Deployment:** The team responsible for the Dashboard UI can iterate and deploy completely independently of the Action Center team, as they are separate applications (though they may share a common backend API).
*   **Clear Product Definition:** This creates a clear boundary between the operational "doing" part of the platform and the analytical "reviewing" part.

### Negative

*   **Increased Number of Frontend Projects:** This approach requires us to build, maintain, and deploy multiple frontend applications, which increases overhead compared to a single application.
*   **Risk of UI Inconsistency:** We must be deliberate in creating and maintaining a shared component library or design system to ensure a consistent visual identity and user experience across the different UIs.
*   **Seamless Navigation is Required:** Users who fulfill both roles (e.g., a team lead who is both a Manager and an Agent) will need to navigate between two separate applications. This reinforces the critical need for a smooth Single Sign-On (SSO) experience to make this transition transparent.