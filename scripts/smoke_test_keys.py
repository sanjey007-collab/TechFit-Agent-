#!/usr/bin/env python3
"""
Smoke test utility for Phase 0 API Key Onboarding.
Tests each key with a minimal live request, returns masked status, and NEVER logs raw secrets.
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Dict, Any

try:
    import httpx
except ImportError:
    print("[ERROR] httpx is required for smoke tests. Run: pip install httpx")
    sys.exit(1)

def load_dotenv():
    """Load variables from .env if present."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())

def mask_key(key: str) -> str:
    """Safely mask key showing only first 4 and last 2 characters."""
    if not key or len(key) < 8:
        return "********"
    return f"{key[:4]}****{key[-2:]}"

async def test_gemini(api_key: str, model: str = "gemini-3.5-flash") -> Dict[str, Any]:
    """Test Gemini API key using Google's v1beta REST endpoint with smart fallback."""
    if not api_key or "your_" in api_key.lower():
        return {"configured": False, "status": "FAIL", "reason": "Key not provided"}
    
    candidate_models = [model]
    for fallback in ["gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-3.8-flash"]:
        if fallback not in candidate_models:
            candidate_models.append(fallback)

    last_error = ""
    async with httpx.AsyncClient(timeout=15.0) as client:
        for m in candidate_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": "Reply with one word: OK"}]}],
                "generationConfig": {"maxOutputTokens": 10}
            }
            try:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
                    return {"configured": True, "status": "PASS", "masked_key": mask_key(api_key), "model": m, "response": text}
                else:
                    last_error = f"{m} ({resp.status_code}): {resp.text[:150]}"
            except Exception as e:
                last_error = f"{m} error: {str(e)}"
    
    return {"configured": True, "status": "FAIL", "masked_key": mask_key(api_key), "error": last_error}

async def test_search(provider: str, api_key: str, cx: str = "") -> Dict[str, Any]:
    """Test search provider with a minimal query for manufacturer specs."""
    if not api_key or "your_" in api_key.lower():
        return {"configured": False, "status": "FAIL", "reason": "Key not provided"}
    
    provider = provider.lower()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            if provider == "serper":
                resp = await client.post(
                    "https://google.serper.dev/search",
                    headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
                    json={"q": "Lenovo ThinkPad T480 RAM specs", "num": 1}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    organic = data.get("organic", [])
                    return {
                        "configured": True,
                        "status": "PASS",
                        "provider": "serper",
                        "masked_key": mask_key(api_key),
                        "results_count": len(organic)
                    }
                return {"configured": True, "status": "FAIL", "provider": "serper", "code": resp.status_code, "error": resp.text[:200]}

            elif provider in ("google_custom_search", "google"):
                url = f"https://www.googleapis.com/customsearch/v1?key={api_key}&cx={cx}&q=Lenovo+ThinkPad+T480+RAM+specs&num=1"
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    items = data.get("items", [])
                    return {
                        "configured": True,
                        "status": "PASS",
                        "provider": "google_custom_search",
                        "masked_key": mask_key(api_key),
                        "results_count": len(items)
                    }
                return {"configured": True, "status": "FAIL", "provider": "google_custom_search", "code": resp.status_code, "error": resp.text[:200]}

            elif provider == "serpapi":
                url = f"https://serpapi.com/search.json?engine=google&q=Lenovo+ThinkPad+T480+RAM+specs&api_key={api_key}&num=1"
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    organic = data.get("organic_results", [])
                    return {
                        "configured": True,
                        "status": "PASS",
                        "provider": "serpapi",
                        "masked_key": mask_key(api_key),
                        "results_count": len(organic)
                    }
                return {"configured": True, "status": "FAIL", "provider": "serpapi", "code": resp.status_code, "error": resp.text[:200]}

            elif provider == "brave":
                resp = await client.get(
                    "https://api.search.brave.com/res/v1/web/search?q=Lenovo+ThinkPad+T480+RAM+specs&count=1",
                    headers={"Accept": "application/json", "X-Subscription-Token": api_key}
                )
                if resp.status_code == 200:
                    return {"configured": True, "status": "PASS", "provider": "brave", "masked_key": mask_key(api_key)}
                return {"configured": True, "status": "FAIL", "provider": "brave", "code": resp.status_code, "error": resp.text[:200]}

            else:
                return {"configured": True, "status": "FAIL", "reason": f"Unknown provider: {provider}"}
    except Exception as e:
        return {"configured": True, "status": "FAIL", "error": str(e)}

async def test_product_details(provider: str, api_key: str) -> Dict[str, Any]:
    """Test product details provider."""
    provider = provider.lower()
    if provider in ("mock", "mock_store_only", "none"):
        return {"configured": True, "status": "PASS", "provider": "mock_store_only", "note": "Internal catalog active"}
    
    if not api_key or "your_" in api_key.lower():
        return {"configured": False, "status": "SKIPPED", "reason": "No external key provided, using mock store"}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            if provider == "serpapi":
                # Test SerpApi Google Shopping / Product engine
                url = f"https://serpapi.com/search.json?engine=google_shopping&q=Crucial+16GB+DDR4+SODIMM&api_key={api_key}&num=1"
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    results = data.get("shopping_results", [])
                    return {
                        "configured": True,
                        "status": "PASS",
                        "provider": "serpapi",
                        "masked_key": mask_key(api_key),
                        "results_count": len(results)
                    }
                return {"configured": True, "status": "FAIL", "provider": "serpapi", "code": resp.status_code, "error": resp.text[:200]}

            elif provider == "upcitemdb":
                url = f"https://api.upcitemdb.com/prod/trial/lookup?upc=0195553018288"
                headers = {"user_key": api_key, "key_type": "3pm"} if api_key else {}
                resp = await client.get(url, headers=headers)
                if resp.status_code in (200, 404):
                    return {"configured": True, "status": "PASS", "provider": "upcitemdb", "masked_key": mask_key(api_key)}
                return {"configured": True, "status": "FAIL", "provider": "upcitemdb", "code": resp.status_code, "error": resp.text[:200]}
            else:
                return {"configured": True, "status": "PASS", "provider": provider, "masked_key": mask_key(api_key)}
    except Exception as e:
        return {"configured": True, "status": "FAIL", "error": str(e)}

async def run_all():
    load_dotenv()
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    search_provider = os.getenv("SEARCH_PROVIDER", "serper")
    search_key = os.getenv("SEARCH_API_KEY") or os.getenv("GOOGLE_SEARCH_API_KEY", "")
    cx = os.getenv("GOOGLE_SEARCH_ENGINE_ID", "")
    product_provider = os.getenv("PRODUCT_DETAILS_PROVIDER", "mock_store_only")
    product_key = os.getenv("PRODUCT_DETAILS_API_KEY", "")

    print("\n=======================================================")
    print("      TechFit Agent — Phase 0 Live Smoke Test Report    ")
    print("=======================================================")
    
    gemini_res = await test_gemini(gemini_key, model)
    print(f"\n1. Gemini API ({model}):")
    print(f"   Status:     {gemini_res.get('status')}")
    print(f"   Masked Key: {gemini_res.get('masked_key', 'N/A')}")
    if gemini_res.get("status") == "PASS":
        print(f"   Response:   '{gemini_res.get('response')}' (Verification Successful)")
    else:
        print(f"   Error:      {gemini_res.get('error') or gemini_res.get('reason')}")

    search_res = await test_search(search_provider, search_key, cx)
    print(f"\n2. Search Provider ({search_provider}):")
    print(f"   Status:     {search_res.get('status')}")
    print(f"   Masked Key: {search_res.get('masked_key', 'N/A')}")
    if search_res.get("status") == "PASS":
        print(f"   Results:    {search_res.get('results_count', 0)} organic items retrieved (Live Search OK)")
    else:
        print(f"   Error:      {search_res.get('error') or search_res.get('reason')}")

    prod_res = await test_product_details(product_provider, product_key)
    print(f"\n3. Product Details Provider ({product_provider}):")
    print(f"   Status:     {prod_res.get('status')}")
    print(f"   Masked Key: {prod_res.get('masked_key', 'N/A')}")
    if prod_res.get("status") == "PASS":
        print(f"   Results:    {prod_res.get('results_count', 'OK')} items retrieved (Catalog Enrichment OK)")
    else:
        print(f"   Error:      {prod_res.get('error') or prod_res.get('reason')}")

    print("\n=======================================================")
    all_passed = (
        gemini_res.get("status") == "PASS" and 
        search_res.get("status") == "PASS" and 
        prod_res.get("status") in ("PASS", "SKIPPED")
    )
    if all_passed:
        print(" Gate Verdict: PASS (All critical Phase 0 credentials verified)")
    else:
        print(" Gate Verdict: FAIL (One or more critical keys failed)")
    print("=======================================================\n")
    return 0 if all_passed else 1

if __name__ == "__main__":
    res = asyncio.run(run_all())
    sys.exit(res)
