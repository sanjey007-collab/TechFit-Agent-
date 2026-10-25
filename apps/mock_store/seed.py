import asyncio
import json
from sqlalchemy import select
from .database import engine, Base, AsyncSessionLocal
from .models import StoreProduct, StoreCart, StoreCartItem

OFFICIAL_PRODUCTS = [
    {
        "sku": "RAM-A",
        "title": "Crucial 16GB DDR4-3200 SODIMM Laptop Memory",
        "brand": "Crucial",
        "category": "RAM",
        "price": 42.99,
        "stock": 50,
        "specs_json": json.dumps({
            "ddr_generation": "DDR4",
            "form_factor": "SO-DIMM",
            "capacity_gb": 16,
            "speed_mhz": 3200,
            "voltage": 1.2,
            "pin_count": 260,
            "ecc": False
        }),
        "description": "High performance 16GB DDR4 notebook RAM module operating at 3200MHz, 1.2V, 260-pin non-ECC SO-DIMM."
    },
    {
        "sku": "RAM-B",
        "title": "Kingston FURY Impact 16GB DDR5-4800 SODIMM Memory",
        "brand": "Kingston",
        "category": "RAM",
        "price": 58.99,
        "stock": 25,
        "specs_json": json.dumps({
            "ddr_generation": "DDR5",
            "form_factor": "SO-DIMM",
            "capacity_gb": 16,
            "speed_mhz": 4800,
            "voltage": 1.1,
            "pin_count": 262,
            "ecc": "on-die"
        }),
        "description": "Next-generation 16GB DDR5 notebook RAM module operating at 4800MHz, 1.1V, 262-pin SO-DIMM."
    },
    {
        "sku": "RAM-C",
        "title": "Corsair Vengeance LPX 16GB DDR4-3200 Desktop DIMM",
        "brand": "Corsair",
        "category": "RAM",
        "price": 39.99,
        "stock": 40,
        "specs_json": json.dumps({
            "ddr_generation": "DDR4",
            "form_factor": "DIMM",
            "capacity_gb": 16,
            "speed_mhz": 3200,
            "voltage": 1.35,
            "pin_count": 288,
            "ecc": False
        }),
        "description": "Standard full-size desktop 288-pin DIMM memory module. NOT for laptop/notebook use."
    },
    {
        "sku": "UNIVERSAL-CHARGER-001",
        "title": "Universal Multi-Tip Laptop Charger 90W Ultra Slim",
        "brand": "GenericPower",
        "category": "CHARGER",
        "price": 29.99,
        "stock": 100,
        "specs_json": json.dumps({
            "connector": "universal_multiple_tips",
            "claimed_wattage": 90,
            "unverified_claim": True
        }),
        "description": "Works with all laptops worldwide! Guaranteed universal fit for any brand without setup."
    },
    {
        "sku": "CHARGER-OEM-65W-USB-C",
        "title": "Lenovo Standard 65W AC Adapter USB-C (Type-C)",
        "brand": "Lenovo",
        "category": "CHARGER",
        "price": 49.99,
        "stock": 35,
        "specs_json": json.dumps({
            "connector": "USB-C",
            "wattage": 65,
            "voltage_output": [20.0, 15.0, 9.0, 5.0],
            "current_output": [3.25, 3.0, 2.0, 2.0],
            "pd_version": "PD 3.0",
            "oem_certified": True
        }),
        "description": "Official genuine 65W USB-C AC power adapter supporting USB Power Delivery 3.0 profiles (20V/3.25A, 15V/3A, 9V/2A, 5V/2A)."
    },
    {
        "sku": "CHARGER-BARREL-45W",
        "title": "Dell 45W 4.5mm Small Pin AC Power Adapter",
        "brand": "Dell",
        "category": "CHARGER",
        "price": 24.99,
        "stock": 20,
        "specs_json": json.dumps({
            "connector": "Barrel 4.5mm x 3.0mm with center pin",
            "wattage": 45,
            "voltage_output": [19.5],
            "current_output": [2.31],
            "oem_certified": True
        }),
        "description": "Original 45W 19.5V 2.31A 4.5mm barrel tip charger for Dell Inspiron and XPS laptops."
    }
]

async def seed_mock_store(custom_engine=None, custom_session_factory=None):
    use_engine = custom_engine or engine
    use_session_factory = custom_session_factory or AsyncSessionLocal

    async with use_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with use_session_factory() as session:
        for p_data in OFFICIAL_PRODUCTS:
            stmt = select(StoreProduct).where(StoreProduct.sku == p_data["sku"])
            res = await session.execute(stmt)
            existing = res.scalar_one_or_none()
            if not existing:
                product = StoreProduct(**p_data)
                session.add(product)
            else:
                for k, v in p_data.items():
                    setattr(existing, k, v)
        await session.commit()
    print("[Mock Store] Seed completed successfully.")

if __name__ == "__main__":
    asyncio.run(seed_mock_store())
