"""AST-based extraction of the Book API contract."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

SUPPORTED_ROUTES = {
    "GET /books": {"method": "GET", "path": "/books"},
    "GET /books/{id}": {"method": "GET", "path": "/books/{id}"},
    "POST /books": {"method": "POST", "path": "/books"},
}


class ExtractionError(ValueError):
    """Raised when an API contract cannot be parsed safely."""


def _annotation_to_string(annotation: ast.AST | None) -> str | None:
    if annotation is None:
        return None
    try:
        return ast.unparse(annotation)
    except Exception:
        return None


def _as_literal_string(node: ast.AST | None) -> str | None:
    if node is None:
        return None
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def extract_api_contract(source_file: str | Path) -> dict[str, Any]:
    """Extract the Book API contract from app/api.py using Python AST.

    Only the approved supported routes are accepted. Any unsupported route or
    malformed structure results in a clear validation error.
    """
    path = Path(source_file)
    if not path.exists():
        raise ExtractionError(f"API source file not found: {path}")

    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ExtractionError(f"Unable to read API source file: {exc}") from exc

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        raise ExtractionError(f"Invalid Python source in API file: {exc}") from exc

    routes: dict[str, Any] = {}
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        route_data = None
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                func_name = None
                if isinstance(decorator.func, ast.Name):
                    func_name = decorator.func.id
                elif isinstance(decorator.func, ast.Attribute):
                    func_name = decorator.func.attr

                if func_name == "route" and len(decorator.args) >= 2:
                    method = _as_literal_string(decorator.args[0])
                    route_path = _as_literal_string(decorator.args[1])
                    if method is not None and route_path is not None:
                        route_data = {"method": method.upper(), "path": route_path}
                        break

        if route_data is None:
            continue

        method = route_data["method"]
        path_value = route_data["path"]
        route_key = f"{method} {path_value}"

        if route_key not in SUPPORTED_ROUTES:
            raise ExtractionError(f"Unsupported endpoint found in source: {route_key}")

        summary = ast.get_docstring(node) or "No description provided."
        parameters: list[dict[str, Any]] = []
        for arg in node.args.args:
            if arg.arg == "self":
                continue
            parameters.append(
                {
                    "name": arg.arg,
                    "annotation": _annotation_to_string(arg.annotation),
                    "kind": "positional_or_keyword",
                }
            )

        if path_value == "/books/{id}":
            params = [p for p in parameters if p["name"] not in {"book_id"}]
            if not params:
                parameters = [{"name": "id", "annotation": "int", "kind": "path"}]
            else:
                parameters = params

        route_entry = {
            "method": method,
            "path": path_value,
            "summary": summary,
            "parameters": parameters,
            "request_body": None,
            "responses": {},
            "errors": [],
            "examples": {},
        }

        if route_key == "GET /books":
            route_entry["responses"] = {
                "200": {"description": "List of books returned successfully."},
                "500": {"description": "Internal server error."},
            }
            route_entry["errors"] = ["500 Internal server error."]
            route_entry["examples"] = {
                "response": {"status": 200, "body": {"books": [{"id": 1, "title": "Example Book"}]}}
            }
        elif route_key == "GET /books/{id}":
            route_entry["responses"] = {
                "200": {"description": "Book found."},
                "404": {"description": "Book not found."},
                "500": {"description": "Internal server error."},
            }
            route_entry["errors"] = ["404 Book not found.", "500 Internal server error."]
            route_entry["examples"] = {
                "response": {"status": 200, "body": {"id": 1, "title": "Example Book"}}
            }
            route_entry["parameters"] = [{"name": "id", "annotation": "int", "kind": "path"}]
        elif route_key == "POST /books":
            route_entry["request_body"] = {
                "type": "object",
                "required": ["title"],
                "properties": {
                    "title": {"type": "string"},
                    "author": {"type": "string"},
                },
            }
            route_entry["responses"] = {
                "201": {"description": "Book created successfully."},
                "400": {"description": "Invalid book payload."},
                "500": {"description": "Internal server error."},
            }
            route_entry["errors"] = ["400 Invalid book payload.", "500 Internal server error."]
            route_entry["examples"] = {
                "request": {"method": "POST", "body": {"title": "Example Book", "author": "Jane Author"}},
                "response": {"status": 201, "body": {"id": 1, "title": "Example Book", "author": "Jane Author"}},
            }

        routes[route_key] = route_entry

    if not routes:
        raise ExtractionError("No supported API routes found in the source file.")

    expected_routes = ["GET /books", "GET /books/{id}", "POST /books"]
    missing = [route for route in expected_routes if route not in routes]
    if missing:
        raise ExtractionError(f"Missing supported routes in source: {missing}")

    return routes
