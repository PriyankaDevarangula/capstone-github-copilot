# Design Review: Book API Documentation Sync

## Review scope
This review evaluates the current solution against the finalized requirements in [requirements.md](requirements.md) and the proposed architecture in [architecture.md](architecture.md).

The review is intentionally restricted to the Book API scope:
- GET /books
- GET /books/{id}
- POST /books

The review focuses on whether the architecture is safe, minimal, implementation-ready, and consistent with the requirements, especially for:
- Git-based change detection
- AST-based source inspection
- documentation synchronization boundaries
- documentation validation
- error handling and safe failure semantics
- no-op and deterministic output behavior
- CLI behavior and user messaging

## Review findings

### 1) BLOCKER — Exact API source convention is not yet fixed
- Finding: The architecture states that the source should use a “simple, clear convention” and that AST extraction should be used, but it does not define the exact source structure that the extractor will parse. This is necessary because the extractor must reliably read app/api.py without executing it.
- Why it matters: Without a single explicit contract, multiple implementations could parse the same file differently, making the tool unreliable and hard to test. It also risks misreading unrelated code or silently missing supported routes.
- Recommended decision: Define one explicit route-definition convention inside app/api.py, such as a single ROUTES list of structured route metadata objects, and require the extractor to parse exactly that structure. The convention must be limited to the supported endpoints and must be easy to validate.
- Change needed: This is primarily an architecture decision, not a product feature. architecture.md must define the exact route metadata convention before implementation begins.

### 2) HIGH — Generated document contract and marker format are not sufficiently specific
- Finding: The architecture requires generated endpoint blocks to be updated, but it does not specify the exact Markdown structure or marker names that must be used.
- Why it matters: Without a canonical output template and marker syntax, implementations may generate different documentation layouts, causing non-deterministic output and difficult validation.
- Recommended decision: Require a clearly named generated block with fixed markers (for example BEGIN GENERATED ENDPOINT BLOCK and END GENERATED ENDPOINT BLOCK) and a deterministic Markdown template that always renders the supported endpoint sections in a fixed order.
- Change needed: architecture.md must specify the exact marker syntax and the standard template format for each endpoint section.

### 3) HIGH — “Relevant supported API change” is still an implementation decision, not a precise requirement
- Finding: The requirements state that relevant supported API changes should trigger synchronization, but they do not define what counts as “relevant.”
- Why it matters: If the definition is too broad, the tool may rewrite documentation unnecessarily; if too narrow, it may ignore important changes. This directly affects no-op and update behavior.
- Recommended decision: Define “relevant change” as any change to the route metadata or route contract for the supported endpoints in app/api.py that affects the generated documentation: method, path, path parameter names, request schema, response schema, status codes, summary, or examples. Ignore unrelated changes outside the supported API contract.
- Change needed: requirements.md should clarify the definition of relevant change, and architecture.md should align with it.

### 4) HIGH — Git edge cases are described but not fully operationalized
- Finding: The architecture names missing Git HEAD, missing repository, and Git errors as important cases, but it does not define the exact exit behavior for each case.
- Why it matters: In real use, a repository may be in a detached HEAD state, an unborn branch, or a non-git directory. These conditions need deterministic behavior to avoid risky updates or confusing CLI output.
- Recommended decision: The application should treat the following as fail-safe states: no Git repository, missing HEAD, Git execution errors, and unsupported repository state. In those cases, show a clear failure message and do not update docs/api.md.
- Change needed: architecture.md should explicitly map each Git state to a result category: success, no-change, or fail-safe error.

### 5) HIGH — Staged and unstaged changes need explicit treatment
- Finding: The requirements say compare with the current Git HEAD, but they do not specify whether both staged and unstaged local changes count for synchronization.
- Why it matters: Different interpretations can lead to the same file being considered changed or unchanged depending on state. This creates inconsistent behavior when the user is editing app/api.py before running the CLI.
- Recommended decision: Define the comparison as git diff HEAD -- app/api.py, which includes both staged and unstaged changes since HEAD. This is the most faithful interpretation of “current app/api.py compared with the current Git HEAD.”
- Change needed: architecture.md should specify the Git command strategy and the reason it includes both staged and unstaged diffs.

### 6) MEDIUM — Unsupported API changes need a definitive fail-safe rule
- Finding: The requirements require unsupported API changes to be handled gracefully, but the architecture does not state whether unsupported changes should block sync, allow partial generation, or mark the file as invalid.
- Why it matters: If an unsupported route is introduced, the tool could silently ignore it or produce misleading docs, which violates the requirement to report errors clearly.
- Recommended decision: If the current API contract contains an unsupported route or a route outside the three permitted endpoints, the synchronizer must fail with a clear error message and leave docs/api.md unchanged.
- Change needed: architecture.md should explicitly state that only the supported three routes may be generated and any other route definition is a fail-safe error.

### 7) MEDIUM — Documentation marker failures are covered but not fully constrained
- Finding: The architecture identifies malformed markers as a failure case, but it does not define the exact expected behavior when markers are missing, duplicated, or mismatched.
- Why it matters: A malformed doc file is one of the most likely safety risks; the tool must never guess where to insert or replace content.
- Recommended decision: Define a strict marker pair rule: exactly one begin marker and one end marker for the generated block, with no duplicates. If missing or malformed, the synchronization fails and docs/api.md remains unchanged.
- Change needed: architecture.md should require exact marker validation and explicit failure semantics.

### 8) MEDIUM — Duplicate endpoint blocks and ordering are not explicitly resolved
- Finding: The validation section mentions detecting duplicate endpoint sections, but does not define ordering or how duplicates are handled.
- Why it matters: Duplicate sections can create conflicting documentation and make the output nondeterministic. Ordering matters because the requirement names specific endpoints and expects them to be rendered in a consistent way.
- Recommended decision: The generated endpoint sections must appear in canonical order: GET /books, GET /books/{id}, POST /books. Duplicate sections are invalid and must cause failure. The validator should reject duplicates rather than trying to merge them.
- Change needed: architecture.md should define canonical ordering and duplicate rejection explicitly.

### 9) MEDIUM — Partial writes and rollback behavior need exact implementation guidance
- Finding: The architecture says to write atomically to avoid partial update risk, but it does not specify the exact strategy.
- Why it matters: A safety-critical file such as docs/api.md should never be overwritten in place without a controlled write-and-validate process.
- Recommended decision: Use a temporary file in the same directory, write the complete updated content, validate it, and then atomically replace the original file only after validation passes. If any stage fails, leave the original file untouched.
- Change needed: architecture.md should describe the write sequence and safe replacement pattern.

### 10) MEDIUM — No-op synchronization semantics need a precise message and behavior
- Finding: The requirements say if no relevant changes exist, the tool should report documentation is already up to date and avoid unnecessary rewrite. The architecture mentions this but does not define whether the CLI still validates the file in that path.
- Why it matters: A no-op path should not trigger a rewrite, but it may still be useful to validate the current docs structure. The exact behavior should be consistent and safe.
- Recommended decision: On no-op detection, the app should validate the existing documentation file if it exists, report “Documentation already up to date,” and avoid writing the file. It should not rewrite the file merely because the validation happened.
- Change needed: architecture.md must clarify that validation is informational in the no-op path and not a write trigger.

### 11) MEDIUM — Documentation validity is under-specified beyond structure
- Finding: The validator checks for missing or malformed endpoint sections, but the architecture does not define exactly what content is required within each generated section.
- Why it matters: A section can exist but still be structurally wrong or semantically incomplete. That could allow documentation to pass validation while still being inaccurate.
- Recommended decision: Validation should include required fields per endpoint: method, path, description, path parameters (if any), request schema (if applicable), response status codes, response schema/example, and error responses when applicable. Validation should fail if a required field is missing.
- Change needed: architecture.md should specify the expected content contract per endpoint section.

### 12) LOW — CLI messaging contract is not fully specified
- Finding: The requirements require clear success, no-change, and failure messages, but they do not define the exact required wording or output categories.
- Why it matters: This is not a blocker, but it affects testability and clarity. The CLI should be deterministic and testable by output message categories.
- Recommended decision: Use fixed result states: SUCCESS, NO_CHANGE, ERROR. Each state maps to exactly one user-facing message pattern and a defined exit behavior.
- Change needed: architecture.md should include a minimal output contract for CLI messages.

### 13) LOW — Deterministic output and formatting are implied but not mandated
- Finding: The requirement mentions keeping the project simple and understandable, and the architecture mentions deterministic output, but it does not explicitly require deterministic Markdown formatting.
- Why it matters: Without formatting rules, generated docs may vary by implementation and become hard to diff or review.
- Recommended decision: Output must be deterministic: fixed endpoint ordering, fixed Markdown headings, fixed bullet and section formatting, and consistent whitespace rules.
- Change needed: architecture.md should define the canonical markdown output style.

## Risks and gaps summary
The highest-risk areas are:
- the exact route-definition convention in app/api.py
- the exact generated-doc section contract and markers
- the definition of “relevant supported API change”
- safe handling of Git repo states and diff semantics
- atomic update and rewrite safety
- strict validation against malformed or duplicate sections

These are all manageable with explicit design decisions and should be finalized before coding.

## Decisions made
The following decisions resolve the likely implementation risks and keep the project aligned with the requirements:

1. The app/api.py source-of-truth convention will be a single explicit metadata structure for the three supported routes.
2. Extraction will use Python AST only; no module import or execution.
3. Git comparison will use HEAD as the repository baseline and include both staged and unstaged diffs relative to HEAD.
4. The synchronization process will be user-triggered from the menu and will be a fail-safe operation.
5. The docs/api.md file will preserve all content outside the generated endpoint block.
6. The generated content will be placed inside exact begin/end markers and only that block will be replaced.
7. Validation will reject missing, malformed, duplicated, or misplaced generated sections.
8. The app will fail safely on any unsupported API contract, invalid source structure, or Git failure.
9. Output will be deterministic and follow a canonical endpoint order: GET /books, GET /books/{id}, POST /books.

## Resolved blockers
No genuine requirement ambiguity remains that requires a user question before implementation planning.

The concerns identified above are technical design decisions that can be resolved before implementation without changing the product requirements. They do not indicate missing product intent.

## Remaining assumptions
The following assumptions are intentionally narrow and do not expand the product scope:
- The route metadata convention will be defined by the implementation team before coding begins, using a simple AST-visible structure in app/api.py.
- The docs/api.md generated block will have explicit begin/end markers and a deterministic Markdown template.
- The CLI will expose only the minimal menu actions required by the requirements.
- The validation step will be strict and fail-safe rather than permissive.

## Testing implications
The design is testable with pytest without requiring external services or additional frameworks.

The tests should cover:
- no-change sync when API source is unchanged relative to HEAD
- relevant change detection when supported routes change
- unsupported endpoint detection and failure path
- invalid or missing app/api.py handling
- missing Git HEAD and Git failure handling
- malformed marker detection in docs/api.md
- duplicate section rejection
- correct endpoint ordering and deterministic output
- atomic-write safety and no partial update behavior
- CLI success/no-change/error message categories

## Final approval status
Final approval status: APPROVED FOR IMPLEMENTATION PLANNING

The architecture is not fully detailed to the level of code, but it is specific enough to proceed to implementation planning. The remaining concerns are implementation-level decisions, not unresolved product-level requirements.

No additional clarification question is required at this stage.
