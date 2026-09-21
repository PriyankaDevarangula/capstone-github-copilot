from pathlib import Path

from app.extractor import extract_api_contract


def test_extract_api_contract_success(tmp_path):
    source = tmp_path / "api.py"
    source.write_text(
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

    contract = extract_api_contract(source)
    assert set(contract) == {"GET /books", "GET /books/{id}", "POST /books"}
    assert contract["GET /books"]["method"] == "GET"
    assert contract["GET /books/{id}"]["path"] == "/books/{id}"
    assert contract["POST /books"]["method"] == "POST"


def test_extract_api_contract_rejects_unsupported_route(tmp_path):
    source = tmp_path / "api.py"
    source.write_text(
        '''
@route("GET", "/authors")
def get_authors():
    """Not supported."""
    return []
''',
        encoding="utf-8",
    )

    try:
        extract_api_contract(source)
        assert False, "Expected ExtractionError"
    except Exception as exc:  # pragma: no cover - explicit failure check
        assert "Unsupported endpoint" in str(exc)
