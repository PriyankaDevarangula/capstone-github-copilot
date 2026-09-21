from pathlib import Path

from app.synchronizer import synchronize_documentation


def test_synchronize_documentation_updates_only_endpoint_blocks(tmp_path):
    docs = tmp_path / "api.md"
    docs.write_text(
        '''# Manual Intro\n\n<!-- BEGIN ENDPOINT: GET /books -->\nOld content\n<!-- END ENDPOINT: GET /books -->\n\n<!-- BEGIN ENDPOINT: GET /books/{id} -->\nOld content\n<!-- END ENDPOINT: GET /books/{id} -->\n\n<!-- BEGIN ENDPOINT: POST /books -->\nOld content\n<!-- END ENDPOINT: POST /books -->\n\nManual footer\n''',
        encoding="utf-8",
    )

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

    updated = synchronize_documentation(docs, contract)
    assert "Manual Intro" in updated
    assert "Manual footer" in updated
    assert "### GET /books" in updated
    assert "### GET /books/{id}" in updated
    assert "### POST /books" in updated
    assert "Old content" not in updated
