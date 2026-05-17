from pydantic import BaseModel

class CrawlRequest(BaseModel):
    url: str
    max_pages: int