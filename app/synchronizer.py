"""Safely synchronize generated endpoint documentation blocks."""

from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

from app.validator import DocumentationValidator

SUPPORTED_ENDPOINT_ORDER = [
    "GET /books",
    "GET /books/{id}",
    "POST /books",
]


class SynchronizationError(ValueError):
    """Raised when documentation cannot be synchronized safely."""


def _render_json(value: Any) -> str:
    """Render a JSON-like Python value using deterministic standard-library formatting."""
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)


def _build_endpoint_block(endpoint: str, api_contract: dict[str, Any]) -> str:
    route = api_contract.get(endpoint)
    if route is None:
        raise SynchronizationError(f"Unsupported endpoint in contract: {endpoint}")

    method = route["method"]
    path = route["path"]
    summary = route["summary"]
    params = route.get("parameters", [])
    request_body = route.get("request_body")
    responses = route.get("responses", {})
    errors = route.get("errors", [])
    examples = route.get("examples", {})

    lines = [
        f"<!-- BEGIN ENDPOINT: {endpoint} -->",
        f"### {method} {path}",
        "",
        summary,
        "",
    ]

    lines.append("#### Parameters")
    lines.append("")
    if params:
        for param in params:
            lines.append(f"- `{param['name']}`: {param.get('kind', 'parameter')}")
    else:
        lines.append("None")
    lines.append("")

    lines.append("#### Request Body")
    lines.append("")
    if request_body:
        lines.append("```json")
        lines.append(_render_json(request_body))
        lines.append("```")
    else:
        lines.append("None")
    lines.append("")

    lines.append("#### Responses")
    lines.append("")
    for status, payload in responses.items():
        description = payload.get("description", "")
        lines.append(f"- Status `{status}`: {description}")
    lines.append("")

    if errors:
        lines.append("#### Error Responses")
        lines.append("")
        for error in errors:
            lines.append(f"- {error}")
        lines.append("")
    else:
        lines.append("#### Error Responses")
        lines.append("")
        lines.append("None")
        lines.append("")

    if examples:
        lines.append("#### Examples")
        lines.append("")
        if "request" in examples and examples["request"] is not None:
            lines.append("Request example:")
            lines.append("```json")
            lines.append(_render_json(examples["request"]))
            lines.append("```")
        if "response" in examples and examples["response"] is not None:
            lines.append("Response example:")
            lines.append("```json")
            lines.append(_render_json(examples["response"]))
            lines.append("```")
        if "request" not in examples and "response" not in examples:
            lines.append("None")
        lines.append("")
    else:
        lines.append("#### Examples")
        lines.append("")
        lines.append("None")
        lines.append("")

    lines.append(f"<!-- END ENDPOINT: {endpoint} -->")
    return "\n".join(lines) + "\n"


def synchronize_documentation(doc_path: str | Path, api_contract: dict[str, Any]) -> str:
    """Synchronize docs/api.md while preserving all content outside endpoint blocks."""
    path = Path(doc_path)
    if not path.exists():
        raise SynchronizationError(f"Documentation file is missing: {path}")

    try:
        original = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SynchronizationError(f"Unable to read documentation file: {exc}") from exc

    begin_pattern = re.compile(r"<!--\s*BEGIN ENDPOINT: ([^\n]+?)\s*-->")
    end_pattern = re.compile(r"<!--\s*END ENDPOINT: ([^\n]+?)\s*-->")
    begins = begin_pattern.findall(original)
    ends = end_pattern.findall(original)

    if len(begins) != len(ends):
        raise SynchronizationError("Documentation markers are not properly paired.")

    if len(begins) != 3:
        raise SynchronizationError("Exactly three endpoint blocks are required.")

    for endpoint in SUPPORTED_ENDPOINT_ORDER:
        begin_tag = f"<!-- BEGIN ENDPOINT: {endpoint} -->"
        end_tag = f"<!-- END ENDPOINT: {endpoint} -->"
        if begin_tag not in original or end_tag not in original:
            raise SynchronizationError(f"Required endpoint block missing: {endpoint}")

    if begins != SUPPORTED_ENDPOINT_ORDER:
        raise SynchronizationError("Endpoint blocks are not in the required order.")

    if len(set(begins)) != len(begins):
        raise SynchronizationError("Duplicate endpoint markers found.")

    generated_blocks = []
    for endpoint in SUPPORTED_ENDPOINT_ORDER:
        generated_blocks.append(_build_endpoint_block(endpoint, api_contract))

    new_document = original
    for endpoint, block in zip(SUPPORTED_ENDPOINT_ORDER, generated_blocks):
        begin_tag = f"<!-- BEGIN ENDPOINT: {endpoint} -->"
        end_tag = f"<!-- END ENDPOINT: {endpoint} -->"
        start = new_document.find(begin_tag)
        end = new_document.find(end_tag)
        if start == -1 or end == -1 or start > end:
            raise SynchronizationError(f"Malformed endpoint block for {endpoint}.")
        end_of_block = end + len(end_tag)
        replacement = block
        new_document = new_document[:start] + replacement + new_document[end_of_block:]

    validation = DocumentationValidator.validate_documentation(new_document)
    if not validation["valid"]:
        raise SynchronizationError("; ".join(validation["errors"]))

    return new_document


def write_document_atomically(doc_path: str | Path, content: str) -> None:
    """Atomically replace the documentation file after validating the complete content."""
    path = Path(doc_path)
    validation = DocumentationValidator.validate_documentation(content)
    if not validation["valid"]:
        raise SynchronizationError("; ".join(validation["errors"]))

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=str(path.parent),
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())

        os.replace(temp_path, path)
    except OSError as exc:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink(missing_ok=True)
        raise SynchronizationError(f"Unable to write documentation file: {exc}") from exc
    except Exception as exc:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink(missing_ok=True)
        raise SynchronizationError(f"Unable to update documentation file: {exc}") from exc
    else:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink(missing_ok=True)
