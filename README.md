# LaTeX Renderer Service

An asynchronous LaTeX rendering service that converts LaTeX documents to PDF.

## Prerequisites

- Python 3.12 or higher
- Redis server
- LuaLaTeX (LaTeX distribution with LuaTeX engine)

## Docker

Either build the service yourself or use the pre-built image from Docker Hub.

Compose:

```yaml
services:
  latex-renderer:
    image: sbroeckling/skillpage-latex-renderer
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379/0
      - DEBUG=False
    healthcheck:
      test: curl --fail http://localhost:4343 || exit 1
      interval: 5s
    depends_on:
      - redis
```

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd skillpage-latex-renderer
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

## Environment Variables

Create a `.env` file in the project root with the following variables:

```env
REDIS_URL=redis://localhost:6379/0
DEBUG=False
```

## Running the Service

1. Start the Redis server:
   ```bash
   redis-server
   ```

2. Start the LaTeX renderer service:
   ```bash
   uvicorn main:app --reload
   ```
   The service will be available at `http://localhost:8000`

## API Documentation

### 1. Submit a LaTeX Document

**Endpoint:** `POST /document`

Submit LaTeX files for rendering. The main LaTeX file must be named `main.tex`.

**Request:**
- Content-Type: `multipart/form-data`
- Form fields:
  - `document`: (required) All files for the render (.tex, .cls etc.). Must contain a `main.tex` file.
  - `image`: (optional) Additional image files referenced in the LaTeX document
- Header:
  - `X-Webhook-Url`: (optional) URL to receive webhook notifications about the document's status

**Response (202 Accepted):**
```json
{
  "message": "Document received",
  "document_id": "<unique-document-id>"
}
```

### 2. Check Document Status

**Endpoint:** `GET /state/{document_id}`

Check the status of a submitted document.

**Response (200 OK):**
```json
{
  "document_id": "<document-id>",
  "state": "pending|processing|success|failed-latex-error|failed-no-main-tex|non-existent"
}
```

### 3. Download Rendered PDF

**Endpoint:** `GET /document/{document_id}`

Download the rendered PDF file if processing is complete.

**Responses:**
- 200 OK: Returns the PDF file
- 202 Accepted: Document is still being processed
- 404 Not Found: Document ID does not exist
- 500 Internal Server Error: Error during PDF generation

## Example Usage

### Using cURL

1. Submit a LaTeX document:
   ```bash
   curl -X POST -F "document=@main.tex" -F "image=@figure1.png" http://localhost:8000/document
   ```
   Response:
   ```json
   {
     "message": "Document received",
     "document_id": "550e8400-e29b-41d4-a716-446655440000"
   }
   ```

2. Check status:
   ```bash
   curl http://localhost:8000/state/550e8400-e29b-41d4-a716-446655440000
   ```
   Response when complete:
   ```json
   {
     "document_id": "550e8400-e29b-41d4-a716-446655440000",
     "state": "success"
   }
   ```

3. Download the PDF:
   ```bash
   curl -o output.pdf http://localhost:8000/document/550e8400-e29b-41d4-a716-446655440000
   ```

4. (Optional) Submit a LaTeX document with webhook:
   ```bash
   curl --header "X-Webhook-Url: https://example.com/webhook" -X POST -F "document=@main.tex" -F "image=@figure1.png" http://localhost:8000/document
   ```
   Response:
   ```json
   {
     "message": "Document received",
     "document_id": "550e8400-e29b-41d4-a716-446655440000"
   }
   ```
## Webhook

The optional `X-Webhook-Url` header can be used to receive webhook notifications about the document's status.

The webhook will be called with a POST request with the following JSON body:
```json
{
  "document_id": "<document-id>",
  "state": "pending|processing|success|failed-latex-error|failed-no-main-tex|non-existent"
}
```

## Error Handling

The service returns appropriate HTTP status codes and error messages:

- `400 Bad Request`: Invalid request format
- `404 Not Found`: Document ID does not exist
- `500 Internal Server Error`: Server error during processing

## License

[MIT License](LICENSE)

