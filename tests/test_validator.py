from app.validator import DocumentationValidator


def test_validator_accepts_well_formed_documentation():
    markdown = '''
# Book API Documentation

<!-- BEGIN ENDPOINT: GET /books -->
### GET /books
Returns all books.

#### Parameters
None

#### Request Body
None

#### Responses
- Status `200`: List of books returned successfully.

#### Error Responses
- 500 Internal server error.

#### Examples
Response example:
```json
{"status":200,"body":{"books":[]}}
```
<!-- END ENDPOINT: GET /books -->

<!-- BEGIN ENDPOINT: GET /books/{id} -->
### GET /books/{id}
Returns a single book by ID.

#### Parameters
- `id`: path

#### Request Body
None

#### Responses
- Status `200`: Book found.

#### Error Responses
- 404 Book not found.

#### Examples
Response example:
```json
{"status":200,"body":{"id":1}}
```
<!-- END ENDPOINT: GET /books/{id} -->

<!-- BEGIN ENDPOINT: POST /books -->
### POST /books
Creates a new book.

#### Parameters
None

#### Request Body
```json
{"type":"object"}
```

#### Responses
- Status `201`: Book created successfully.

#### Error Responses
- 400 Invalid book payload.

#### Examples
Request example:
```json
{"method":"POST","body":{"title":"Example"}}
```
<!-- END ENDPOINT: POST /books -->
'''
    result = DocumentationValidator.validate_documentation(markdown)
    assert result["valid"] is True


def test_validator_rejects_missing_endpoint_block():
    markdown = '''
# Book API Documentation

<!-- BEGIN ENDPOINT: GET /books -->
### GET /books
Returns all books.
<!-- END ENDPOINT: GET /books -->
'''
    result = DocumentationValidator.validate_documentation(markdown)
    assert result["valid"] is False
    assert any("Missing endpoint block" in err for err in result["errors"])
