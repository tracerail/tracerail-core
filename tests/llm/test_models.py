import pytest
from pydantic import ValidationError

# Import the models to be tested
from tracerail.llm.base import LLMRequest, LLMResponse, LLMMessage, LLMUsage


class TestLLMModels:
    """
    Unit tests for the LLM data models to ensure validation and serialization
    are working as expected.
    """

    def test_llm_response_serialization_and_validation(self):
        """
        Tests that an LLMResponse can be serialized to a dictionary and then
        re-validated from that dictionary. This prevents the bug where
        LLMResponse was a dataclass and lacked `.model_validate()`.
        """
        # Arrange
        original_response = LLMResponse(
            content="This is the LLM's answer.",
            model="test-model",
            usage=LLMUsage(prompt_tokens=10, completion_tokens=20),
            request_id="req-123",
            finish_reason="stop",
            metadata={"source": "test"},
        )

        # Act
        # 1. Serialize the object to a dictionary.
        #    We use model_dump() here as it's the standard Pydantic way.
        response_dict = original_response.model_dump()

        # 2. Re-create the object from the dictionary using model_validate.
        #    This is the critical step that would fail if the model was a dataclass.
        validated_response = LLMResponse.model_validate(response_dict)

        # Assert
        # The re-created object should be identical to the original.
        assert validated_response == original_response
        # Also confirm that the nested model's validator ran correctly.
        assert validated_response.usage.total_tokens == 30

    def test_llm_request_content_to_messages(self):
        """
        Tests that providing only 'content' to an LLMRequest correctly
        populates the 'messages' list via its model validator.
        """
        # Act
        request = LLMRequest(content="Hello, world!")

        # Assert
        assert len(request.messages) == 1
        assert request.messages[0].role == "user"
        assert request.messages[0].content == "Hello, world!"
        assert request.content == "Hello, world!"  # content should still be present

    def test_llm_request_requires_content_or_messages(self):
        """
        Tests that creating an LLMRequest with neither 'content' nor 'messages'
        raises a ValidationError.
        """
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            LLMRequest()  # No content or messages provided

        # Check that the validation error contains our custom message.
        assert "Either 'content' or 'messages' must be provided" in str(exc_info.value)

    def test_llm_request_with_messages_only(self):
        """
        Tests that an LLMRequest can be created successfully with only a
        'messages' list.
        """
        # Arrange
        messages = [LLMMessage(role="user", content="This is a test.")]

        # Act
        try:
            request = LLMRequest(messages=messages)
        except ValidationError:
            pytest.fail("ValidationError was raised unexpectedly.")

        # Assert
        assert request.messages == messages
        assert request.content is None  # content should remain None

    def test_llm_usage_total_tokens_calculation(self):
        """
        Tests that the total_tokens field in LLMUsage is calculated correctly
        by its model validator.
        """
        # Act
        usage = LLMUsage(prompt_tokens=50, completion_tokens=100)

        # Assert
        assert usage.total_tokens == 150
