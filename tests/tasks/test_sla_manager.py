import pytest
from datetime import datetime, timedelta

from tracerail.tasks.managers.sla import BasicSlaManager
from tracerail.tasks.models import TaskData, TaskResult, TaskStatus


class TestBasicSlaManager:
    """
    Unit tests for the BasicSlaManager to ensure it correctly handles
    SLA calculations and tracking.
    """

    @pytest.fixture
    def sla_manager(self) -> BasicSlaManager:
        """Provides a default BasicSlaManager instance for tests."""
        return BasicSlaManager(manager_name="test_sla", default_sla_hours=24)

    @pytest.fixture
    def sample_task_result(self) -> TaskResult:
        """Provides a sample TaskResult object with no due date set."""
        task_data = TaskData(title="Test Task")
        return TaskResult(
            task_id="task-123",
            data=task_data,
            status=TaskStatus.OPEN,
            created_at=datetime.now(),
        )

    def test_start_tracking_sets_due_date_on_task_data(
        self, sla_manager: BasicSlaManager, sample_task_result: TaskResult
    ):
        """
        Tests that start_tracking_task correctly sets the due_date on the
        nested TaskData object, preventing the AttributeError we found.
        """
        # Arrange: Ensure the due_date is initially None on the data model
        assert sample_task_result.data.due_date is None

        # Act: Start tracking the task, which should calculate and set the due date.
        sla_manager.start_tracking_task(sample_task_result)

        # Assert: The core of the bug fix verification.
        # Check that the due_date is now set on the correct nested object.
        assert sample_task_result.data.due_date is not None

        # Verify the calculation is correct
        expected_due_date = sample_task_result.created_at + timedelta(hours=24)
        assert abs(sample_task_result.data.due_date - expected_due_date) < timedelta(
            seconds=1
        )

    @pytest.mark.asyncio
    async def test_is_task_overdue_logic(self, sla_manager: BasicSlaManager):
        """
        Tests the logic of the is_task_overdue method for both overdue
        and on-time tasks.
        """
        # Arrange: Create a task that is definitely in the past
        overdue_task_data = TaskData(
            title="Overdue Task", due_date=datetime.now() - timedelta(days=1)
        )
        overdue_task = TaskResult(task_id="overdue-1", data=overdue_task_data)

        # Arrange: Create a task that is definitely in the future
        ontime_task_data = TaskData(
            title="On-time Task", due_date=datetime.now() + timedelta(days=1)
        )
        ontime_task = TaskResult(task_id="ontime-1", data=ontime_task_data)

        # Act & Assert
        assert await sla_manager.is_task_overdue(overdue_task) is True
        assert await sla_manager.is_task_overdue(ontime_task) is False

    @pytest.mark.asyncio
    async def test_check_sla_violations_identifies_overdue_tasks(
        self, sla_manager: BasicSlaManager, sample_task_result: TaskResult
    ):
        """
        Tests that check_sla_violations correctly identifies and returns
        only the tasks that are overdue from its tracked list.
        """
        # Arrange
        # Create an overdue task
        overdue_task_data = TaskData(
            title="Overdue Task", due_date=datetime.now() - timedelta(hours=1)
        )
        overdue_task = TaskResult(
            task_id="overdue-2",
            data=overdue_task_data,
            created_at=datetime.now() - timedelta(days=1),
        )

        # Track both an on-time task (sample_task_result) and an overdue task
        sla_manager.start_tracking_task(sample_task_result)
        sla_manager.start_tracking_task(overdue_task)

        # Act
        violations = await sla_manager.check_sla_violations()

        # Assert
        assert len(violations) == 1
        assert violations[0].task_id == "overdue-2"
