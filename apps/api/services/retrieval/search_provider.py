import abc
import os
import httpx
from typing import List, Dict, Any, Optional

class SearchResult:
    def __init__(self, title: str, url: str, snippet: str, domain: str, is_official: bool = False):
        self.title = title
        self.url = url
        self.snippet = snippet
        self.domain = domain
        self.is_official = is_official

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "domain": self.domain,
            "is_official": self.is_official
        }

OFFICIAL_DOMAINS = [
    "lenovo.com", "dell.com", "hp.com", "asus.com", "acer.com",
    "apple.com", "samsung.com", "crucial.com", "kingston.com",
    "intel.com", "amd.com", "psref.lenovo.com"
]

class SearchProvider(abc.ABC):
    @abc.abstractmethod
    async def search(self, query: str, num_results: int = 5) -> List[SearchResult]:
        pass

class SerperSearchProvider(SearchProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def search(self, query: str, num_results: int = 5) -> List[SearchResult]:
        if not self.api_key:
            return []
        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {"q": query, "num": num_results}
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code != 200:
                return []
            data = resp.json()
            organic = data.get("organic", [])
            results = []
            for item in organic:
                link = item.get("link", "")
                domain = link.split("//")[-1].split("/")[0].lower()
                is_official = any(d in domain for d in OFFICIAL_DOMAINS)
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=link,
                    snippet=item.get("snippet", ""),
                    domain=domain,
                    is_official=is_official
                ))
            # Sort official domains to top
            results.sort(key=lambda r: (not r.is_official))
            return results

class SerpApiSearchProvider(SearchProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def search(self, query: str, num_results: int = 5) -> List[SearchResult]:
        if not self.api_key:
            return []
        url = "https://serpapi.com/search.json"
        params = {
            "engine": "google",
            "q": query,
            "num": num_results,
            "api_key": self.api_key
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
            if resp.status_code != 200:
                return []
            data = resp.json()
            organic = data.get("organic_results", [])
            results = []
            for item in organic:
                link = item.get("link", "")
                domain = link.split("//")[-1].split("/")[0].lower()
                is_official = any(d in domain for d in OFFICIAL_DOMAINS)
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=link,
                    snippet=item.get("snippet", ""),
                    domain=domain,
                    is_official=is_official
                ))
            results.sort(key=lambda r: (not r.is_official))
            return results

class MockSearchProvider(SearchProvider):
    async def search(self, query: str, num_results: int = 5) -> List[SearchResult]:
        return [
            SearchResult(
                title="DemoTech DEMO-LAPTOP-001 Official PSREF Maintenance Manual",
                url="https://support.demotech.example.com/specs/demo-laptop-001",
                snippet="Supports 2x DDR4-3200 SO-DIMM sockets. Max capacity 32GB total.",
                domain="support.demotech.example.com",
                is_official=True
            )
        ]

def get_search_provider() -> SearchProvider:
    from ...config import settings
    provider = settings.SEARCH_PROVIDER.lower()
    key = settings.SEARCH_API_KEY or settings.GOOGLE_SEARCH_API_KEY
    if provider == "serper" and key:
        return SerperSearchProvider(key)
    elif provider == "serpapi" and key:
        return SerpApiSearchProvider(key)
    return MockSearchProvider()
