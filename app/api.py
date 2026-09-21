"""Source-of-truth API definitions for the Book API documentation sync project.

This file intentionally defines only the supported endpoints and uses a simple
route decorator convention so the AST extractor can inspect the contract without
executing the module.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class RouteSpec:
    """Simple metadata container for a route contract."""

    def __init__(
        self,
        method: str,
        path: str,
        summary: str,
        path_params: Optional[list[str]] = None,
        request_body: Optional[dict[str, Any]] = None,
        responses: Optional[dict[str, Any]] = None,
        errors: Optional[list[str]] = None,
        examples: Optional[dict[str, Any]] = None,
    ) -> None:
        self.method = method
        self.path = path
        self.summary = summary
        self.path_params = path_params or []
        self.request_body = request_body or {}
        self.responses = responses or {}
        self.errors = errors or []
        self.examples = examples or {}


def route(method: str, path: str):
    """Decorator-like route marker for AST inspection.

    The decorator does not create an HTTP server or execute application logic.
    it is only used as a source-code convention for documentation sync.
    """

    def decorator(func):
        func.__route__ = {
            "method": method,
            "path": path,
        }
        return func

    return decorator


@route("GET", "/books")
def get_books():
    """Return all books."""
    return {"books": []}


@route("GET", "/books/{id}")
def get_book(book_id: int):
    """Return a single book by ID."""
    return {"book_id": book_id}


@route("POST", "/books")
def create_book(book: dict):
    """Create a new book record."""
    return {"created": True, "book": book}


BOOK_API_CONTRACT = {
    "GET /books": RouteSpec(
        method="GET",
        path="/books",
        summary="Return all books.",
        responses={
            "200": {
                "description": "List of books returned successfully.",
                "schema": {"type": "array", "items": {"type": "object"}},
            },
            "500": {"description": "Internal server error."},
        },
        errors=["500 Internal server error."],
        examples={
            "request": None,
            "response": {
                "status": 200,
                "body": {"books": [{"id": 1, "title": "Example Book"}]},
            },
        },
    ),
    "GET /books/{id}": RouteSpec(
        method="GET",
        path="/books/{id}",
        summary="Return a single book by ID.",
        path_params=["id"],
        responses={
            "200": {
                "description": "Book found.",
                "schema": {"type": "object"},
            },
            "404": {"description": "Book not found."},
            "500": {"description": "Internal server error."},
        },
        errors=["404 Book not found.", "500 Internal server error."],
        examples={
            "request": None,
            "response": {
                "status": 200,
                "body": {"id": 1, "title": "Example Book"},
            },
        },
    ),
    "POST /books": RouteSpec(
        method="POST",
        path="/books",
        summary="Create a new book record.",
        request_body={
            "type": "object",
            "required": ["title"],
            "properties": {"title": {"type": "string"}, "author": {"type": "string"}},
        },
        responses={
            "201": {
                "description": "Book created successfully.",
                "schema": {"type": "object"},
            },
            "400": {"description": "Invalid book payload."},
            "500": {"description": "Internal server error."},
        },
        errors=["400 Invalid book payload.", "500 Internal server error."],
        examples={
            "request": {
                "method": "POST",
                "body": {"title": "Example Book", "author": "Jane Author"},
            },
            "response": {
                "status": 201,
                "body": {"id": 1, "title": "Example Book", "author": "Jane Author"},
            },
        },
    ),
}
