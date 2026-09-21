from app.cli import AppRuntime


def test_cli_runtime_success_message(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "app").mkdir()
    (repo / "docs").mkdir()
    api = repo / "app" / "api.py"
    api.write_text(
        '''
@route("GET", "/books")
def get_books():
    """Return the list of books."""
    return {"books": []}

@route("GET", "/books/{id}")
def get_book(book_id: int):
    """Return a single book by ID."""
    return {"book_id": book_id}

@route("POST", "/books")
def create_book(book: dict):
    """Create a new book record."""
    return {"created": True, "book": book}
''',
        encoding="utf-8",
    )

    docs = repo / "docs" / "api.md"
    docs.write_text(
        '''# Book API Documentation\n\n<!-- BEGIN ENDPOINT: GET /books -->\n### GET /books\nReturns all books.\n\n#### Parameters\nNone\n\n#### Request Body\nNone\n\n#### Responses\n- Status `200`: List of books returned successfully.\n\n#### Error Responses\n- 500 Internal server error.\n\n#### Examples\nResponse example:\n```json\n{"status":200,"body":{"books":[]}}\n```\n<!-- END ENDPOINT: GET /books -->\n\n<!-- BEGIN ENDPOINT: GET /books/{id} -->\n### GET /books/{id}\nReturns a single book by ID.\n\n#### Parameters\n- `id`: path\n\n#### Request Body\nNone\n\n#### Responses\n- Status `200`: Book found.\n\n#### Error Responses\n- 404 Book not found.\n\n#### Examples\nResponse example:\n```json\n{"status":200,"body":{"id":1}}\n```\n<!-- END ENDPOINT: GET /books/{id} -->\n\n<!-- BEGIN ENDPOINT: POST /books -->\n### POST /books\nCreates a new book.\n\n#### Parameters\nNone\n\n#### Request Body\n```json\n{"type":"object"}\n```\n\n#### Responses\n- Status `201`: Book created successfully.\n\n#### Error Responses\n- 400 Invalid book payload.\n\n#### Examples\nRequest example:\n```json\n{"method":"POST","body":{"title":"Example"}}\n```\n<!-- END ENDPOINT: POST /books -->\n''',
        encoding="utf-8",
    )

    import subprocess

    subprocess.run(["git", "init"], cwd=str(repo), check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["git", "config", "user.name", "Tester"], cwd=str(repo), check=True)
    subprocess.run(["git", "config", "user.email", "tester@example.com"], cwd=str(repo), check=True)
    subprocess.run(["git", "add", "app/api.py", "docs/api.md"], cwd=str(repo), check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=str(repo), check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # make the source different from HEAD
    api.write_text(
        '''
@route("GET", "/books")
def get_books():
    """Return the list of books."""
    return {"books": []}

@route("GET", "/books/{id}")
def get_book(book_id: int):
    """Return a single book by ID."""
    return {"book_id": book_id}

@route("POST", "/books")
def create_book(book: dict):
    """Create a new book record."""
    return {"created": True, "book": book, "status": "created"}
''',
        encoding="utf-8",
    )

    runtime = AppRuntime(repo, "app/api.py", "docs/api.md")
    result = runtime.run_sync()
    assert result.startswith("SUCCESS")
