from app.api import BOOK_API_CONTRACT


def test_book_api_contract_has_supported_routes():
    expected = ["GET /books", "GET /books/{id}", "POST /books"]
    for route in expected:
        assert route in BOOK_API_CONTRACT
