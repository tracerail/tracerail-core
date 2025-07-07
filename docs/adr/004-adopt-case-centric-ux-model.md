# ADR-004: Adopt a Case-Centric User Experience Model

*   **Status:** Accepted
*   **Date:** 2024-08-22

## Context

The initial design for the `tracerail-action-center` was based on a literal interpretation of the "conversation" metaphor. This resulted in a UI that resembled a standard chat application (e.g., Slack or Teams), with a list of conversations on the left and the selected conversation's message history on the right.

During early development, we identified a critical flaw in this model. For an Agent to resolve a case effectively, they need immediate, persistent access to the case's core metadata (its status, assignee, creation date, and key data points like an order ID or customer name). In the chat-based model, this critical information was either buried in the activity stream or not visible at all, forcing the Agent to scroll and search for context, which is highly inefficient. The model was not optimized for professional, high-volume case resolution.

## Decision

We have decided to pivot from a "conversation-first" model to a **"Case-Centric" user experience**.

The primary interface for viewing and acting on a single Case will be a **three-pane layout**:

1.  **Left Pane (`CaseList`):** A list of Cases assigned to the Agent. This provides the queue of work.
2.  **Center Pane (`ActivityStream`):** The chronological log of all events, messages, and interaction prompts related to the selected Case. This shows the history of the Case.
3.  **Right Pane (`CaseDetailsPanel`):** A new, dedicated panel that continuously displays the core, structured metadata of the selected Case. This provides at-a-glance context.

This decision elevates the **Case** as the central entity in the UI. The "conversation" is now more accurately represented as the **Activity Stream** *within* the context of a larger Case.

## Consequences

### Positive

*   **Dramatically Improved Agent Efficiency:** The persistent visibility of the `CaseDetailsPanel` means Agents have immediate access to the context they need to make decisions, without having to hunt for information in a linear message log.
*   **Clear Information Hierarchy:** The three-pane layout provides a logical and intuitive separation between the agent's queue (`CaseList`), the history of a specific task (`ActivityStream`), and the static, factual data about that task (`CaseDetailsPanel`).
*   **Aligns with Professional Tooling:** This layout is a standard and proven pattern in industry-grade case management, CRM, and support software, making it immediately familiar to experienced agents.
*   **Scalable Design:** The dedicated details panel can easily accommodate a growing number of custom fields and metadata as the complexity of our workflows increases over time.

### Negative

*   **Increased UI Complexity:** A three-pane layout is more complex to implement and manage from a state and component perspective than a simple two-pane layout.
*   **Backend API Requirement:** This design requires the backend API to provide a well-structured `caseDetails` object in addition to the list of activity stream events. This decision was a primary driver for the structure of our Pact contract.
*   **Potential for Information Overload:** The design of the `CaseDetailsPanel` must be carefully considered to avoid cluttering it with too much information, which could overwhelm the Agent.
