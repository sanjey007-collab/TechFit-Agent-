import abc
import httpx
from typing import Dict, Any, Optional

class ProductDetails:
    def __init__(
        self,
        sku: str,
        title: str,
        brand: str,
        category: str,
        price: float,
        specs: Dict[str, Any],
        seller_name: str,
        source: str
    ):
        self.sku = sku
        self.title = title
        self.brand = brand
        self.category = category
        self.price = price
        self.specs = specs
        self.seller_name = seller_name
        self.source = source

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sku": self.sku,
            "title": self.title,
            "brand": self.brand,
            "category": self.category,
            "price": self.price,
            "specs": self.specs,
            "seller_name": self.seller_name,
            "source": self.source
        }

class ProductDetailsProvider(abc.ABC):
    @abc.abstractmethod
    async def get_product_details(self, identifier: str) -> Optional[ProductDetails]:
        pass

class SerpApiProductDetailsProvider(ProductDetailsProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def get_product_details(self, identifier: str) -> Optional[ProductDetails]:
        if not self.api_key:
            return None
        url = "https://serpapi.com/search.json"
        params = {
            "engine": "google_shopping",
            "q": identifier,
            "num": 1,
            "api_key": self.api_key
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    shopping = data.get("shopping_results", [])
                    if shopping:
                        first = shopping[0]
                        price_raw = first.get("extracted_price", 0.0)
                        return ProductDetails(
                            sku=first.get("product_id", identifier),
                            title=first.get("title", identifier),
                            brand=first.get("source", "Marketplace"),
                            category="RAM" if "ram" in identifier.lower() or "ddr" in identifier.lower() else "CHARGER",
                            price=float(price_raw) if price_raw else 39.99,
                            specs={"snippet": first.get("snippet", ""), "delivery": first.get("delivery", "")},
                            seller_name=first.get("source", "Online Retailer"),
                            source="serpapi_google_shopping"
                        )
        except Exception:
            return None
        return None

class MockStoreProductDetailsProvider(ProductDetailsProvider):
    async def get_product_details(self, identifier: str) -> Optional[ProductDetails]:
        # Fallback to local catalog
        from ...models import Product
        from ...database import AsyncSessionLocal
        from sqlalchemy import select
        import json
        async with AsyncSessionLocal() as session:
            stmt = select(Product).where(Product.sku == identifier)
            res = await session.execute(stmt)
            p = res.scalar_one_or_none()
            if p:
                return ProductDetails(
                    sku=p.sku,
                    title=p.name,
                    brand=p.brand,
                    category=p.category,
                    price=p.price,
                    specs=json.loads(p.specs_json) if p.specs_json else {},
                    seller_name="Official Mock Store",
                    source="mock_store"
                )
        return None

def get_product_details_provider() -> ProductDetailsProvider:
    from ...config import settings
    provider = settings.PRODUCT_DETAILS_PROVIDER.lower()
    key = settings.PRODUCT_DETAILS_API_KEY
    if provider == "serpapi" and key:
        return SerpApiProductDetailsProvider(key)
    return MockStoreProductDetailsProvider()
