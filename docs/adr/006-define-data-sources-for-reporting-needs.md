# ADR-006: Define Data Sources for Different Reporting Needs

*   **Status:** Accepted
*   **Date:** 2024-08-22

## Context

Our platform must provide data to two different types of UIs serving two different personas with distinct needs:

1.  **The Agent's Operational View (`tracerail-action-center`):** This UI requires a real-time view of a specific Agent's queue of *live* cases. The primary needs are filtering a list of active work items and seeing their current status and key metadata (e.g., SLA timers).

2.  **The Manager's Analytical Dashboard (`tracerail-dashboard-ui`):** This UI requires a high-level, aggregate view of performance across all cases, both *live and completed*. The primary needs are historical trend analysis, performance metrics (e.g., average time to resolution), and team workload reporting.

A single data source architecture is poorly suited to serve both needs. The Temporal Visibility store is excellent for querying live workflows but is not designed for complex, historical aggregation. Conversely, a traditional data warehouse is great for analytics but is not the real-time system of record for live case state. We needed to define a clear data sourcing strategy for each use case.

## Decision

We will adopt a hybrid, CQRS-style data architecture that uses the best data source for each specific query pattern.

1.  **Agent Operational Views will query the Temporal Visibility Store.**
    *   The backend API serving the `tracerail-action-center` will query Temporal's Visibility API directly to fetch lists of live cases for an agent.
    *   This ensures the data is real-time and perfectly consistent with the state of the active workflows.
    *   Workflows are responsible for `upsert`-ing their key metadata to their Search Attributes to make this possible.

2.  **Manager Analytical Dashboards will query a dedicated Analytics Database.**
    *   The backend API serving the `tracerail-dashboard-ui` will query a separate, external database (e.g., Snowflake, BigQuery, PostgreSQL) that is purpose-built for analytics.
    *   This Analytics Database will be populated via a data pipeline that consolidates information from two sources:
        *   The **Temporal Visibility Store** (for the latest status of live cases).
        *   The **Temporal Archival Store** (for the full, detailed event history of completed cases).
    *   This unified data store will allow for rich, historical, and aggregate queries that span both live and completed workflows.

## Consequences

### Positive

*   **Optimized Performance for Each Use Case:** Each query type is directed to a data store that is architecturally optimized to handle it. Live operational queries are fast and consistent; complex analytical queries do not impact the performance of the core operational system.
*   **Architectural Clarity:** This provides a clear blueprint for our data architecture. It defines where different types of data live and how they are accessed, which simplifies future development.
*   **Scalability:** The architecture scales gracefully. As the volume of historical data grows, our analytics database can be scaled independently without affecting the performance of the live Temporal cluster.
*   **Enables Rich Business Intelligence:** By consolidating all historical data into a queryable warehouse, we unlock the ability to perform complex business intelligence and trend analysis that would otherwise be impossible.

### Negative

*   **Increased System Complexity:** This is a more complex architecture than a single-database approach. It requires us to build and maintain a data pipeline (ETL/ELT process) to populate the analytics database.
*   **Data Latency in Analytics:** There will be an inherent latency between an event occurring in a workflow and that event being available for querying in the analytics database. This is acceptable for historical reporting but reinforces why it's not suitable for real-time operational views.
*   **Higher Infrastructure Cost and Overhead:** This architecture requires provisioning, managing, and paying for an additional data warehouse and the associated data pipeline infrastructure.
*   **Data Modeling Effort:** Significant effort will be required to design and maintain the data models and transformations (e.g., using a tool like dbt) within the analytics database.
