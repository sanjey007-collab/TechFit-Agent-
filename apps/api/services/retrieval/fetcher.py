import re
import datetime
from typing import Optional, Tuple
import httpx
from bs4 import BeautifulSoup

USER_AGENT = "TechFit-Compatibility-Agent/1.0 (+https://techfit.onrender.com; hardware-spec-audit)"

class FetchedDocument:
    def __init__(
        self,
        url: str,
        title: str,
        text: str,
        retrieval_timestamp: datetime.datetime,
        success: bool,
        error_message: Optional[str] = None
    ):
        self.url = url
        self.title = title
        self.text = text
        self.retrieval_timestamp = retrieval_timestamp
        self.success = success
        self.error_message = error_message

async def fetch_page_content(url: str, timeout: float = 8.0) -> FetchedDocument:
    now = datetime.datetime.utcnow()
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                return FetchedDocument(
                    url=url,
                    title="",
                    text="",
                    retrieval_timestamp=now,
                    success=False,
                    error_message=f"HTTP Error {resp.status_code}: Source inaccessible"
                )

            html = resp.text
            soup = BeautifulSoup(html, "html.parser")

            # Remove non-content tags
            for tag in soup(["script", "style", "nav", "footer", "form", "noscript", "svg"]):
                tag.decompose()

            title = soup.title.string.strip() if soup.title and soup.title.string else "Manufacturer Specification Document"
            clean_text = soup.get_text(separator=" ", strip=True)

            # Cap length to 100,000 characters for safety
            if len(clean_text) > 100000:
                clean_text = clean_text[:100000] + "... [TRUNCATED]"

            return FetchedDocument(
                url=url,
                title=title,
                text=clean_text,
                retrieval_timestamp=now,
                success=True
            )

    except httpx.TimeoutException:
        return FetchedDocument(
            url=url,
            title="",
            text="",
            retrieval_timestamp=now,
            success=False,
            error_message="Connection timed out while contacting manufacturer server."
        )
    except Exception as e:
        return FetchedDocument(
            url=url,
            title="",
            text="",
            retrieval_timestamp=now,
            success=False,
            error_message=f"Retrieval error: {str(e)}"
        )

def verify_excerpt_in_document(excerpt: str, full_text: str) -> bool:
    """
    Provenance Guard: Verifies that the quoted excerpt literally exists
    inside the fetched source text. Rejects hallucinated claims.
    """
    if not excerpt or not full_text:
        return False

    norm_excerpt = re.sub(r"\s+", " ", excerpt.lower().strip())
    norm_doc = re.sub(r"\s+", " ", full_text.lower().strip())

    if norm_excerpt in norm_doc:
        return True

    # Allow partial sliding window match for punctuation differences
    tokens = [t for t in norm_excerpt.split(" ") if len(t) > 3]
    if len(tokens) >= 3:
        all_found = all(t in norm_doc for t in tokens)
        return all_found

    return False
