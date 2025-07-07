# TraceRail Core Interfaces Design

This document defines the core interfaces for the `tracerail-core` package that will provide production-ready libraries for AI workflow systems with human-in-the-loop task management.

## Package Structure

```
tracerail-core/
├── tracerail/
│   ├── __init__.py
│   ├── llm/                     # LLM abstraction layer
│   │   ├── __init__.py
│   │   ├── base.py             # Abstract base classes
│   │   ├── providers/          # Concrete implementations
│   │   │   ├── __init__.py
│   │   │   ├── deepseek.py
│   │   │   ├── openai.py
│   │   │   └── anthropic.py
│   │   └── exceptions.py
│   ├── routing/                # Decision routing engines
│   │   ├── __init__.py
│   │   ├── base.py            # Abstract routing interface
│   │   ├── rules.py           # Rule-based engine
│   │   ├── ml.py              # ML-based routing
│   │   └── dmn.py             # DMN integration
│   ├── tasks/                  # Task management (Temporal-native)
│   │   ├── __init__.py
│   │   ├── models.py          # Data models
│   │   ├── workflows.py       # Task management workflows
│   │   ├── activities.py      # Task-related activities
│   │   ├── assignment.py      # Assignment strategies
│   │   ├── sla.py             # SLA management
│   │   └── escalation.py      # Escalation policies
│   ├── temporal/              # Temporal utilities
│   │   ├── __init__.py
│   │   ├── base.py           # Base workflow/activity classes
│   │   ├── signals.py        # Signal handling utilities
│   │   └── queries.py        # Query utilities
│   └── integrations/          # External system integrations
│       ├── __init__.py
│       ├── flowable.py       # Flowable DMN
│       └── monitoring.py     # Observability
└── tests/
```

## Core Interfaces

### 1. LLM Provider Interface

```python
# tracerail/llm/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass
from enum import Enum

class LLMProvider(str, Enum):
    DEEPSEEK = "deepseek"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"

@dataclass
class LLMRequest:
    messages: list[Dict[str, str]]
    model: str
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    stream: bool = False
    metadata: Dict[str, Any] = None

@dataclass
class LLMResponse:
    content: str
    usage: Dict[str, int]  # prompt_tokens, completion_tokens, total_tokens
    model: str
    provider: str
    metadata: Dict[str, Any] = None

@dataclass
class LLMStreamChunk:
    content: str
    done: bool = False
    metadata: Dict[str, Any] = None

class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers"""
    
    def __init__(self, api_key: str, base_url: Optional[str] = None, **kwargs):
        self.api_key = api_key
        self.base_url = base_url
        self.config = kwargs
    
    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate a single response"""
        pass
    
    @abstractmethod
    async def stream(self, request: LLMRequest) -> AsyncGenerator[LLMStreamChunk, None]:
        """Generate streaming response"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if provider is healthy"""
        pass
    
    @property
    @abstractmethod
    def supported_models(self) -> list[str]:
        """List of supported models"""
        pass

class LLMFactory:
    """Factory for creating LLM providers"""
    
    @staticmethod
    def create(provider: LLMProvider, **kwargs) -> BaseLLMProvider:
        """Create LLM provider instance"""
        pass
    
    @staticmethod
    def from_config(config: Dict[str, Any]) -> BaseLLMProvider:
        """Create provider from configuration"""
        pass
```

### 2. Routing Engine Interface

```python
# tracerail/routing/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class RoutingDecision(str, Enum):
    AUTO = "auto"
    HUMAN = "human"
    ESCALATE = "escalate"
    REJECT = "reject"

@dataclass
class RoutingContext:
    """Input context for routing decisions"""
    content: str
    metadata: Dict[str, Any]
    token_count: Optional[int] = None
    sentiment: Optional[str] = None
    complexity_score: Optional[float] = None
    user_id: Optional[str] = None
    priority: Optional[str] = None

@dataclass
class RoutingResult:
    """Result of routing decision"""
    decision: RoutingDecision
    confidence: float  # 0.0 to 1.0
    reason: str
    metadata: Dict[str, Any]
    suggested_assignee: Optional[str] = None
    sla_hours: Optional[int] = None

class BaseRoutingEngine(ABC):
    """Abstract base class for routing engines"""
    
    @abstractmethod
    async def route(self, context: RoutingContext) -> RoutingResult:
        """Make routing decision"""
        pass
    
    @abstractmethod
    async def explain(self, context: RoutingContext) -> Dict[str, Any]:
        """Explain routing logic for debugging"""
        pass

class RoutingEngineFactory:
    """Factory for creating routing engines"""
    
    @staticmethod
    def create_rules_engine(rules_config: Dict[str, Any]) -> 'RulesEngine':
        pass
    
    @staticmethod
    def create_ml_engine(model_path: str) -> 'MLEngine':
        pass
    
    @staticmethod
    def create_dmn_engine(dmn_url: str, decision_key: str) -> 'DMNEngine':
        pass
```

### 3. Task Management Interface

```python
# tracerail/tasks/models.py
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    WAITING_REVIEW = "waiting_review"
    COMPLETED = "completed"
    ESCALATED = "escalated"
    CANCELLED = "cancelled"

class TaskPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

@dataclass
class TaskData:
    """Core task information"""
    id: str
    content: str
    task_type: str
    priority: TaskPriority
    created_at: datetime
    created_by: str
    metadata: Dict[str, Any]
    
    # SLA settings
    sla_hours: int = 24
    escalation_hours: int = 48
    
    # Assignment requirements
    skills_required: List[str] = None
    assignee_pool: Optional[str] = None
    min_confidence_level: Optional[float] = None

@dataclass
class TaskAssignment:
    """Task assignment information"""
    task_id: str
    assignee_id: str
    assigned_at: datetime
    due_at: datetime
    assignment_reason: str
    metadata: Dict[str, Any] = None

@dataclass
class TaskResult:
    """Task completion result"""
    task_id: str
    status: TaskStatus
    result_data: Dict[str, Any]
    completed_by: str
    completed_at: datetime
    review_comments: Optional[str] = None
    quality_score: Optional[float] = None

# tracerail/tasks/base.py
from abc import ABC, abstractmethod
from typing import List, Optional, AsyncGenerator

class BaseTaskManager(ABC):
    """Abstract interface for task management systems"""
    
    @abstractmethod
    async def create_task(self, task_data: TaskData) -> str:
        """Create a new task, returns task_id"""
        pass
    
    @abstractmethod
    async def assign_task(self, task_id: str, assignee_id: str) -> TaskAssignment:
        """Assign task to user"""
        pass
    
    @abstractmethod
    async def complete_task(self, task_id: str, result: TaskResult) -> None:
        """Mark task as completed"""
        pass
    
    @abstractmethod
    async def escalate_task(self, task_id: str, reason: str) -> None:
        """Escalate task"""
        pass
    
    @abstractmethod
    async def get_task(self, task_id: str) -> Optional[TaskData]:
        """Get task by ID"""
        pass
    
    @abstractmethod
    async def get_user_tasks(self, user_id: str, status: Optional[TaskStatus] = None) -> List[TaskData]:
        """Get tasks assigned to user"""
        pass
    
    @abstractmethod
    async def get_overdue_tasks(self) -> List[TaskData]:
        """Get tasks past their SLA"""
        pass

class BaseAssignmentStrategy(ABC):
    """Abstract interface for task assignment strategies"""
    
    @abstractmethod
    async def assign(self, task_data: TaskData, available_users: List[str]) -> str:
        """Select best assignee for task"""
        pass

class BaseSLAManager(ABC):
    """Abstract interface for SLA management"""
    
    @abstractmethod
    async def check_sla_breaches(self) -> List[str]:
        """Get list of task IDs with SLA breaches"""
        pass
    
    @abstractmethod
    async def get_sla_status(self, task_id: str) -> Dict[str, Any]:
        """Get SLA status for specific task"""
        pass
```

### 4. Temporal Integration Interface

```python
# tracerail/temporal/base.py
from abc import ABC, abstractmethod
from temporalio import workflow, activity
from typing import Dict, Any, Optional, TypeVar, Generic

T = TypeVar('T')

class BaseAIWorkflow(ABC):
    """Base class for AI workflows with human-in-the-loop"""
    
    @workflow.run
    @abstractmethod
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main workflow execution"""
        pass
    
    async def process_with_llm(self, content: str, model: str = None) -> Dict[str, Any]:
        """Common LLM processing activity"""
        return await workflow.execute_activity(
            self.llm_activity,
            content,
            start_to_close_timeout=timedelta(minutes=5)
        )
    
    async def route_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Common routing decision activity"""
        return await workflow.execute_activity(
            self.routing_activity,
            context,
            start_to_close_timeout=timedelta(seconds=30)
        )
    
    async def wait_for_human_decision(self, task_data: Dict[str, Any], timeout_hours: int = 24) -> Dict[str, Any]:
        """Wait for human decision with SLA timeout"""
        try:
            return await workflow.wait_condition(
                lambda: workflow.get_signal("human_decision"),
                timeout=timedelta(hours=timeout_hours)
            )
        except asyncio.TimeoutError:
            # SLA breach - escalate
            await self.escalate_task(task_data)
            # Continue waiting with extended deadline
            return await workflow.wait_condition(
                lambda: workflow.get_signal("human_decision"),
                timeout=timedelta(hours=timeout_hours * 2)
            )
    
    @abstractmethod
    async def llm_activity(self, content: str) -> Dict[str, Any]:
        """LLM processing activity - must be implemented"""
        pass
    
    @abstractmethod
    async def routing_activity(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Routing decision activity - must be implemented"""
        pass
    
    async def escalate_task(self, task_data: Dict[str, Any]) -> None:
        """Default escalation handling"""
        await workflow.execute_activity(
            escalate_task_activity,
            task_data,
            start_to_close_timeout=timedelta(minutes=2)
        )

# Temporal-native task management workflows
@workflow.defn
class TaskManagementWorkflow:
    """Long-running workflow that manages all human tasks"""
    
    def __init__(self):
        self.active_tasks: Dict[str, TaskData] = {}
        self.sla_timers: Dict[str, Any] = {}
    
    @workflow.run
    async def run(self) -> None:
        """Main task management loop"""
        pass
    
    @workflow.signal
    def create_task(self, task_data: TaskData) -> None:
        """Signal to create new task"""
        pass
    
    @workflow.signal
    def complete_task(self, task_id: str, result: TaskResult) -> None:
        """Signal to complete task"""
        pass
    
    @workflow.query
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Query task status"""
        pass
    
    @workflow.query
    def get_user_tasks(self, user_id: str) -> List[TaskData]:
        """Query tasks for user"""
        pass
```

### 5. Configuration Interface

```python
# tracerail/config.py
from dataclasses import dataclass
from typing import Dict, Any, Optional
import os

@dataclass
class LLMConfig:
    provider: str
    api_key: str
    base_url: Optional[str] = None
    default_model: str = "gpt-4o-mini"
    max_tokens: int = 1000
    temperature: float = 0.7

@dataclass
class RoutingConfig:
    engine_type: str  # "rules", "ml", "dmn"
    config_data: Dict[str, Any]

@dataclass
class TaskConfig:
    default_sla_hours: int = 24
    escalation_hours: int = 48
    assignment_strategy: str = "round_robin"
    enable_auto_escalation: bool = True

@dataclass
class TemporalConfig:
    host: str = "localhost:7233"
    namespace: str = "default"
    task_queue: str = "tracerail"
    
@dataclass
class TraceRailConfig:
    """Main configuration object"""
    llm: LLMConfig
    routing: RoutingConfig
    tasks: TaskConfig
    temporal: TemporalConfig
    
    @classmethod
    def from_env(cls) -> 'TraceRailConfig':
        """Create config from environment variables"""
        return cls(
            llm=LLMConfig(
                provider=os.getenv("TRACERAIL_LLM_PROVIDER", "deepseek"),
                api_key=os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY"),
                base_url=os.getenv("LLM_BASE_URL"),
            ),
            routing=RoutingConfig(
                engine_type=os.getenv("TRACERAIL_ROUTING_ENGINE", "rules"),
                config_data={}
            ),
            tasks=TaskConfig(
                default_sla_hours=int(os.getenv("TRACERAIL_DEFAULT_SLA_HOURS", "24")),
            ),
            temporal=TemporalConfig(
                host=os.getenv("TEMPORAL_HOST", "localhost:7233"),
            )
        )
    
    @classmethod
    def from_file(cls, config_path: str) -> 'TraceRailConfig':
        """Load config from YAML/JSON file"""
        pass
```

### 6. High-Level Client Interface

```python
# tracerail/__init__.py
from .config import TraceRailConfig
from .llm import LLMFactory, LLMRequest, LLMResponse
from .routing import RoutingEngineFactory, RoutingContext, RoutingResult
from .tasks import TaskManager, TaskData, TaskResult
from .temporal import BaseAIWorkflow

class TraceRail:
    """Main client interface for TraceRail"""
    
    def __init__(self, config: TraceRailConfig):
        self.config = config
        self._llm_provider = None
        self._routing_engine = None
        self._task_manager = None
    
    @property
    def llm(self):
        """Get LLM provider instance"""
        if not self._llm_provider:
            self._llm_provider = LLMFactory.create(
                self.config.llm.provider,
                api_key=self.config.llm.api_key,
                base_url=self.config.llm.base_url
            )
        return self._llm_provider
    
    @property
    def routing(self):
        """Get routing engine instance"""
        if not self._routing_engine:
            self._routing_engine = RoutingEngineFactory.create_rules_engine(
                self.config.routing.config_data
            )
        return self._routing_engine
    
    @property
    def tasks(self):
        """Get task manager instance"""
        if not self._task_manager:
            self._task_manager = TaskManager(self.config)
        return self._task_manager
    
    async def process_content(self, content: str, **kwargs) -> Dict[str, Any]:
        """High-level content processing with routing"""
        # LLM analysis
        llm_response = await self.llm.generate(LLMRequest(
            messages=[{"role": "user", "content": content}],
            model=self.config.llm.default_model
        ))
        
        # Routing decision
        routing_result = await self.routing.route(RoutingContext(
            content=content,
            metadata=kwargs,
            token_count=llm_response.usage.get("total_tokens")
        ))
        
        return {
            "llm_response": llm_response,
            "routing": routing_result,
            "requires_human": routing_result.decision == "human"
        }

# Convenience functions
def create_client(config_path: str = None) -> TraceRail:
    """Create TraceRail client from config file or environment"""
    if config_path:
        config = TraceRailConfig.from_file(config_path)
    else:
        config = TraceRailConfig.from_env()
    
    return TraceRail(config)

# Export main interfaces
__all__ = [
    "TraceRail",
    "TraceRailConfig", 
    "LLMRequest",
    "LLMResponse",
    "RoutingContext",
    "RoutingResult",
    "TaskData",
    "TaskResult",
    "BaseAIWorkflow",
    "create_client"
]
```

## Usage Examples

### Simple Usage (Bootstrap Examples)
```python
import tracerail

# Create client from environment
client = tracerail.create_client()

# Process content with automatic routing
result = await client.process_content("Analyze this complex document...")

if result["requires_human"]:
    # Create human task
    task_id = await client.tasks.create_task(
        TaskData(
            content="Please review this analysis",
            task_type="content_review",
            priority="normal"
        )
    )
    print(f"Task created: {task_id}")
```

### Advanced Usage (Custom Workflows)
```python
from tracerail import BaseAIWorkflow, TraceRail
from temporalio import workflow

@workflow.defn  
class ContentAnalysisWorkflow(BaseAIWorkflow):
    def __init__(self):
        self.tracerail = TraceRail.from_env()
    
    async def run(self, content: str) -> Dict[str, Any]:
        # Use built-in LLM processing
        llm_result = await self.process_with_llm(content)
        
        # Use built-in routing
        routing = await self.route_decision({
            "content": content,
            "llm_result": llm_result
        })
        
        if routing["decision"] == "human":
            # Use built-in human task management
            human_result = await self.wait_for_human_decision({
                "content": content,
                "llm_analysis": llm_result
            })
            return self.merge_results(llm_result, human_result)
        
        return llm_result
```

This interface design provides:
- **Clean abstractions** for all major components
- **Pluggable implementations** (swap LLM providers, routing engines)
- **Temporal-native task management** built-in
- **Production-ready patterns** (SLA, escalation, assignment)
- **Simple high-level API** for common use cases
- **Advanced customization** for complex workflows

Ready to implement this structure?