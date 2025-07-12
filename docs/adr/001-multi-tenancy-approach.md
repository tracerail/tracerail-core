# ADR 001: Multi-Tenancy Implementation Approach

**Status:** Proposed

**Date:** 2024-07-12

## Context

The TraceRail platform was initially developed as a single-tenant system to rapidly build and validate the core workflow and business logic. The current architecture has no concept of tenant isolation; all data, workflows, and API interactions exist in a single, shared space.

To evolve into a commercially viable SaaS product, the platform must support multiple, isolated tenants securely and scalably. A decision is required on the strategy and step-by-step plan to refactor the existing system for multi-tenancy. Key concerns include data isolation, workflow execution separation, API security, and the developer experience during and after the transition.

This ADR outlines a phased approach to introduce multi-tenancy across the entire platform stack.

## Decision

We will adopt a phased, full-stack approach to implement multi-tenancy. The chosen strategy prioritizes strong isolation using established patterns for each layer of the stack: API-level tenant context, Temporal Namespaces for workflow execution, and Row-Level Security (RLS) for data storage in PostgreSQL.

The implementation will be executed in the following four phases:

---

### Phase 1: Tenant-Aware API Boundary

The first step is to make tenancy an explicit, required concept at the system's entry point.

1.  **Tenant Identification:** Introduce a `tenant_id` as the primary key for a tenant, likely a `UUID`.
2.  **API Contract Redesign:** All tenant-specific API endpoints will be prefixed with a tenant identifier.
    *   **Current:** `/api/v1/cases/{caseId}`
    *   **New:** `/api/v1/tenants/{tenantId}/cases/{caseId}`
3.  **Authentication:**
    *   Implement a simple, server-side authentication mechanism (e.g., API keys).
    *   Each API key will be mapped to a `tenantId`.
    *   The `tracerail-task-bridge` will be responsible for authenticating incoming requests. Upon success, it will extract the `tenantId` and pass it down to the service layer. Unauthorized or non-tenant requests will be rejected.
4.  **Update Contracts:** Update the Pact consumer-driven contracts to reflect the new tenant-aware URL structure and authentication requirements. This will be the primary driver for changes in the API layer.

---

### Phase 2: Workflow and Execution Isolation

Next, we will ensure that each tenant's business processes are executed in complete isolation.

1.  **Temporal Namespaces:** We will leverage Temporal's Namespace feature as the primary isolation mechanism. Each tenant will be provisioned with their own Namespace. This provides strong guarantees of separation for workflows, task queues, schedules, and visibility records.
2.  **Dynamic Client Connection:** The `CaseService` in `tracerail-task-bridge` will be updated. Instead of using a single, global Temporal client, it will use a factory or manager to get a client configured for the specific `tenantId`'s namespace for each incoming request.
3.  **Tenant Context in Workflows:** The `tenantId` will be passed as a mandatory first-class argument to all workflow runs. This makes the workflow logic explicitly aware of its tenant context, which will be crucial for interacting with tenant-specific resources or configurations in the future.

---

### Phase 3: Data Isolation in PostgreSQL

This is the most critical phase for ensuring tenant data is never exposed to another tenant.

1.  **Add `tenant_id` Column:** A non-nullable `tenant_id` column will be added to every database table that contains tenant-specific data (e.g., `cases`, `activity_stream_items`).
2.  **Adopt Row-Level Security (RLS):** We will use PostgreSQL's built-in RLS feature.
    *   For each protected table, an RLS policy will be created that permits `SELECT`, `INSERT`, `UPDATE`, and `DELETE` operations only if the row's `tenant_id` column matches the current tenant identifier set in the session.
3.  **Set Session Context:** The application's data access layer will be responsible for setting the tenant context for every database transaction using `SET app.current_tenant_id = '<tenantId>'`. This setting is session-local and secure. The RLS policies will use this setting to enforce data access rules automatically at the database level.
4.  **Database Migrations:** A comprehensive migration script will be written to:
    *   Alter existing tables to add the `tenant_id` column.
    *   Enable RLS on those tables.
    *   Define and apply the security policies.

---

### Phase 4: Frontend Integration

Finally, we will update the `tracerail-action-center` to be fully tenant-aware.

1.  **Authentication Flow:** Implement a simple login screen or mechanism for users to provide credentials (or an API key for now) to authenticate with the backend.
2.  **Client-Side Tenant Context:** Upon successful authentication, the frontend will securely store the auth token and `tenantId`.
3.  **API Client Refactoring:** The frontend's API client will be updated to:
    *   Include the authentication token in the `Authorization` header of every request.
    *   Construct API call URLs using the stored `tenantId` to match the new API contract (e.g., `/api/v1/tenants/{tenantId}/...`).

## Consequences

*   **Positive:**
    *   This approach provides a very high degree of security and data isolation.
    *   By starting at the API boundary and moving down the stack, we ensure that changes are driven by a clear, top-down contract.
    *   Future feature development will naturally and correctly be built within this tenant-aware framework, significantly reducing future refactoring.
    *   The platform will be architecturally ready to support a SaaS business model.

*   **Negative:**
    *   This is a significant, invasive refactoring effort that will touch every component of the system. It will temporarily slow down user-facing feature development.
    *   It introduces new operational complexity, such as provisioning and managing Temporal Namespaces for new tenants.
    *   The initial implementation of authentication and RLS policies must be done carefully to avoid security loopholes.

## Rejected Options

*   **Separate Database per Tenant:** Considered too costly and complex to manage at scale. It complicates deployments, migrations, and maintenance.
*   **Application-Level Data Scoping (No RLS):** Relying solely on the application code (`WHERE tenant_id = ?`) to filter data was rejected as too brittle and error-prone. A single missing `WHERE` clause could lead to a catastrophic data leak. RLS provides a much stronger safety net at the database level.
