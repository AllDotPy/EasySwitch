# Contributing to EasySwitch

## Prerequisites

- Python 3.9+
- `pip` (or `uv` for faster installs)

## Local Setup

```bash
git clone https://github.com/AllDotPy/EasySwitch.git
cd EasySwitch

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install the package in editable mode with dev dependencies
pip install -e ".[dev]"
```

## Code Conventions

- **Typing**: Use type annotations for all function signatures and public attributes
- **Async**: Use `async/await` for all I/O-bound operations
- **Naming**:
  - Variables/functions: `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPER_CASE`
- **Comments**: Write clear English comments explaining the *why*, not the *what*
- **Imports**: Standard library → third-party → local (separated by blank lines)

## Testing

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_paystack.py -v

# Run with coverage
python -m pytest tests/ --cov=easyswitch
```

Tests use `pytest-asyncio` for async adapter methods. All external APIs are mocked.

## Adding a New Provider

1. Create `easyswitch/integrators/<name>.py`
2. Inherit from `BaseAdapter` and add `@AdaptersRegistry.register()`
3. Implement all abstract methods (see [Base Adapter](api-reference/base-adapter.md))
4. Add the provider to the `Provider` enum in `easyswitch/types.py`
5. Write tests in `tests/test_<name>.py`
6. Add documentation in `docs/integrations/<name>.md`
7. Run tests: `python -m pytest tests/ -v`

## Pull Request Process

1. Create a branch from `main`
2. Implement your changes with tests
3. Run the full test suite and ensure all tests pass
4. Open a PR with a clear description of the changes
