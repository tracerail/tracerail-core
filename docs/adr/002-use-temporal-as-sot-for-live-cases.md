# ADR-002: Use Temporal as System of Record for Live Cases

*   **Status:** Accepted
*   **Date:** 2024-08-22

## Context

A core architectural question for the Tracerail platform is where the "state" of a Case resides. A traditional application architecture would store all case data in a primary database (e.g., PostgreSQL, MongoDB), which the API layer would query directly.

However, our platform's business logic is executed as durable, long-running Temporal workflows. A Temporal workflow execution is inherently stateful and event-sourced, maintaining its own complete, consistent state in its event history.

Using a separate, primary database for case data would introduce a significant challenge: maintaining consistency between the state stored in the database and the actual state of the running workflow. This "dual-write" problem is a notorious source of complex bugs and data integrity issues. We need to select a single, authoritative System of Record (SoT) for the state of an active Case.

## Decision

We will adopt a **Workflow-as-SoT** architecture.

1.  **For a single, active Case, the live Temporal Workflow Execution is the System of Record.** To retrieve the complete, up-to-the-minute details of a specific Case, the API layer will query the live workflow directly using a Temporal Query.

2.  **For list views and dashboards, the Temporal Visibility Store is the System of Record.** To retrieve lists of cases (e.g., for the Action Center's case list), the API layer will query the Temporal service's Visibility API. It is the responsibility of each workflow to `upsert` its queryable metadata (e.g., status, assignee, title) to its Search Attributes as it executes.

3.  **For completed Cases, the Archival Store is the System of Record.** For long-term audit and deep analytics, we will rely on Temporal's Archival feature to persist the full event history of completed workflows to a dedicated blob store (e.g., S3).

This creates a CQRS (Command Query Responsibility Segregation)-like pattern where the path for reading a single record is different from the path for reading a list of records, with each path being optimized for its specific purpose.

## Consequences

### Positive

*   **Eliminates Data Consistency Bugs:** By treating the workflow itself as the source of truth, we completely avoid the "dual-write" problem and the risk of the application database becoming out of sync with the workflow's actual state.
*   **Leverages Temporal's Core Strengths:** This decision fully embraces the event-sourced and durable execution model that Temporal provides, using the platform as it was intended.
*   **Architectural Clarity:** It provides a clear and logical separation of concerns. The workflow contains the business logic, the Visibility store handles querying, and the Archival store handles long-term storage.
*   **High Freshness:** When an Agent views a case, they are guaranteed to see the absolute latest state directly from the live workflow, not a potentially stale replica.

### Negative

*   **New Developer Mental Model:** This is a departure from traditional database-centric architectures. Developers must learn and be comfortable with the pattern of querying a live workflow vs. a separate read store.
*   **Visibility Store Considerations:** While powerful, Temporal's Visibility store has its own query language and limitations. For extremely complex querying needs in the future, we may need to upgrade the Visibility store's backend (e.g., to Elasticsearch) or supplement it by streaming visibility data to an external analytics database.
*   **No Cross-Workflow Joins:** It is not possible to perform "joins" or queries that span across the state of multiple live workflows. Such requirements must be met by modeling data correctly in the Visibility store or an external analytics database.