from fastapi import APIRouter, HTTPException
from app.schema.chatinput import ReviewRequest, ReviewResponse
from app.schema.review_model import Model
from app.utils.playwright_utils import fetch_cookies, robust_request
from app.core.config import settings, logger
from curl_cffi import requests
import json
from datetime import datetime

ReviewRouter = APIRouter()

@ReviewRouter.post("/reviews", response_model=ReviewResponse)
async def get_reviews(request: ReviewRequest):
    try:
        if not request.start_date or not request.last_date:
            logger.info("Rejected request: start_date and last_date must be provided.")
            raise HTTPException(status_code=400, detail="start_date and last_date must be provided.")
        if request.start_date < request.last_date:
            logger.info("Rejected request: start_date must be >= last_date.")
            raise HTTPException(status_code=400, detail="start_date must be after or equal to last_date.")

        cookies = await fetch_cookies()
        logger.info(f"Cookies collected and Started scraping {request.company_code}")
        
        headers = {
            "User-Agent": settings.User_Agent,
            "next-router-state-tree": settings.next_router_state_tree,
            "rsc": settings.rsc,
        }

        overall_review = {}
        all_reviews = []
        extracted_data = None

        PAGE = 1
        reached_cutoff = False

        while not reached_cutoff:
            REVIEWS_URL = (
                f"https://www.teamblind.com/company/{request.company_code}/reviews?page={PAGE}"
            )
            logger.info(f"Fetching {REVIEWS_URL}")

            resp = await robust_request(
                REVIEWS_URL,
                headers=headers,
                #cookies=cookies,
            )

            if resp and resp.text:
                raw_output_string = resp.text
                lines = raw_output_string.splitlines()

                for line in lines:
                    stripped_line = line.strip()
                    if stripped_line.startswith("2:"):
                        extracted_data = stripped_line[2:].strip()
                        break
                if not extracted_data:
                    logger.error(f"No data found in response for page {PAGE}.")
                    raise HTTPException(status_code=404, detail=f"No data found in response for page {PAGE}.")
            else:
                logger.error(f"Failed to retrieve content or content is empty for page {PAGE}.")
                raise HTTPException(status_code=502, detail=f"Failed to retrieve content or content is empty for page {PAGE}.")

            try:
                data = json.loads(extracted_data)
            except Exception as e:
                logger.error(f"JSON decode error: {e}")
                raise HTTPException(status_code=500, detail="Failed to parse review data.")

            try:
                overall_review = data[0][3]["children"][0][3]
                reviews = data[0][3]["children"][1][3]["children"][3]["reviews"]["list"]
            except Exception as e:
                logger.error(f"Data structure error: {e}")
                raise HTTPException(status_code=500, detail="Unexpected data structure in review response.")

            if reviews:
                for review in reviews:
                    review_obj = Model(**review).model_dump()
                    created_at = datetime.fromisoformat(review_obj["createdAt"].replace("Z", "+00:00")).date()
                    # Include only reviews within the requested date range
                    if request.last_date <= created_at <= request.start_date:
                        all_reviews.append(review_obj)
                # Check last review's createdAt for stopping condition
                last_review_date = datetime.fromisoformat(reviews[-1]["createdAt"].replace("Z", "+00:00")).date()
                if last_review_date < request.last_date:
                    reached_cutoff = True
                else:
                    PAGE += 1
            else:
                logger.info(f"No reviews found on page {PAGE}.")
                break

        return ReviewResponse(
            overall_review=overall_review,
            reviews=all_reviews
        )

    except Exception as e:
        logger.error(f"Error fetching reviews: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")