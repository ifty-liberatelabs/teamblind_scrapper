
# TeamBlind Review Scraper
A robust, container-ready FastAPI microservice that scrapes employee reviews from [TeamBlind.com](https://www.teamblind.com/) for any company, using resilient session management and a date-range query interface.

---

## 🚀 Features

- **Scrape reviews by company code** for any employer on TeamBlind
- **Specify a date range** (`start_date`, `last_date`) to fetch reviews only within that window
- **Automatic session and cookie handling** with Playwright and curl_cffi
- **Auto-relogin and retry** on session expiry or network error (robust_request)
- **Modern async FastAPI backend**—easily deployable and scalable
- **Structured API response:** overall company review stats + detailed review list

---


## ⚡️ Quickstart

### 1. **Clone and Install**

```bash
git clone https://github.com/yourusername/teamblind-data-scraper.git
cd teamblind-data-scraper
pip install -r requirements.txt
````

### 2. **Configure Environment**

* Edit `app/core/config.py` with your credentials:

  * `TEAMBLIND_USER_EMAIL`
  * `TEAMBLIND_USER_PASS`
  * Custom `User_Agent`, etc.

> **Never commit your real credentials to source control!**

### 3. **Run the Service**

```bash
uvicorn main:app --reload
```

Or use Docker:

```bash
docker-compose up --build
```

---

## 🔗 API Usage

### **POST** `/api/v1/reviews`

**Request Body:**

```json
{
  "company_code": "Synopsys",
  "start_date": "2024-01-01",
  "last_date": "2023-01-01"
}
```

* `company_code`: String, TeamBlind's URL alias for the company (e.g., `"Google"`, `"Meta"`, `"Synopsys"`)
* `start_date`: Fetch reviews **from this date** (inclusive, format: `YYYY-MM-DD`)
* `last_date`: Fetch reviews **down to this date** (inclusive)

**Response Example:**

```json
{
  "overall_review": {
    "companyName": "Synopsys",
    "companyUrlAlias": "Synopsys",
    "count": 393,
    "career": "3.1",
    "balance": "3.9",
    "compensation": "2.9",
    "culture": "3.5",
    "management": "3.2",
    "rating": "3.5"
  },
  "reviews": [
    {
      "overall": 4,
      "career": 4,
      "balance": 4,
      "compensation": 4,
      "culture": 4,
      "management": 4,
      "summary": "Good",
      "pros": "...",
      "cons": "...",
      "reasonResign": null,
      "createdAt": "2024-04-18T04:12:03.000Z"
    },
    ...
  ]
}
```

---

## 🛡️ Resilience and Retry

* **Auto-relogin:** If TeamBlind session expires, login is retried seamlessly.
* **Retry logic:** All review-fetch requests are wrapped for network and auth reliability.
* **Cookie storage:** Cookies are saved to `auth_state.json` for reuse.

---

## 🧰 Development & Customization

* All main logic is in `app/utils/playwright_utils.py` and `app/api/v1/reviews.py`
* To adjust scraping structure, see the JSON path in `reviews.py`
* For rate limits or proxies, extend the request logic as needed

---

## ❗ Disclaimer

* This tool is for educational, research, or authorized internal use only.
* Use responsibly and in accordance with TeamBlind’s Terms of Service.

---

