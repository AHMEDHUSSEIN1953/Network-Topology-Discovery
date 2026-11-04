import json
import re
import subprocess
from pathlib import Path

DATA_FILE = Path("discovery.json")

def parse_neighbors(output):
    pattern = re.compile(
        r"(?ms)^[ \t]*\d+[ \t]+interface=(.*?)(?=^[ \t]*\d+[ \t]+interface=|\Z)"
    )
    neighbors = []

    for match in pattern.finditer(output):
        block = "interface=" + match.group(1)

        def field(name):
            item = re.search(rf'\b{name}=("[^"]*"|\S+)', block)
            if not item:
                return None
            value = item.group(1)
            return value[1:-1] if value.startswith('"') else value

        protocols = field("discovered-by") or ""
        neighbors.append({
            "identity": field("identity"),
            "address": field("address4") or field("address"),
            "mac_address": field("mac-address"),
            "local_interface": field("interface"),
            "remote_interface": field("interface-name"),
            "discovered_by": [p for p in protocols.split(",") if p],
        })

    return neighbors

data = json.loads(DATA_FILE.read_text(encoding="utf-8"))

for router in data["routers"]:
    address = router["address"]
    label = router["label"]
    print(f"\n[SSH] Connecting to {label} ({address})...", flush=True)

    try:
        result = subprocess.run(
            [
                "ssh", "-T", "-o", "ConnectTimeout=8",
                f"admin@{address}",
                "/ip/neighbor/print detail",
            ],
            text=True,
            stdout=subprocess.PIPE,
            timeout=25,
            check=False,
        )

        if result.returncode != 0:
            router["ssh_error"] = f"SSH exited with code {result.returncode}"
            print(f"[FAIL] {label}: check the SSH message above")
            continue

        neighbors = parse_neighbors(result.stdout)
        # A previous failed run may have left an error beside stale data.
        # Clear that status after a successful current query.
        router.pop("ssh_error", None)
        router["tables"]["routeros_neighbors"] = neighbors
        print(f"[OK] {label}: {len(neighbors)} neighbors")

        for neighbor in neighbors:
            print(
                f"  {neighbor['identity']} via "
                f"{','.join(neighbor['discovered_by']) or 'protocol not reported'}"
            )

    except Exception as exc:
        router["ssh_error"] = str(exc)
        print(f"[FAIL] {label}: {exc}")

DATA_FILE.write_text(
    json.dumps(data, indent=2, ensure_ascii=False),
    encoding="utf-8",
)
print("\nUpdated: discovery.json")
