import asyncio
from pysnmp.hlapi.v3arch.asyncio import (
    CommunityData,
    ContextData,
    ObjectIdentity,
    ObjectType,
    SnmpEngine,
    UdpTransportTarget,
    get_cmd,
)

ROUTERS = {
    "MikroTik-1": "192.168.56.105",
    "MikroTik-2": "10.0.12.2",
    "MikroTik-3": "10.0.13.2",
    "MikroTik-4": "10.0.24.2",
}

async def main():
    engine = SnmpEngine()

    for name, address in ROUTERS.items():
        target = await UdpTransportTarget.create(
            (address, 161),
            timeout=2,
            retries=1,
        )

        error, status, index, values = await get_cmd(
            engine,
            CommunityData("TopoRead2026", mpModel=1),
            target,
            ContextData(),
            ObjectType(ObjectIdentity("1.3.6.1.2.1.1.1.0")),
            lookupMib=False,
        )

        if error:
            print(f"[FAIL] {name} ({address}): {error}")
        elif status:
            print(f"[FAIL] {name} ({address}): {status}")
        else:
            print(f"[OK] {name} ({address}): {values[0][1]}")

asyncio.run(main())
