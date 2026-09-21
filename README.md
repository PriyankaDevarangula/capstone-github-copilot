# Book API Documentation Sync

This project is a small Python application that keeps the Book API documentation synchronized with the source-of-truth API definitions in app/api.py.

## Purpose
The application compares the current app/api.py with Git HEAD and, when relevant changes are detected, updates only the generated endpoint sections in docs/api.md.

## Supported endpoints
- GET /books
- GET /books/{id}
- POST /books

## Project structure
- app/
  - __init__.py
  - api.py
  - cli.py
  - change_detector.py
  - extractor.py
  - synchronizer.py
  - validator.py
- docs/
  - api.md
- tests/
  - test_app_api.py
  - test_cli.py
  - test_change_detector.py
  - test_extractor.py
  - test_synchronizer.py
  - test_validator.py

## Prerequisites
- Python 3.10+
- Git installed and available on PATH

## Installation
1. Clone the repository.
2. Change into the project directory.
3. Ensure Python and Git are installed.

## Running the application
From the project root, run:

python -m app.cli

The menu supports:
1. Synchronize Documentation
2. Validate Documentation
3. Exit

## Synchronization behavior
- The source of truth is app/api.py.
- The sync logic compares the current file with Git HEAD.
- Only the endpoint blocks in docs/api.md are updated.
- All content outside the generated endpoint blocks is preserved.
- If the source or documentation is invalid, the operation fails safely without partial updates.

## Testing
Run the full test suite with:

pytest

## Scope and limitations
- Only the three supported endpoints are included.
- No database, authentication, frontend, cloud deployment, or external services are used.
- No HTTP server or web framework is implemented.
- The route decorator is a source-code convention only.
