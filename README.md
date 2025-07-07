# TraceRail Core SDK

[![PyPI version](https://img.shields.io/pypi/v/tracerail-core.svg)](https://pypi.org/project/tracerail-core/)
[![Build Status](https://img.shields.io/github/actions/workflow/status/tracerail/tracerail-core/main.yml?branch=main)](https://github.com/tracerail/tracerail-core/actions)
[![Code Coverage](https://img.shields.io/codecov/c/github/tracerail/tracerail-core)](https://codecov.io/gh/tracerail/tracerail-core)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**TraceRail Core** is a Python SDK for building robust, production-ready AI workflows with built-in support for human-in-the-loop (HITL) task management. It provides the foundational components to orchestrate LLM interactions, intelligent routing, and durable execution using Temporal.

This library is the engine that powers the [TraceRail Bootstrap](https://github.com/tracerail/tracerail-bootstrap) application stack.

---

## Key Features

*   **Pluggable LLM Providers**: Easily switch between different LLM providers (OpenAI, Anthropic, Azure, DeepSeek) with a unified interface.
*   **Configurable Routing Engine**: Define rules to intelligently route content for automatic processing or human review.
*   **Durable Workflows**: Built-in integration with [Temporal.io](https://temporal.io/) to make your workflows stateful, reliable, and scalable.
*   **Task Management Primitives**: Core models and interfaces for creating and managing human-in-the-loop tasks.
*   **Async-First Design**: Fully asynchronous, leveraging `asyncio` for high-performance I/O operations.
*   **Pydantic-based Configuration**: Strong typing and validation for all configurations, loadable from environment variables.

---

## Installation

Install the library directly from PyPI:

```bash
pip install tracerail-core
```

---

## Quick Start

The following example demonstrates how to initialize the `TraceRail` client and process a piece of content. This single call will use the configured LLM, evaluate the result against the routing rules, and determine the next step.

```python
import asyncio
import tracerail

# Note: The client will automatically load configuration from environment
# variables (e.g., from a .env file). Ensure your LLM API key is set.
# See the Configuration section below.

async def main():
    """
    Initializes the TraceRail client and processes a sample prompt.
    """
    try:
        # create_client_async initializes all components (LLM, routing, etc.)
        async with await tracerail.create_client_async() as client:
            print(f"✅ Client initialized with LLM provider: {client.config.llm.provider.value}")

            prompt = "This is a simple test prompt for TraceRail."
            print(f"\n📝 Processing content: '{prompt}'")

            # The main entry point for the library
            result = await client.process_content(prompt)

            print("\n--- Processing Complete ---")
            print(f"🤖 LLM Response: {result.llm_response.content[:80]}...")
            print(f"🔀 Routing Decision: {result.routing_decision.decision.value}")
            print(f"   - Reason: {result.routing_decision.reason}")
            print(f"   - Human Review Required: {result.requires_human}")

    except tracerail.TraceRailError as e:
        print(f"❌ An error occurred: {e}")
        print("   Please ensure your .env file is configured correctly with an API key.")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Configuration

The library uses a `TraceRailConfig` model (based on Pydantic) to manage settings. Configuration is automatically loaded from environment variables. For local development, create a `.env` file in your project root:

```dotenv
# .env file
# Choose your provider and add the corresponding API key.
TRACERAIL_LLM_PROVIDER=openai
OPENAI_API_KEY="sk-..."
# DEEPSEEK_API_KEY="sk-..."

# Optionally, override the default task queue for Temporal
# TRACERAIL_TEMPORAL_TASK_QUEUE="my-custom-queue"
```

---

## Development & Contribution

We welcome contributions! To set up the development environment:

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/tracerail/tracerail-core.git
    cd tracerail-core
    ```
2.  **Install dependencies with Poetry**:
    This project uses [Poetry](https://python-poetry.org/) for dependency management.
    ```bash
    # This installs main dependencies plus dev and docs extras
    make install
    ```
3.  **Run tests and linters**:
    The `Makefile` contains convenience commands for all common development tasks.
    ```bash
    make test    # Run the full unit test suite
    make lint    # Check code style and formatting
    make format  # Automatically format the code
    make all     # Run install, lint, and test
    ```

---

## License

This project is licensed under the **MIT License**. See the `LICENSE` file for details.