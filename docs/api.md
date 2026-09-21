# Book API Documentation

This file contains approved manual documentation. The generated endpoint sections are kept in the blocks below and are synchronized automatically.

<!-- BEGIN ENDPOINT: GET /books -->
### GET /books

Return all books.

#### Parameters

None

#### Request Body

None

#### Responses

- Status `200`: List of books returned successfully.
- Status `500`: Internal server error.

#### Error Responses

- 500 Internal server error.

#### Examples

Response example:
```json
{
  "body": {
    "books": [
      {
        "id": 1,
        "title": "Example Book"
      }
    ]
  },
  "status": 200
}
```

<!-- END ENDPOINT: GET /books -->






<!-- BEGIN ENDPOINT: GET /books/{id} -->
### GET /books/{id}

Return a single book by ID.

#### Parameters

- `id`: path

#### Request Body

None

#### Responses

- Status `200`: Book found.
- Status `404`: Book not found.
- Status `500`: Internal server error.

#### Error Responses

- 404 Book not found.
- 500 Internal server error.

#### Examples

Response example:
```json
{
  "body": {
    "id": 1,
    "title": "Example Book"
  },
  "status": 200
}
```

<!-- END ENDPOINT: GET /books/{id} -->






<!-- BEGIN ENDPOINT: POST /books -->
### POST /books

Create a new book record.

#### Parameters

- `book`: positional_or_keyword

#### Request Body

```json
{
  "properties": {
    "author": {
      "type": "string"
    },
    "title": {
      "type": "string"
    }
  },
  "required": [
    "title"
  ],
  "type": "object"
}
```

#### Responses

- Status `201`: Book created successfully.
- Status `400`: Invalid book payload.
- Status `500`: Internal server error.

#### Error Responses

- 400 Invalid book payload.
- 500 Internal server error.

#### Examples

Request example:
```json
{
  "body": {
    "author": "Jane Author",
    "title": "Example Book"
  },
  "method": "POST"
}
```
Response example:
```json
{
  "body": {
    "author": "Jane Author",
    "id": 1,
    "title": "Example Book"
  },
  "status": 201
}
```

<!-- END ENDPOINT: POST /books -->






## Notes

This section is preserved manually and should not be overwritten by the synchronizer.
