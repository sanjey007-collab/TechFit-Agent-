import asyncio
import json
import datetime
from sqlalchemy import select
from .database import engine, Base, AsyncSessionLocal
from .models import Device, DeviceVariant, Source, SpecFact, Product

OFFICIAL_DEVICES = [
    {
        "id": "dev_demo_001",
        "brand": "DemoTech",
        "model_family": "DEMO-LAPTOP-001",
        "description": "Standard business laptop with expandable DDR4 memory slots.",
        "variants": [
            {
                "id": "var_demo_001_core",
                "variant_code": "DEMO-LAPTOP-001-CORE",
                "full_name": "DemoTech DEMO-LAPTOP-001 (Core Edition)",
                "form_factor": "Laptop"
            }
        ]
    },
    {
        "id": "dev_demo_002",
        "brand": "DemoTech",
        "model_family": "DEMO-LAPTOP-002",
        "description": "Mid-range laptop with conflicting documentation revisions across regional support bulletins.",
        "variants": [
            {
                "id": "var_demo_002_core",
                "variant_code": "DEMO-LAPTOP-002-CORE",
                "full_name": "DemoTech DEMO-LAPTOP-002 (Dual Revision)",
                "form_factor": "Laptop"
            }
        ]
    },
    {
        "id": "dev_demo_004",
        "brand": "DemoTech",
        "model_family": "DEMO-LAPTOP-004",
        "description": "Modern ultraportable laptop requiring 65W USB-C Power Delivery charging.",
        "variants": [
            {
                "id": "var_demo_004_typec",
                "variant_code": "DEMO-LAPTOP-004-TYPEC",
                "full_name": "DemoTech DEMO-LAPTOP-004 (Type-C Edition)",
                "form_factor": "Laptop"
            }
        ]
    }
]

OFFICIAL_SOURCES = [
    {
        "id": "src_demo_001_psref",
        "url": "https://support.demotech.example.com/specs/demo-laptop-001",
        "title": "DemoTech Official Hardware Maintenance Manual & PSREF - DEMO-LAPTOP-001",
        "domain": "support.demotech.example.com",
        "author": "DemoTech Engineering Documentation",
        "is_official": True,
        "excerpt": "Memory Architecture: Supports 2x DDR4-3200 SO-DIMM sockets. Factory installed: 8GB DDR4-3200 in slot 1; slot 2 is open. Maximum supported system memory is 32GB (up to 16GB per module). Standard operating voltage is 1.2V.",
        "applicability": "DEMO-LAPTOP-001"
    },
    {
        "id": "src_demo_002_psref",
        "url": "https://psref.demotech.example.com/product/demo-laptop-002",
        "title": "DemoTech PSREF Product Specification Sheet - DEMO-LAPTOP-002",
        "domain": "psref.demotech.example.com",
        "author": "DemoTech Product Systems Reference",
        "is_official": True,
        "excerpt": "System Memory Specification: Standard DDR4 SO-DIMM operating at 2400MHz, supporting dual-channel memory expansion up to 32GB total.",
        "applicability": "DEMO-LAPTOP-002"
    },
    {
        "id": "src_demo_002_bulletin",
        "url": "https://support-bulletin.demotech.example.com/hardware/demo-laptop-002",
        "title": "DemoTech Global Technical Support Bulletin #2026-09 - DEMO-LAPTOP-002 Motherboard Revision",
        "domain": "support-bulletin.demotech.example.com",
        "author": "DemoTech Global Support Center",
        "is_official": True,
        "excerpt": "Engineering Notice: Platform Revision B for DEMO-LAPTOP-002 utilizes DDR5 SO-DIMM operating at 4800MHz. DDR4 memory modules are strictly incompatible with Revision B motherboards.",
        "applicability": "DEMO-LAPTOP-002"
    },
    {
        "id": "src_demo_004_power",
        "url": "https://support.demotech.example.com/specs/demo-laptop-004",
        "title": "DemoTech DEMO-LAPTOP-004 Power & Charging Architecture Specification",
        "domain": "support.demotech.example.com",
        "author": "DemoTech Hardware Architecture Group",
        "is_official": True,
        "excerpt": "Electrical Input: Requires USB Type-C AC Adapter delivering 65W with USB Power Delivery 3.0 protocol negotiation (20V/3.25A required). Non-PD chargers or chargers below 65W will trigger low-power warning or fail to charge during active system operation.",
        "applicability": "DEMO-LAPTOP-004"
    }
]

OFFICIAL_SPEC_FACTS = [
    # DEMO-LAPTOP-001 facts
    {
        "id": "fact_001_ddr",
        "device_variant_id": "var_demo_001_core",
        "source_id": "src_demo_001_psref",
        "category": "RAM",
        "field_name": "ddr_generation",
        "raw_value": "DDR4-3200",
        "normalized_value": "DDR4",
        "excerpt": "Supports 2x DDR4-3200 SO-DIMM sockets.",
        "confidence": 1.0
    },
    {
        "id": "fact_001_form",
        "device_variant_id": "var_demo_001_core",
        "source_id": "src_demo_001_psref",
        "category": "RAM",
        "field_name": "form_factor",
        "raw_value": "SO-DIMM",
        "normalized_value": "SO-DIMM",
        "excerpt": "Supports 2x DDR4-3200 SO-DIMM sockets.",
        "confidence": 1.0
    },
    {
        "id": "fact_001_max_cap",
        "device_variant_id": "var_demo_001_core",
        "source_id": "src_demo_001_psref",
        "category": "RAM",
        "field_name": "max_capacity_gb",
        "raw_value": "32GB",
        "normalized_value": "32",
        "excerpt": "Maximum supported system memory is 32GB (up to 16GB per module).",
        "confidence": 1.0
    },
    {
        "id": "fact_001_slots",
        "device_variant_id": "var_demo_001_core",
        "source_id": "src_demo_001_psref",
        "category": "RAM",
        "field_name": "available_slots",
        "raw_value": "1 available (2 total, 1 occupied)",
        "normalized_value": "1",
        "excerpt": "Factory installed: 8GB DDR4-3200 in slot 1; slot 2 is open.",
        "confidence": 1.0
    },
    {
        "id": "fact_001_speed",
        "device_variant_id": "var_demo_001_core",
        "source_id": "src_demo_001_psref",
        "category": "RAM",
        "field_name": "speed_mhz",
        "raw_value": "3200MHz",
        "normalized_value": "3200",
        "excerpt": "Supports 2x DDR4-3200 SO-DIMM sockets.",
        "confidence": 1.0
    },

    # DEMO-LAPTOP-002 conflicting facts
    {
        "id": "fact_002_ddr_psref",
        "device_variant_id": "var_demo_002_core",
        "source_id": "src_demo_002_psref",
        "category": "RAM",
        "field_name": "ddr_generation",
        "raw_value": "DDR4",
        "normalized_value": "DDR4",
        "excerpt": "Standard DDR4 SO-DIMM operating at 2400MHz",
        "confidence": 0.9
    },
    {
        "id": "fact_002_ddr_bulletin",
        "device_variant_id": "var_demo_002_core",
        "source_id": "src_demo_002_bulletin",
        "category": "RAM",
        "field_name": "ddr_generation",
        "raw_value": "DDR5",
        "normalized_value": "DDR5",
        "excerpt": "Platform Revision B for DEMO-LAPTOP-002 utilizes DDR5 SO-DIMM operating at 4800MHz",
        "confidence": 0.9
    },

    # DEMO-LAPTOP-004 charger facts
    {
        "id": "fact_004_connector",
        "device_variant_id": "var_demo_004_typec",
        "source_id": "src_demo_004_power",
        "category": "CHARGER",
        "field_name": "connector",
        "raw_value": "USB Type-C",
        "normalized_value": "USB-C",
        "excerpt": "Requires USB Type-C AC Adapter delivering 65W with USB Power Delivery 3.0",
        "confidence": 1.0
    },
    {
        "id": "fact_004_wattage",
        "device_variant_id": "var_demo_004_typec",
        "source_id": "src_demo_004_power",
        "category": "CHARGER",
        "field_name": "wattage",
        "raw_value": "65W",
        "normalized_value": "65",
        "excerpt": "Requires USB Type-C AC Adapter delivering 65W",
        "confidence": 1.0
    },
    {
        "id": "fact_004_voltage",
        "device_variant_id": "var_demo_004_typec",
        "source_id": "src_demo_004_power",
        "category": "CHARGER",
        "field_name": "voltage",
        "raw_value": "20V",
        "normalized_value": "20.0",
        "excerpt": "20V/3.25A required",
        "confidence": 1.0
    },
    {
        "id": "fact_004_current",
        "device_variant_id": "var_demo_004_typec",
        "source_id": "src_demo_004_power",
        "category": "CHARGER",
        "field_name": "current",
        "raw_value": "3.25A",
        "normalized_value": "3.25",
        "excerpt": "20V/3.25A required",
        "confidence": 1.0
    },
    {
        "id": "fact_004_pd",
        "device_variant_id": "var_demo_004_typec",
        "source_id": "src_demo_004_power",
        "category": "CHARGER",
        "field_name": "charging_protocol",
        "raw_value": "USB Power Delivery 3.0",
        "normalized_value": "USB-PD",
        "excerpt": "USB Power Delivery 3.0 protocol negotiation (20V/3.25A required)",
        "confidence": 1.0
    }
]

OFFICIAL_PRODUCTS = [
    {
        "id": "prod_ram_a",
        "sku": "RAM-A",
        "name": "Crucial 16GB DDR4-3200 SODIMM Laptop Memory",
        "brand": "Crucial",
        "category": "RAM",
        "price": 42.99,
        "in_stock": True,
        "stock_quantity": 50,
        "specs_json": json.dumps({
            "ddr_generation": "DDR4",
            "form_factor": "SO-DIMM",
            "capacity_gb": 16,
            "speed_mhz": 3200,
            "voltage": 1.2,
            "pin_count": 260,
            "ecc": False
        }),
        "evidence_notes": "Official verified compatible DDR4 SO-DIMM module for DEMO-LAPTOP-001."
    },
    {
        "id": "prod_ram_b",
        "sku": "RAM-B",
        "name": "Kingston FURY Impact 16GB DDR5-4800 SODIMM Memory",
        "brand": "Kingston",
        "category": "RAM",
        "price": 58.99,
        "in_stock": True,
        "stock_quantity": 25,
        "specs_json": json.dumps({
            "ddr_generation": "DDR5",
            "form_factor": "SO-DIMM",
            "capacity_gb": 16,
            "speed_mhz": 4800,
            "voltage": 1.1,
            "pin_count": 262,
            "ecc": "on-die"
        }),
        "evidence_notes": "DDR5 memory module. Incompatible with DDR4 slots."
    },
    {
        "id": "prod_ram_c",
        "sku": "RAM-C",
        "name": "Corsair Vengeance LPX 16GB DDR4-3200 Desktop DIMM",
        "brand": "Corsair",
        "category": "RAM",
        "price": 39.99,
        "in_stock": True,
        "stock_quantity": 40,
        "specs_json": json.dumps({
            "ddr_generation": "DDR4",
            "form_factor": "DIMM",
            "capacity_gb": 16,
            "speed_mhz": 3200,
            "voltage": 1.35,
            "pin_count": 288,
            "ecc": False
        }),
        "evidence_notes": "Desktop 288-pin DIMM. Incompatible with laptop SO-DIMM slots."
    },
    {
        "id": "prod_charger_univ",
        "sku": "UNIVERSAL-CHARGER-001",
        "name": "Universal Multi-Tip Laptop Charger 90W Ultra Slim",
        "brand": "GenericPower",
        "category": "CHARGER",
        "price": 29.99,
        "in_stock": True,
        "stock_quantity": 100,
        "specs_json": json.dumps({
            "connector": "universal_multiple_tips",
            "claimed_wattage": 90,
            "unverified_claim": True
        }),
        "evidence_notes": "Advertised as works with all laptops, but lacks specific connector pinout and voltage negotiation evidence."
    },
    {
        "id": "prod_charger_oem_65w",
        "sku": "CHARGER-OEM-65W-USB-C",
        "name": "Lenovo Standard 65W AC Adapter USB-C (Type-C)",
        "brand": "Lenovo",
        "category": "CHARGER",
        "price": 49.99,
        "in_stock": True,
        "stock_quantity": 35,
        "specs_json": json.dumps({
            "connector": "USB-C",
            "wattage": 65,
            "voltage_output": [20.0, 15.0, 9.0, 5.0],
            "current_output": [3.25, 3.0, 2.0, 2.0],
            "pd_version": "PD 3.0",
            "oem_certified": True
        }),
        "evidence_notes": "OEM 65W Type-C adapter with verified 20V/3.25A USB PD profiles."
    }
]

async def seed_backend(custom_engine=None, custom_session_factory=None):
    use_engine = custom_engine or engine
    use_session_factory = custom_session_factory or AsyncSessionLocal

    async with use_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with use_session_factory() as session:
        # 1. Seed Devices and Variants
        for d_data in OFFICIAL_DEVICES:
            variants = d_data.pop("variants", [])
            stmt = select(Device).where(Device.id == d_data["id"])
            res = await session.execute(stmt)
            dev = res.scalar_one_or_none()
            if not dev:
                dev = Device(**d_data)
                session.add(dev)
            for v_data in variants:
                v_stmt = select(DeviceVariant).where(DeviceVariant.id == v_data["id"])
                v_res = await session.execute(v_stmt)
                var = v_res.scalar_one_or_none()
                if not var:
                    var = DeviceVariant(device_id=dev.id, **v_data)
                    session.add(var)

        # 2. Seed Sources
        for s_data in OFFICIAL_SOURCES:
            stmt = select(Source).where(Source.id == s_data["id"])
            res = await session.execute(stmt)
            if not res.scalar_one_or_none():
                src = Source(**s_data)
                session.add(src)

        # 3. Seed Spec Facts
        for f_data in OFFICIAL_SPEC_FACTS:
            stmt = select(SpecFact).where(SpecFact.id == f_data["id"])
            res = await session.execute(stmt)
            if not res.scalar_one_or_none():
                fact = SpecFact(**f_data)
                session.add(fact)

        # 4. Seed Products
        for p_data in OFFICIAL_PRODUCTS:
            stmt = select(Product).where(Product.sku == p_data["sku"])
            res = await session.execute(stmt)
            existing = res.scalar_one_or_none()
            if not existing:
                prod = Product(**p_data)
                session.add(prod)
            else:
                for k, v in p_data.items():
                    setattr(existing, k, v)

        await session.commit()
    print("[Backend API] Database seed completed successfully.")

if __name__ == "__main__":
    asyncio.run(seed_backend())
