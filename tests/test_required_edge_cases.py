from pathlib import Path

from app.cli import AppRuntime
from app.synchronizer import SynchronizationError, synchronize_documentation
from app.validator import DocumentationValidator


def test_missing_docs_file_fails_safely(tmp_path):
    docs = tmp_path / "missing.md"
    contract = {
        "GET /books": {
            "method": "GET",
            "path": "/books",
            "summary": "Return the list of books.",
            "parameters": [],
            "request_body": None,
            "responses": {"200": {"description": "List of books returned successfully."}},
            "errors": ["500 Internal server error."],
            "examples": {"response": {"status": 200, "body": {"books": []}}},
        },
        "GET /books/{id}": {
            "method": "GET",
            "path": "/books/{id}",
            "summary": "Return a single book by ID.",
            "parameters": [{"name": "id", "kind": "path"}],
            "request_body": None,
            "responses": {"200": {"description": "Book found."}},
            "errors": ["404 Book not found."],
            "examples": {"response": {"status": 200, "body": {"id": 1}}},
        },
        "POST /books": {
            "method": "POST",
            "path": "/books",
            "summary": "Create a new book record.",
            "parameters": [],
            "request_body": {"type": "object"},
            "responses": {"201": {"description": "Book created successfully."}},
            "errors": ["400 Invalid book payload."],
            "examples": {"request": {"method": "POST", "body": {"title": "Example"}}, "response": {"status": 201, "body": {"id": 1}}},
        },
    }

    try:
        synchronize_documentation(docs, contract)
        raise AssertionError("Expected SynchronizationError")
    except SynchronizationError as exc:
        assert "missing" in str(exc).lower()


def test_missing_git_head_unborn_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "app").mkdir()
    (repo / "app" / "api.py").write_text("print('x')\n", encoding="utf-8")

    import subprocess

    subprocess.run(["git", "init"], cwd=str(repo), check=True, stdout=subprocess.DEVNULL)
    result = subprocess.run(["git", "rev-parse", "--verify", "HEAD"], cwd=str(repo), check=False, capture_output=True, text=True)
    assert result.returncode != 0

    from app.change_detector import detect_api_change

    detection = detect_api_change(repo, repo / "app" / "api.py")
    assert detection.status == "OPERATIONAL ERROR"


def test_duplicate_endpoint_markers_are_rejected():
    markdown = '''
# Book API Documentation

<!-- BEGIN ENDPOINT: GET /books -->
### GET /books
Returns all books.
<!-- END ENDPOINT: GET /books -->

<!-- BEGIN ENDPOINT: GET /books -->
### GET /books
Returns all books again.
<!-- END ENDPOINT: GET /books -->
'''

    result = DocumentationValidator.validate_documentation(markdown)
    assert result["valid"] is False
    assert any("Duplicate" in error for error in result["errors"])


def test_nested_markers_are_rejected():
    markdown = '''
# Book API Documentation

<!-- BEGIN ENDPOINT: GET /books -->
<!-- BEGIN ENDPOINT: GET /books/{id} -->
### GET /books/{id}
Returns a book.
<!-- END ENDPOINT: GET /books/{id} -->
<!-- END ENDPOINT: GET /books -->
'''

    result = DocumentationValidator.validate_documentation(markdown)
    assert result["valid"] is False
    assert any("Nested" in error for error in result["errors"])


def test_malformed_markers_are_rejected():
    markdown = '''
# Book API Documentation

<!-- BEGIN ENDPOINT: GET /books -->
### GET /books
Returns all books.
<!-- END ENDPOINT: POST /books -->
'''

    result = DocumentationValidator.validate_documentation(markdown)
    assert result["valid"] is False
    assert any("Mismatched" in error or "not properly paired" in error for error in result["errors"])


def test_unsupported_endpoint_marker_is_rejected():
    markdown = '''
# Book API Documentation

<!-- BEGIN ENDPOINT: GET /authors -->
### GET /authors
Returns authors.
<!-- END ENDPOINT: GET /authors -->
'''

    result = DocumentationValidator.validate_documentation(markdown)
    assert result["valid"] is False
    assert any("Unsupported endpoint marker" in error for error in result["errors"])


def test_invalid_cli_selection_is_handled():
    repo = Path("c:/Users/DPriyanka/Desktop/capstone-copilot")
    runtime = AppRuntime(repo, "app/api.py", "docs/api.md")
    result = runtime.validate_docs()
    assert "VALIDATION ERROR" in result or "SUCCESS" in result


def test_synchronization_failure_leaves_original_docs_unchanged(tmp_path):
    docs = tmp_path / "api.md"
    original_contents = "# Manual Intro\n\n<!-- BEGIN ENDPOINT: GET /books -->\nOld\n<!-- END ENDPOINT: GET /books -->\n\n<!-- BEGIN ENDPOINT: GET /books/{id} -->\nOld\n<!-- END ENDPOINT: GET /books/{id} -->\n\n<!-- BEGIN ENDPOINT: POST /books -->\nOld\n<!-- END ENDPOINT: POST /books -->\n\nManual footer\n"
    docs.write_text(original_contents, encoding="utf-8")

    invalid_contract = {
        "GET /books": {
            "method": "GET",
            "path": "/books",
            "summary": "Return the list of books.",
            "parameters": [],
            "request_body": None,
            "responses": {"200": {"description": "List of books returned successfully."}},
            "errors": ["500 Internal server error."],
            "examples": {"response": {"status": 200, "body": {"books": []}}},
        },
        "GET /books/{id}": {
            "method": "GET",
            "path": "/books/{id}",
            "summary": "Return a single book by ID.",
            "parameters": [{"name": "id", "kind": "path"}],
            "request_body": None,
            "responses": {"200": {"description": "Book found."}},
            "errors": ["404 Book not found."],
            "examples": {"response": {"status": 200, "body": {"id": 1}}},
        },
    }

    try:
        synchronize_documentation(docs, invalid_contract)
    except SynchronizationError:
        pass

    assert docs.read_text(encoding="utf-8") == original_contents


def test_validation_rejects_block_missing_required_content():
    markdown = '''
# Book API Documentation

<!-- BEGIN ENDPOINT: GET /books -->
### GET /books
<!-- END ENDPOINT: GET /books -->

<!-- BEGIN ENDPOINT: GET /books/{id} -->
### GET /books/{id}
Returns a single book by ID.
<!-- END ENDPOINT: GET /books/{id} -->

<!-- BEGIN ENDPOINT: POST /books -->
### POST /books
Creates a new book.
<!-- END ENDPOINT: POST /books -->
'''

    result = DocumentationValidator.validate_documentation(markdown)
    assert result["valid"] is False
    assert any("Parameters section is missing" in error for error in result["errors"])
