"""
This module defines the core domain models for 'Cases'.

A Case represents a primary unit of work within the TraceRail system,
such as an expense report, a support ticket, or any other workflow instance
that requires tracking and potential human interaction.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


# --- Pydantic Models for the Case Domain ---
# These models define the canonical data structure for a Case and its components.
# They are used to ensure data consistency across different layers of the application.

class CaseParticipant(BaseModel):
    name: str
    email: Optional[str] = None


class CaseData(BaseModel):
    amount: float
    currency: str
    category: str
    ai_summary: str
    ai_policy_check: str
    ai_risk_score: str


class CaseDetails(BaseModel):
    caseId: str
    caseTitle: str
    status: str
    assignee: CaseParticipant
    submitter: CaseParticipant
    createdAt: datetime
    updatedAt: datetime
    caseData: CaseData


class ActivityStreamItem(BaseModel):
    id: int
    type: str
    sender: str
    text: str
    timestamp: datetime


class ActionButton(BaseModel):
    label: str
    value: str
    style: str


class InteractionPayload(BaseModel):
    actions: List[ActionButton]


class ActiveInteraction(BaseModel):
    interactionId: str
    interactionType: str
    prompt: str
    payload: InteractionPayload
    submitUrl: str


class Case(BaseModel):
    """
    The top-level model representing a complete Case.
    """
    caseDetails: CaseDetails
    activityStream: List[ActivityStreamItem]
    activeInteraction: Optional[ActiveInteraction]
