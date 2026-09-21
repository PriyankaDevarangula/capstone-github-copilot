# Requirements: Book API Documentation Sync

## Goal
As a developer, I want the API documentation to be automatically updated when the Book API source code changes, so that the documentation stays consistent with the actual API.

## Scope
This project is intentionally limited to a small Python CLI application that manages documentation synchronization for the Book API.

Supported API scope:
- GET /books
- GET /books/{id}
- POST /books

The source of truth is the Python source code in app/api.py. Documentation is maintained in docs/api.md.

## Decisions agreed
- The API is implemented as a custom Python application without FastAPI, Flask, or any other framework.
- The source code in app/api.py is the authoritative definition of the API.
- The CLI is menu-driven and the user triggers synchronization by selecting Synchronize Documentation.
- Synchronization checks the current app/api.py against the version in the current Git HEAD.
- If relevant API changes are detected, docs/api.md is updated.
- If no relevant changes are detected, the tool reports that the documentation is already up to date and does not rewrite the file unnecessarily.
- Only clearly marked endpoint documentation blocks are updated; all approved/manual content outside those sections is preserved.
- The tool must fail clearly and leave docs/api.md unchanged if synchronization cannot be completed safely.
- The implementation must be testable with pytest.
- No database, authentication, external services, frontend, cloud deployment, or CI/CD are included.

## Functional requirements
### FR1: API source inspection
The application must inspect app/api.py as the source of truth using a simple, reliable convention that can be parsed without executing the API code.

The source must expose the supported endpoints in a way that can be read reliably by Python AST inspection.

### FR2: Supported endpoint coverage
The application must support exactly these endpoints:
- GET /books
- GET /books/{id}
- POST /books

For each supported endpoint, the generated documentation must include the relevant method, path, summary, path parameters, request body schema, response codes, response schema or examples, error responses, and request/response examples where available.

### FR3: Synchronization trigger
The application must provide a menu-driven CLI with an option to synchronize documentation.

When the user selects Synchronize Documentation, the application must:
1. Read the current app/api.py.
2. Compare it with the version at the current Git HEAD.
3. Detect whether a relevant supported API change exists.
4. If relevant changes exist, update the generated endpoint sections in docs/api.md.
5. If no relevant changes exist, report that documentation is already up to date and avoid rewriting the file.

### FR4: Documentation update boundaries
The documentation file must preserve all approved/manual content outside the generated endpoint sections.

The synchronizer must update only clearly marked endpoint blocks. It must not replace the entire docs/api.md file.

The generated sections must be separated and identifiable for future synchronization.

### FR5: Error handling
The application must handle expected operational failures clearly and safely. If synchronization cannot be completed safely, it must:
- report a clear error message,
- stop without silently continuing,
- leave docs/api.md unchanged.

Expected failure cases include:
- missing app/api.py,
- missing Git HEAD,
- invalid API source structure,
- malformed documentation markers,
- unsupported API changes,
- unreadable or invalid documentation file state.

### FR6: CLI behavior
The CLI must be small and understandable.

At minimum, it must allow the user to:
- view the menu,
- run documentation synchronization,
- exit the application.

### FR7: Testability
The solution must be testable with pytest. Tests must validate the key behaviors of source detection, synchronization decisions, documentation updates, and error handling without requiring external services or frameworks.

## Non-functional requirements
### NFR1: Simplicity
The project must remain small, readable, and intentionally limited in scope.

### NFR2: Standard library first
Python standard library functionality should be used where practical. No unnecessary external frameworks or services should be introduced.

### NFR3: Reliability and safety
Documentation must not be silently corrupted or partially updated. Updates must only happen when the tool can safely determine the correct output.

### NFR4: Maintainability
The implementation must use a clear and explicit convention for the API definition so the documentation synchronizer can inspect the source reliably and predictably.

### NFR5: Output clarity
All user-visible messages must clearly state whether synchronization succeeded, found no relevant changes, or failed and why.

## Constraints
- No database, authentication, frontend, cloud deployment, CI/CD, or external services.
- No additional API endpoints beyond the three supported endpoints.
- No background watcher, scheduler, or automatic runtime process outside the CLI.
- No use of FastAPI, Flask, or any other web framework.
- No implementation beyond the finalized requirements stage.

## Acceptance criteria
The project is complete for the Requirements stage when:
1. The scope is clearly limited to the three endpoints and the custom Python API source in app/api.py.
2. The synchronization workflow is defined as a CLI-triggered action based on Git diff against HEAD.
3. The documentation update rules preserve manual content outside the generated sections.
4. The failure behavior is explicitly defined as fail-safe with no silent partial writes.
5. The requirements are precise enough for implementation and test design with pytest.
