# Architecture: Book API Documentation Sync

## 1. Purpose and scope
This project is a small Python CLI application that keeps the Book API documentation aligned with the authoritative API source in app/api.py.

The goal is to ensure that when the supported Book API route definitions change, the generated documentation sections in docs/api.md are synchronized safely and predictably without overwriting approved manual content outside those sections.

The solution intentionally covers only:
- GET /books
- GET /books/{id}
- POST /books

The architecture is intentionally minimal and avoids frameworks, cloud services, external components, and background automation.

## 2. Architecture overview
The system is organized as a small set of cooperating Python components with a single menu-driven entry point.

The architecture is built around a clear flow:
1. The CLI presents actions to the user.
2. The user selects documentation synchronization.
3. The Change Detector compares the current app/api.py with the version at Git HEAD.
4. The API Contract Extractor reads the current source using Python AST inspection.
5. The Documentation Synchronizer updates only the generated endpoint blocks in docs/api.md.
6. The Documentation Validator checks the resulting documentation structure and content.
7. Results and errors are reported to the user through the CLI.

This design keeps responsibilities separated while staying compact enough to implement and test with pytest.

## 3. Component list
### 3.1 Source contract convention
The project will use one explicit, simple AST-visible convention in app/api.py so the extractor can read it reliably without executing code.

The source-of-truth structure will be a Python route convention using ordinary functions with a decorator-like route marker. The supported routes are defined exactly as:

@route("GET", "/books")
def get_books():
    ...

@route("GET", "/books/{id}")
def get_book(book_id: int):
    ...

@route("POST", "/books")
def create_book(book: dict):
    ...

The route decorator is a source-code convention for this project only; the application does not need to be a real HTTP server.

The functions must use clear type annotations and simple docstrings so the extractor can obtain the API contract deterministically.

This convention is intentionally limited to:
- GET /books
- GET /books/{id}
- POST /books

It prevents ambiguous parsing and keeps extraction deterministic.

### 3.2 CLI Layer
Responsible for user interaction and orchestrating the workflow.

Primary responsibilities:
- Display menu options
- Accept user input
- Start synchronization workflow
- Show success, no-change, and failure messages
- Exit cleanly

### 3.3 Change Detector
Responsible for determining whether a relevant API change exists since Git HEAD.

Primary responsibilities:
- Run Git commands against the repository
- Compare the current app/api.py against HEAD using git diff HEAD -- app/api.py
- Decide whether a supported API contract change is relevant
- Handle missing Git HEAD, missing repository, and Git failure cases safely

### 3.4 API Contract Extractor
Responsible for parsing app/api.py without executing it.

Primary responsibilities:
- Read the file content
- Parse it using Python AST
- Identify the supported routes only
- Extract method, path, summary, parameters, request schema, response schema, and examples
- Return structured data for documentation generation
- Fail clearly if the source convention is missing or malformed

### 3.5 Documentation Synchronizer
Responsible for reading and updating only the generated endpoint documentation blocks in docs/api.md.

Primary responsibilities:
- Load the existing docs file
- Locate clearly marked generated sections
- Replace only those sections
- Preserve all approved/manual content outside the generated sections
- Write atomically to avoid partial update risk
- Stop without writing if markers are malformed or validation fails

### 3.6 Documentation Validator
Responsible for checking whether docs/api.md contains the required generated endpoint documentation in the expected form.

Primary responsibilities:
- Validate required endpoint sections exist
- Detect missing or duplicate sections
- Detect malformed markers
- Detect unsupported or incorrectly structured endpoint docs
- Enforce canonical endpoint ordering: GET /books, GET /books/{id}, POST /books
- Report clear validation results

## 4. Responsibilities by component
### CLI Layer
- User-facing menu and workflow control
- Calls the synchronization flow in a defined order
- Displays human-readable messages
- Stops execution when a failure is detected

### Change Detector
- Guards the system against unnecessary rewrites
- Answers the key question: “Did the supported API source change since HEAD?”
- Fails clearly if Git is unavailable or the repository state is invalid

### API Contract Extractor
- Converts code into a structured contract model
- Prevents unsafe execution of untrusted source code
- Keeps extraction narrow to the three supported endpoints

### Documentation Synchronizer
- Performs the safe update step only after validation of inputs
- Ensures the generated endpoint blocks are replaced in place
- Preserves the rest of the file exactly

### Documentation Validator
- Validates both source-driven output and existing documentation state
- Reduces the risk of silently writing malformed docs
- Ensures downstream user trust and implementation safety

## 5. Data and control flow
### Main control flow
1. CLI starts.
2. User selects “Synchronize Documentation”.
3. Change Detector checks whether app/api.py differs from HEAD for supported API metadata using git diff HEAD -- app/api.py.
4. If no relevant change is detected, CLI reports “Documentation already up to date,” validates the file if present, and exits without rewriting the file.
5. If a relevant change is detected, API Contract Extractor reads app/api.py and extracts the endpoint metadata.
6. If the extracted contract includes unsupported routes or malformed metadata, the process fails safely and leaves docs/api.md unchanged.
7. Documentation Synchronizer reads docs/api.md and replaces only the marked endpoint blocks.
8. Documentation Validator checks whether the resulting file contains valid generated sections in canonical order.
9. If validation passes, success is reported.
10. If validation fails or any earlier step fails, the CLI reports a clear error and leaves docs/api.md unchanged.

## 6. How Git change detection works
The Change Detector is responsible for answering whether the API source is materially different from the version committed at HEAD.

### Expected behavior
- It compares HEAD:app/api.py against the current working-tree app/api.py using git diff HEAD -- app/api.py.
- It includes both staged and unstaged local changes because the comparison is against HEAD.
- It identifies whether the change affects the supported route metadata or route contract used for the three endpoints.
- It ignores unrelated files and unrelated changes outside the supported API source.

### Relevant change definition
For this project, only changes to app/api.py are relevant to documentation synchronization.

If app/api.py has not changed relative to HEAD, the system reports no relevant changes and does not rewrite docs/api.md.

If there is no Git HEAD, this is an operational failure and docs/api.md is not modified.

### Safety handling
The Change Detector must treat the following as failure or no-op conditions:
- Repository not initialized
- Missing Git executable
- app/api.py not present
- HEAD missing (for example, an unborn branch or no commit yet)
- Git command errors

In all such cases it should report a clear message and stop without updating documentation.

## 7. How API source extraction works
The API Contract Extractor must parse app/api.py with Python AST instead of importing or executing the module.

### Extraction approach
- Read app/api.py as text.
- Parse it with ast.parse().
- Search for a simple, explicit route-definition convention that represents supported endpoints.
- Restrict extraction to exactly these cases:
  - GET /books
  - GET /books/{id}
  - POST /books
- Extract data such as:
  - HTTP method
  - path
  - summary/description
  - path parameters
  - body schema
  - response schema/examples
  - status codes
  - error response information

### Why AST instead of execution
- Avoids running arbitrary Python code from the project
- Safer and deterministic
- Matches the requirement that the API source code is the source of truth and that the tool should inspect it reliably

### Source convention requirement
The implementation must define a clear, simple source convention that is easy for the extractor to interpret. The convention should be explicit in the application design, for example using simple route metadata dictionaries or structured route declarations, but without introducing a framework.

The extractor should fail with a clear error if the route convention is missing or malformed.

## 8. How documentation synchronization works
The Documentation Synchronizer will operate on docs/api.md and update only the generated endpoint blocks.

### Marked block pattern
The file must have clearly identifiable markers for each supported endpoint in this exact format:
- <!-- BEGIN ENDPOINT: GET /books -->
- <!-- END ENDPOINT: GET /books -->
- <!-- BEGIN ENDPOINT: GET /books/{id} -->
- <!-- END ENDPOINT: GET /books/{id} -->
- <!-- BEGIN ENDPOINT: POST /books -->
- <!-- END ENDPOINT: POST /books -->

Only the content inside each endpoint block is synchronized. Content outside these blocks remains unchanged. The generated content must appear in canonical endpoint order:
1. GET /books
2. GET /books/{id}
3. POST /books

### Update process
1. Read docs/api.md.
2. Locate the endpoint markers and verify they are present exactly once per endpoint.
3. Validate the markers are correctly formed, not nested, and not duplicated.
4. Build the new generated endpoint documentation from the extracted API contract.
5. Replace the content inside each endpoint block only.
6. Preserve all content before and after the blocks exactly.
7. Write the updated content to a temporary file in the same directory.
8. Validate the temporary content.
9. Atomically replace the original docs/api.md file only if validation succeeds.

### Safety rules
- If markers are missing, malformed, duplicated, out of order, nested, or contain unsupported endpoint markers, stop and report an error.
- If the generated content cannot be built, stop and leave docs/api.md unchanged.
- If validation fails at any point, do not replace the original file.
- No partial update is allowed.

## 9. How validation works
The Documentation Validator checks both the documentation file structure and the generated endpoint content.

### Validation checks
- Required generated section markers exist exactly once
- Endpoint sections for GET /books, GET /books/{id}, and POST /books are present in canonical order
- There are no duplicate endpoint sections
- Sections are correctly structured and internally consistent
- Unsupported endpoints are not present in the generated block
- Manual content outside the generated block remains untouched
- Markers are valid and not malformed
- Each endpoint section contains the required fields: method, path, summary, path parameters if applicable, request schema if applicable, response status codes, response schema or example, and error responses if applicable

### Validation outputs
The validator should return structured results like:
- valid
- no-change needed
- VALIDATION ERROR for malformed or missing endpoint markers or sections
- VALIDATION ERROR for duplicate, out-of-order, or unsupported endpoint blocks

These results are surfaced through the CLI as clear messages.

## 10. Error and failure handling
The architecture is designed to fail safely and visibly.

### Failure categories
- Missing or unreadable app/api.py
- Missing Git HEAD or repository state issues
- Git command failure
- Source structure invalid for AST parsing
- Unsupported or unrecognized endpoint definition
- Malformed documentation markers or duplicate markers
- Duplicate or invalid generated sections
- File read/write problems
- Validation failure before replacement or after temporary-write validation

### Error policy
Every failure path should:
- produce a clear error message,
- classify it as either VALIDATION ERROR or OPERATIONAL ERROR,
- stop processing immediately,
- leave docs/api.md unchanged,
- avoid partial or silent mutation

This is a core safety requirement and should be enforced at each major stage.

## 11. Data and file flow
### Files involved
- app/api.py — authoritative API source
- docs/api.md — documentation target
- .git — repository metadata used by Git detection

### Data flow
- app/api.py -> AST Extractor -> Structured API Contract
- Supported route metadata -> Change Detector -> relevant-change decision
- Structured API Contract -> Documentation Generator -> Generated endpoint markdown blocks
- docs/api.md + markers + generated blocks -> Synchronizer -> updated docs/api.md via temp-file validation and atomic replace
- updated docs/api.md -> Validator -> validation result
- validation result + Git status -> CLI -> user-facing message

## 12. Technology choices and rationale
### Python standard library
Used for:
- argparse or input-driven menu flow
- ast parsing
- pathlib for file handling
- subprocess for Git commands
- json or simple data structures for contract metadata
- tempfile or safe file write strategies

Rationale:
- Small and dependency-free
- Easy to test under pytest
- Matches the requirement for a minimal application

### CLI result categories
The CLI output is deliberately simple and deterministic:
- SUCCESS: synchronization completed
- NO CHANGE: no relevant API source changes detected
- VALIDATION ERROR: documentation/source structure is invalid
- OPERATIONAL ERROR: Git/file/system operation failed

This keeps the user-facing behavior consistent and testable without introducing extra menu features.

### Git CLI
Used for:
- identifying whether app/api.py changed relative to HEAD
- handling repository state checks

Rationale:
- Requirement explicitly says to compare against Git HEAD
- Minimal and standard for a local project

### Markdown
Used for:
- docs/api.md documentation format

Rationale:
- Simple human-readable format
- Fits the requirement for preserving manual content outside generated sections

### pytest
Used for:
- validating functionality and failure behavior
- covering CLI output states and failure-safe behavior

Rationale:
- Required by the project scope
- Fits a small Python application
- Enables deterministic verification for no-change, update, invalid-source, and invalid-doc scenarios

## 13. Key design constraints
- Only one small CLI-driven application
- No web frameworks, no database, no cloud, no deployment
- No background automation or watchers
- Only three supported API endpoints
- Source code inspection through AST; no execution of source code
- Changes are evaluated relative to Git HEAD
- Documentation updates must be atomic and scoped to marked blocks only
- All operational failures must be explicit and safe

## 14. Testing approach
Testing will be done with pytest and should focus on behavior rather than implementation details.

### Recommended test areas
- CLI menu renders valid options
- NO CHANGE path when app/api.py has no relevant changes from HEAD
- SUCCESS path when supported route metadata changes
- VALIDATION ERROR path when endpoint markers are malformed or out of order
- OPERATIONAL ERROR path when Git is unavailable, app/api.py is missing, or HEAD is missing
- AST extractor returns correct data for the three endpoints
- Documentation synchronizer updates only the specified endpoint blocks
- Validator detects missing, duplicated, malformed, or out-of-order endpoint sections
- Safe no-write behavior when docs/api.md cannot be validated or updated
- Deterministic output order and exact result categories

Tests should validate actual file behavior and user-visible outcomes, not mock-only behavior.

## 15. Explicitly out-of-scope items
The following are intentionally not included:
- FastAPI, Flask, or any other web framework
- database integration
- authentication or authorization
- frontend or browser interface
- external APIs or services
- cloud deployment or hosting
- CI/CD automation
- scheduled watchers or background jobs
- additional endpoints beyond the three supported routes
- broad refactoring or generic API-documentation platform features
- implementation beyond the architecture stage

## 16. Simple ASCII component diagram
+----------------------+
| User / Developer     |
+----------+-----------+
           |
           v
+----------------------+
| CLI Menu             |
| - show options       |
| - run sync          |
| - show results      |
+----------+-----------+
           |
           v
+---------------------------+
| Change Detector           |
| - Git diff vs HEAD       |
| - decide if sync needed   |
+------------+--------------+
             |
             v
+---------------------------+
| API Contract Extractor    |
| - AST parse app/api.py    |
| - extract 3 endpoints     |
+------------+--------------+
             |
             v
+---------------------------+
| Documentation Synchronizer|
| - read docs/api.md        |
| - replace marked blocks   |
| - preserve manual content |
+------------+--------------+
             |
             v
+---------------------------+
| Documentation Validator   |
| - verify endpoint blocks  |
| - detect malformed docs  |
+------------+--------------+
             |
             v
+---------------------------+
| Console / User Messages   |
+---------------------------+

## 17. Simple end-to-end flow
User selects Sync Documentation
        |
        v
Check Git diff vs HEAD for app/api.py
        |
        +-- No relevant change --> Report: already up to date
        |
        +-- Relevant change --> Parse app/api.py via AST
                                    |
                                    v
                           Extract supported endpoint metadata
                                    |
                                    v
                          Replace only marked endpoint block(s) in docs/api.md
                                    |
                                    v
                          Validate generated docs structure and content
                                    |
                                    +-- Invalid --> Report clear error, leave file unchanged
                                    |
                                    +-- Valid --> Report success

## 18. Summary
This architecture is intentionally small but robust. It separates the major concerns cleanly while keeping the implementation tractable and testable: Git-based change detection, AST-based source inspection, scoped documentation replacement, and explicit validation and failure handling.

It satisfies the requirements without introducing unnecessary complexity or unsupported technology.
