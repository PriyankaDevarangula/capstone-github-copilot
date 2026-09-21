# Implementation Plan: Book API Documentation Sync

## 1. Overview
This plan covers the complete implementation of the Book API Documentation Sync project as defined by [requirements.md](requirements.md), [architecture.md](architecture.md), and [design-review.md](design-review.md).

The project remains intentionally small and limited to:
- Python
- a menu-driven CLI
- standard library only where practical
- Git CLI for change detection
- AST-based source inspection
- Markdown documentation updates in docs/api.md
- pytest as the test framework
- exactly three supported endpoints: GET /books, GET /books/{id}, POST /books

## 2. Project structure
### Planned repository structure
- app/
  - __init__.py
  - api.py
- docs/
  - api.md
- cli.py
- git_change_detector.py
- api_contract_extractor.py
- docs_synchronizer.py
- docs_validator.py
- app_service.py or orchestration.py
- requirements.txt (if needed for pytest environment documentation only)
- pytest.ini or equivalent test config
- README.md (optional, if the project requires a minimal project note)
- requirements.md
- architecture.md
- design-review.md
- impl-plan.md

### Purpose of the structure
- app/api.py is the source of truth.
- The CLI is the user entry point.
- Git and AST extraction are separate components to keep behavior testable and understandable.
- Synchronization and validation are separate steps to protect docs/api.md from partial or unsafe writes.

## 3. Task list by dependency

### Task ID: T1
### Task name: Define the explicit API source contract and route metadata convention
Purpose:
- Lock the AST-visible pattern in app/api.py before implementation.
- Ensure the extractor has a single known route metadata structure.

Files to create/modify:
- app/api.py
- architecture.md

Dependencies:
- None

Acceptance criteria:
- The route definition format is explicit and limited to the three supported endpoints.
- The format uses the final decorator-like route convention.
- The convention is AST-readable and does not require executing the module.

Blocked?
- No, the route convention is now explicitly finalized.

### Task ID: T2
### Task name: Create the project skeleton and repository layout
Purpose:
- Establish the minimal Python project layout.
- Provide the required directories and files for app, docs, and CLI entry points.

Files to create/modify:
- app/__init__.py
- app/api.py
- docs/api.md
- cli.py
- pytest.ini or equivalent configuration

Dependencies:
- T1

Acceptance criteria:
- The repository contains the expected directories and files.
- app/api.py exists and follows the agreed route metadata convention.
- docs/api.md exists and includes the generated block markers contract.

Blocked?
- No

### Task ID: T3
### Task name: Implement the menu-driven CLI
Purpose:
- Provide the user menu for operations, including synchronize documentation and exit.
- Route user actions to the orchestration layer.

Files to create/modify:
- cli.py
- app_service.py or orchestration.py

Dependencies:
- T2

Acceptance criteria:
- The CLI presents a minimal menu.
- User can select Synchronize Documentation.
- The CLI displays success, no-change, and failure messages clearly.
- The CLI exits cleanly.

Blocked?
- No

### Task ID: T4
### Task name: Implement Git-based change detection
Purpose:
- Compare app/api.py with HEAD and decide whether a relevant change exists.
- Handle missing repository, HEAD, and Git failures safely.

Files to create/modify:
- git_change_detector.py
- app_service.py or orchestration.py

Dependencies:
- T1
- T2

Acceptance criteria:
- git diff HEAD -- app/api.py is used to detect both staged and unstaged changes.
- The tool recognizes relevant supported API contract changes.
- No relevant changes results in a no-op status and no rewrite.
- Missing Git state or command failure results in an error status with no doc update.

Blocked?
- No

### Task ID: T5
### Task name: Implement AST-based API contract extraction
Purpose:
- Read app/api.py without executing it.
- Extract the supported endpoints and needed metadata.

Files to create/modify:
- api_contract_extractor.py
- app/api.py

Dependencies:
- T1
- T2

Acceptance criteria:
- AST parsing is used instead of import execution.
- Only GET /books, GET /books/{id}, and POST /books are extracted.
- Required fields are extracted for documentation generation.
- Unsupported or malformed route metadata causes a clear failure.

Blocked?
- No

### Task ID: T6
### Task name: Implement documentation generation for the supported endpoints
Purpose:
- Convert the extracted API contract into the exact Markdown format for docs/api.md.
- Keep output deterministic and ordered.

Files to create/modify:
- docs_synchronizer.py
- app_service.py or orchestration.py

Dependencies:
- T3
- T4
- T5

Acceptance criteria:
- The output uses a fixed endpoint order: GET /books, GET /books/{id}, POST /books.
- The generated Markdown contains the required sections for method, path, summary, parameters, request schema, response codes, response schema/example, and error responses.
- The generator produces the exact block content to be inserted into the generated markers.

Blocked?
- No

### Task ID: T7
### Task name: Implement safe documentation synchronization
Purpose:
- Update only the generated endpoint block in docs/api.md.
- Preserve all content outside the marked block.
- Prevent partial writes.

Files to create/modify:
- docs_synchronizer.py
- app_service.py or orchestration.py
- docs/api.md

Dependencies:
- T2
- T6

Acceptance criteria:
- The synchronizer locates the begin/end marker pair.
- Only content between markers is replaced.
- All other content in the file is preserved.
- Temporary file + validation + atomic replacement is used.
- Missing, malformed, or duplicate markers cause a failure without writing.

Blocked?
- No

### Task ID: T8
### Task name: Implement documentation validation
Purpose:
- Validate docs/api.md after generation or on no-change checks.
- Detect malformed, duplicate, missing, or unsupported endpoint sections.

Files to create/modify:
- docs_validator.py
- app_service.py or orchestration.py

Dependencies:
- T7

Acceptance criteria:
- The validator checks for required endpoint sections and canonical order.
- Duplicate, missing, malformed, or unsupported sections fail validation.
- Validation passes only for valid generated endpoint blocks.

Blocked?
- No

### Task ID: T9
### Task name: Implement orchestrated synchronization workflow
Purpose:
- Connect the CLI, change detector, extractor, synchronizer, and validator into a single, safe flow.

Files to create/modify:
- app_service.py or orchestration.py
- cli.py

Dependencies:
- T3
- T4
- T5
- T7
- T8

Acceptance criteria:
- The workflow handles success, no-change, and failure outcomes correctly.
- The workflow never writes partial documentation.
- An error in any stage stops the process and leaves docs/api.md unchanged.

Blocked?
- No

### Task ID: T10
### Task name: Implement expected failure handling and user-facing error messages
Purpose:
- Guarantee clear, safe behavior when Git, files, markers, or source structure are invalid.

Files to create/modify:
- git_change_detector.py
- api_contract_extractor.py
- docs_synchronizer.py
- docs_validator.py
- cli.py
- app_service.py or orchestration.py

Dependencies:
- T4
- T5
- T7
- T8

Acceptance criteria:
- Missing app/api.py, missing Git HEAD, Git failure, malformed markers, invalid route metadata, and unsupported routes all report clear messages.
- No partial write occurs in any failure case.
- User-visible status is explicit: success, no-change, or error.

Blocked?
- No

### Task ID: T11
### Task name: Create unit tests for core logic
Purpose:
- Validate behavior at the component level without requiring full end-to-end execution.

Files to create/modify:
- tests/test_git_change_detector.py
- tests/test_api_contract_extractor.py
- tests/test_docs_synchronizer.py
- tests/test_docs_validator.py
- tests/test_cli.py

Dependencies:
- T4
- T5
- T7
- T8
- T9

Acceptance criteria:
- Unit tests cover no-change and change detection behavior.
- AST extraction is verified for the three supported routes.
- Synchronizer preserves manual content and only replaces generated blocks.
- Validator rejects malformed or duplicate sections.
- CLI presents expected states and messages.

Blocked?
- No

### Task ID: T12
### Task name: Create integration and end-to-end tests
Purpose:
- Validate the complete project flow with realistic files and repo scenarios.

Files to create/modify:
- tests/test_integration_sync_flow.py
- tests/test_e2e_cli_flow.py

Dependencies:
- T9
- T10
- T11

Acceptance criteria:
- Integration tests prove the full workflow from Git diff through validator result.
- End-to-end tests cover success, no-change, and failure cases.
- All tests are based on real file operations and CLI behavior.

Blocked?
- No

### Task ID: T13
### Task name: Final verification and project readiness check
Purpose:
- Confirm the complete project meets the approved requirements and architecture.

Files to create/modify:
- All project files under test

Dependencies:
- T11
- T12

Acceptance criteria:
- pytest passes for unit and integration coverage.
- The app behavior matches the requirements.
- No implementation deviates outside the approved scope.
- Final project is ready for acceptance review.

Blocked?
- No

## 4. Final implementation status
All major implementation decisions are now explicitly resolved and no longer require additional product clarification before coding begins.

## 5. Small summary
- Total tasks: 13
- Blocked tasks: 0
- Implementation order: T1 -> T2 -> T3/T4/T5 -> T6/T7/T8 -> T9/T10 -> T11/T12 -> T13
- Remaining decisions: none before coding

This plan remains small, dependency-ordered, and consistent with the approved requirements and architecture.
