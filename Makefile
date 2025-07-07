.PHONY: help install test lint format build all

# Set default command to 'help' when no target is specified.
.DEFAULT_GOAL := help

# Define colors for output
GREEN  := $(shell tput -T screen setaf 2)
YELLOW := $(shell tput -T screen setaf 3)
RESET  := $(shell tput -T screen sgr0)

# --- Development Lifecycle Commands ---

help:
	@echo "tracerail-core - Library Development Commands"
	@echo "=============================================="
	@echo ""
	@echo "${YELLOW}Development & Testing:${RESET}"
	@echo "  install        Install dependencies using Poetry"
	@echo "  test           Run all unit tests with pytest"
	@echo "  lint           Check code formatting and style with Ruff & Black"
	@echo "  format         Automatically format code with Ruff & Black"
	@echo "  build          Build the library package for distribution"
	@echo ""
	@echo "${YELLOW}Convenience Commands:${RESET}"
	@echo "  all            Run install, lint, and test in sequence"
	@echo ""

all: install lint test
	@echo "\n${GREEN}✅ All checks passed.${RESET}"

install:
	@echo "📦 Installing project dependencies via Poetry..."
	@poetry install --with dev --with docs

test:
	@echo "🧪 Running unit tests..."
	@poetry run pytest

lint:
	@echo "🎨 Checking code style with Ruff..."
	@poetry run ruff check .
	@echo "✒️  Checking code formatting with Black..."
	@poetry run black --check .

format:
	@echo "🎨 Auto-fixing code style with Ruff..."
	@poetry run ruff check . --fix
	@echo "✒️  Auto-formatting code with Black..."
	@poetry run black .

build:
	@echo "🏗️  Building library distributables (wheel and sdist)..."
	@poetry build
