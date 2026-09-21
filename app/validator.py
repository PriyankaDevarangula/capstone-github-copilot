"""Validation for generated documentation blocks."""

from __future__ import annotations

import re
from typing import Any

SUPPORTED_ENDPOINT_ORDER = [
    "GET /books",
    "GET /books/{id}",
    "POST /books",
]


class ValidationError(ValueError):
    """Raised for invalid documentation structure."""


class DocumentationValidator:
    """Validate generated endpoint blocks in docs/api.md."""

    @staticmethod
    def _expected_method_path(endpoint: str) -> str:
        if endpoint == "GET /books":
            return "### GET /books"
        if endpoint == "GET /books/{id}":
            return "### GET /books/{id}"
        if endpoint == "POST /books":
            return "### POST /books"
        return f"### {endpoint}"

    @staticmethod
    def _block_section(block: str, header: str) -> str:
        pattern = re.compile(rf"{re.escape(header)}\s*\n(.*?)(?=\n#### |\Z)", re.S)
        match = pattern.search(block)
        if not match:
            return ""
        return match.group(1).strip()

    @staticmethod
    def _check_block_content(markdown: str, endpoint: str) -> list[str]:
        begin = f"<!-- BEGIN ENDPOINT: {endpoint} -->"
        end = f"<!-- END ENDPOINT: {endpoint} -->"
        start_index = markdown.find(begin)
        end_index = markdown.find(end)
        if start_index == -1 or end_index == -1:
            return []

        block = markdown[start_index:end_index + len(end)]
        errors: list[str] = []
        expected_heading = DocumentationValidator._expected_method_path(endpoint)
        if expected_heading not in block:
            errors.append(f"Endpoint heading is missing or incorrect for {endpoint}.")

        heading_match = re.search(r"###\s+.*?\n\s*(.*?)(?=\n#### |\n<!-- END ENDPOINT)", block, flags=re.S)
        if not heading_match or not heading_match.group(1).strip():
            errors.append(f"Summary/description is missing for {endpoint}.")

        params_section = DocumentationValidator._block_section(block, "#### Parameters")
        if endpoint == "GET /books/{id}":
            if not params_section or "id" not in params_section.lower():
                errors.append(f"Parameters section is missing for {endpoint}.")
        elif not params_section:
            errors.append(f"Parameters section is missing for {endpoint}.")
        elif "None" not in params_section and "- `" not in params_section:
            errors.append(f"Parameters section is not documented correctly for {endpoint}.")

        request_body_section = DocumentationValidator._block_section(block, "#### Request Body")
        if not request_body_section:
            errors.append(f"Request Body section is missing for {endpoint}.")
        elif endpoint in {"GET /books", "GET /books/{id}"} and "None" not in request_body_section:
            errors.append(f"Request Body section is incorrectly documented for {endpoint}.")
        elif endpoint == "POST /books" and "```json" not in request_body_section and "None" not in request_body_section:
            errors.append(f"Request Body section is not properly documented for {endpoint}.")

        responses_section = DocumentationValidator._block_section(block, "#### Responses")
        if not responses_section or "- Status `" not in responses_section:
            errors.append(f"Responses section is missing or incomplete for {endpoint}.")

        error_section = DocumentationValidator._block_section(block, "#### Error Responses")
        if not error_section or "- " not in error_section:
            errors.append(f"Error Responses section is missing or incomplete for {endpoint}.")

        examples_section = DocumentationValidator._block_section(block, "#### Examples")
        if not examples_section:
            errors.append(f"Examples section is missing for {endpoint}.")
        elif "None" not in examples_section and "Request example:" not in examples_section and "Response example:" not in examples_section:
            errors.append(f"Examples section is not documented correctly for {endpoint}.")

        return errors

    @staticmethod
    def validate_documentation(markdown: str) -> dict[str, Any]:
        """Return validation result with pass/fail details."""
        result: dict[str, Any] = {"valid": True, "errors": []}

        marker_pattern = re.compile(r"<!--\s*BEGIN ENDPOINT: ([^\n]+?)\s*-->")
        begin_markers = marker_pattern.findall(markdown)

        if not begin_markers:
            result["valid"] = False
            result["errors"].append("No endpoint markers were found.")
            return result

        start_pattern = re.compile(r"<!--\s*BEGIN ENDPOINT: ([^\n]+?)\s*-->")
        end_pattern = re.compile(r"<!--\s*END ENDPOINT: ([^\n]+?)\s*-->")

        matched_starts = start_pattern.findall(markdown)
        matched_ends = end_pattern.findall(markdown)

        if len(matched_starts) != len(matched_ends):
            result["valid"] = False
            result["errors"].append("Endpoint markers are not properly paired.")
            return result

        for endpoint in matched_starts:
            if endpoint not in SUPPORTED_ENDPOINT_ORDER:
                result["valid"] = False
                result["errors"].append(f"Unsupported endpoint marker found: {endpoint}")

        for endpoint in SUPPORTED_ENDPOINT_ORDER:
            begin = f"<!-- BEGIN ENDPOINT: {endpoint} -->"
            end = f"<!-- END ENDPOINT: {endpoint} -->"
            if begin not in markdown or end not in markdown:
                result["valid"] = False
                result["errors"].append(f"Missing endpoint block for {endpoint}.")

        seen_order = []
        for endpoint in SUPPORTED_ENDPOINT_ORDER:
            begin = f"<!-- BEGIN ENDPOINT: {endpoint} -->"
            end = f"<!-- END ENDPOINT: {endpoint} -->"
            begin_index = markdown.find(begin)
            end_index = markdown.find(end)
            if begin_index == -1 or end_index == -1:
                continue
            if begin_index > end_index:
                result["valid"] = False
                result["errors"].append(f"Endpoint block order is invalid for {endpoint}.")
            seen_order.append(endpoint)

        if seen_order != SUPPORTED_ENDPOINT_ORDER:
            result["valid"] = False
            result["errors"].append("Endpoint blocks are not in the required order.")

        for endpoint in SUPPORTED_ENDPOINT_ORDER:
            begin_count = markdown.count(f"<!-- BEGIN ENDPOINT: {endpoint} -->")
            end_count = markdown.count(f"<!-- END ENDPOINT: {endpoint} -->")
            if begin_count > 1 or end_count > 1:
                result["valid"] = False
                result["errors"].append(f"Duplicate endpoint markers found for {endpoint}.")

        marker_sequence = re.findall(r"<!--\s*(BEGIN|END) ENDPOINT: ([^\n]+?)\s*-->", markdown)
        stack: list[str] = []
        for action, endpoint in marker_sequence:
            if action == "BEGIN":
                if stack:
                    result["valid"] = False
                    result["errors"].append(f"Nested endpoint markers detected for {endpoint}.")
                stack.append(endpoint)
            elif action == "END":
                if not stack:
                    result["valid"] = False
                    result["errors"].append(f"Mismatched endpoint marker found for {endpoint}.")
                    continue
                last = stack.pop()
                if last != endpoint:
                    result["valid"] = False
                    result["errors"].append(f"Mismatched endpoint marker found for {endpoint}.")

        if stack:
            result["valid"] = False
            result["errors"].append("Unclosed endpoint markers were found.")

        for endpoint in SUPPORTED_ENDPOINT_ORDER:
            block_errors = DocumentationValidator._check_block_content(markdown, endpoint)
            for error in block_errors:
                result["valid"] = False
                result["errors"].append(error)

        if not result["valid"]:
            return result

        return result
