Teamblind Data Scraper
=====================

This project is a FastAPI application for scraping data from Teamblind.

## Running the Application

You have two options to run the application:

### Option 1: Using Docker Compose

1. Make sure you have Docker and Docker Compose installed on your system
2. Create a `.env` file with the required environment variables (including `PORT`)
3. Run the following command:

```bash
docker compose up --build
```

This will build the Docker image and start the application. The API will be available at `http://localhost:$PORT`.

### Option 2: Running Directly with Uvicorn

1. Install the required dependencies (make sure you have Python installed)
2. Run the following command:

```bash
uvicorn main:app --reload
```

By default, this will start the server on `http://localhost:8000`. The `--reload` flag enables auto-reload on code changes, which is useful during development.

## Environment Variables

Create a `.env` file in the root directory, you can copy the `.env.example` file:
```env
PORT=8000
EMAIL=dummy.user@example.com
PASSWORD=dummypassword123
```

Make sure to replace the dummy credentials with your actual Teamblind account credentials.

## API Documentation

The main entrypoint is `main.py`.
API endpoints are available under `/api/v1/`.

Once the application is running, you can access:
- Interactive API documentation (Swagger UI) at `/docs`
- Alternative API documentation (ReDoc) at `/redoc`

## API Examples

### Scraping Company Reviews

**Endpoint**: `POST /api/v1/scrape`

**Input Example**:
```json
{
  "company_code": "Microsoft",
  "max_page": 2
}
```

**Parameters**:
- `company_code`: The company identifier from Teamblind (e.g., "Microsoft", "Google", etc.)
- `max_page`: Number of pages to scrape (must be greater than 0)

**Output Example**:
```json
{
  "overall_review": {
    "companyName": "Microsoft",
    "companyUrlAlias": "Microsoft",
    "count": 11174,
    "career": "3.5",
    "balance": "4.2",
    "compensation": "3.2",
    "culture": "3.9",
    "management": "3.5",
    "rating": "3.9"
  },
  "reviews": [
    {
      "overall": 3,
      "career": 3,
      "balance": 4,
      "compensation": 3,
      "culture": 4,
      "management": 3,
      "summary": "Great work life balance",
      "pros": "Great work life balance compared to other organizations in the same sector",
      "cons": "Compensation isn't as great compared to companies of other size",
      "reasonResign": null,
      "createdAt": "2025-04-29T04:48:06.000Z"
    }
  ]
}
```

The response includes:
1. `overall_review`: Aggregate statistics for the company
   - Company information
   - Average ratings across different categories
   - Total review count
2. `reviews`: Array of individual reviews with:
   - Individual category ratings
   - Summary, pros, and cons
   - Creation date
   - Reason for resignation (if provided)