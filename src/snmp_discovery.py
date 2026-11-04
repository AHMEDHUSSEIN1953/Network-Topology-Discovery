import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

from pysnmp.hlapi.v3arch.asyncio import (
    CommunityData,
    ContextData,
    ObjectIdentity,
    ObjectType,
    SnmpEngine,
    UdpTransportTarget,
    get_cmd,
    walk_cmd,
)

COMMUNITY = "TopoRead2026"

ROUTERS = {
    "MikroTik-1": "192.168.56.105",
    "MikroTik-2": "10.0.12.2",
    "MikroTik-3": "10.0.13.2",
    "MikroTik-4": "10.0.24.2",
}

SCALARS = {
    "sysName": "1.3.6.1.2.1.1.5.0",
    "sysDescr": "1.3.6.1.2.1.1.1.0",
}

TABLES = {
    "interfaces": "1.3.6.1.2.1.31.1.1.1.1",
    "lldp_local_ports": "1.0.8802.1.1.2.1.3.7.1",
    "lldp_remote": "1.0.8802.1.1.2.1.4.1.1",
    "lldp_remote_management": "1.0.8802.1.1.2.1.4.2.1",
    "mikrotik_neighbors": "1.3.6.1.4.1.14988.1.1.11.1",
    "arp": "1.3.6.1.2.1.4.22.1",
}

async def get_scalar(engine, target, oid):
    error, status, index, values = await get_cmd(
        engine,
        CommunityData(COMMUNITY, mpModel=1),
        target,
        ContextData(),
        ObjectType(ObjectIdentity(oid)),
        lookupMib=False,
    )
    if error:
        raise RuntimeError(str(error))
    if status:
        raise RuntimeError(f"SNMP status {status}, index {index}")
    return values[0][1].prettyPrint() if values else None

async def walk_table(engine, target, root_oid):
    rows = []
    async for error, status, index, bindings in walk_cmd(
        engine,
        CommunityData(COMMUNITY, mpModel=1),
        target,
        ContextData(),
        ObjectType(ObjectIdentity(root_oid)),
        lookupMib=False,
        lexicographicMode=False,
        maxRows=300,
    ):
        if error:
            raise RuntimeError(str(error))
        if status:
            raise RuntimeError(f"SNMP status {status}, index {index}")
        for oid, value in bindings:
            rows.append({
                "oid": oid.prettyPrint(),
                "value": value.prettyPrint(),
            })
    return rows

async def main():
    engine = SnmpEngine()
    result = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "routers": [],
    }

    for router_name, address in ROUTERS.items():
        router = {
            "label": router_name,
            "address": address,
            "system": {},
            "tables": {},
        }

        try:
            target = await UdpTransportTarget.create(
                (address, 161),
                timeout=2,
                retries=1,
            )

            for name, oid in SCALARS.items():
                router["system"][name] = await get_scalar(engine, target, oid)

            for name, oid in TABLES.items():
                router["tables"][name] = await walk_table(engine, target, oid)

            print(
                f"[OK] {router_name} {address}: "
                f"name={router['system']['sysName']}, "
                f"interfaces={len(router['tables']['interfaces'])}, "
                f"LLDP={len(router['tables']['lldp_remote'])}, "
                f"ARP={len(router['tables']['arp'])}"
            )
        except Exception as exc:
            router["error"] = str(exc)
            print(f"[FAIL] {router_name} {address}: {exc}")

        result["routers"].append(router)

    Path("discovery.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print("Saved: discovery.json")

asyncio.run(main())
