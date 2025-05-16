from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date

class ReviewRequest(BaseModel):
    company_code: str
    start_date: date
    last_date: date
    
class ReviewResponse(BaseModel):
    overall_review: Dict[str, Any]
    reviews: List[Dict[str, Any]] 