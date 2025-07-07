"""
TraceRail Task Management Data Models

This module defines the Pydantic models used throughout the task management
system. These models ensure data consistency, validation, and serialization
for tasks, comments, attachments, and other related entities.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

# --- Enumerations ---

class TaskStatus(str, Enum):
    """Enumeration of the possible statuses for a task."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    PENDING = "pending"  # Waiting for a dependency or external action

class TaskPriority(str, Enum):
    """Enumeration of the priority levels for a task."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


# --- Core Data Models ---

class TaskData(BaseModel):
    """
    Represents the data required to create a new task.
    This model is typically used as input to a `create_task` method.
    """
    title: str = Field(..., description="A concise title for the task.")
    description: Optional[str] = Field(None, description="A detailed description of the task.")
    priority: TaskPriority = Field(default=TaskPriority.NORMAL, description="The priority of the task.")
    assignee_id: Optional[str] = Field(None, description="The ID of the user or group assigned to the task.")
    due_date: Optional[datetime] = Field(None, description="The date and time when the task is due.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="A dictionary for storing custom data.")
    tags: List[str] = Field(default_factory=list, description="A list of tags for categorizing the task.")


class TaskResult(BaseModel):
    """
    Represents a task as it exists in the system, including all its data
    and system-managed fields.
    """
    task_id: str = Field(description="The unique identifier for the task.")
    status: TaskStatus = Field(default=TaskStatus.OPEN, description="The current status of the task.")
    data: TaskData = Field(description="The original data used to create the task.")
    created_at: datetime = Field(default_factory=datetime.now, description="The timestamp when the task was created.")
    updated_at: datetime = Field(default_factory=datetime.now, description="The timestamp of the last update.")
    completed_at: Optional[datetime] = Field(None, description="The timestamp when the task was completed.")
    history: List[Dict[str, Any]] = Field(default_factory=list, description="A log of changes made to the task.")

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the task result to a dictionary."""
        return self.model_dump(mode="json")


# --- Supporting Models ---

class TaskAttachment(BaseModel):
    """Represents a file or link attached to a task."""
    attachment_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique ID for the attachment.")
    task_id: str = Field(description="The ID of the task this attachment belongs to.")
    file_name: str = Field(description="The name of the attached file.")
    file_type: str = Field(description="The MIME type of the file.")
    file_url: Optional[str] = Field(None, description="A URL to access the file, if applicable.")
    created_at: datetime = Field(default_factory=datetime.now, description="The timestamp of the attachment.")
    uploader_id: Optional[str] = Field(None, description="The ID of the user who uploaded the attachment.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata for the attachment.")


class TaskComment(BaseModel):
    """Represents a comment made on a task."""
    comment_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique ID for the comment.")
    task_id: str = Field(description="The ID of the task this comment belongs to.")
    user_id: str = Field(description="The ID of the user who made the comment.")
    content: str = Field(description="The text content of the comment.")
    created_at: datetime = Field(default_factory=datetime.now, description="The timestamp of the comment.")


# --- Action-oriented Models ---

class Notification(BaseModel):
    """Represents a notification to be sent."""
    channel: str = Field(description="The channel to send the notification through (e.g., 'email', 'slack').")
    recipient: str = Field(description="The identifier for the recipient (e.g., email address, user ID, channel name).")
    subject: str = Field(description="The subject or title of the notification.")
    body: str = Field(description="The main content of the notification.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional data for the notification service.")


class EscalationAction(BaseModel):
    """
    Represents the set of actions to be taken when a task is escalated.
    """
    new_assignee: Optional[str] = Field(None, description="The ID of the new assignee for the task.")
    new_priority: Optional[TaskPriority] = Field(None, description="The new priority for the task.")
    notifications_to_send: List[Notification] = Field(default_factory=list, description="A list of notifications to send.")
    reason: str = Field(default="Escalation policy triggered", description="The reason for the escalation.")
    escalation_level: int = Field(default=1, description="The level of this escalation (e.g., 1st, 2nd).")
