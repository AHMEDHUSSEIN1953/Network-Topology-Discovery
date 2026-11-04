"""Build the corrected, presentation-ready network topology diagram.

Router links and ARP endpoints come from discovery.json. The GNS3 Cloud and
the three built-in Ethernet switches are visual representations of the lab
design; they are not reported as protocol-discovered devices.
"""

import json
from pathlib import Path

from graphviz import Graph


IFNAME_PREFIX = "1.3.6.1.2.1.31.1.1.1.1"
ARP_PREFIX = "1.3.6.1.2.1.4.22.1"
ALPINE_NAT_IP = "10.0.3.15"

PC_INFO = {
    "192.168.110.11": {"name": "PC1", "gateway": "192.168.110.1", "switch": "SW1"},
    "192.168.110.12": {"name": "PC2", "gateway": "192.168.110.1", "switch": "SW1"},
    "192.168.120.11": {"name": "PC3", "gateway": "192.168.120.1", "switch": "SW2"},
    "192.168.120.12": {"name": "PC4", "gateway": "192.168.120.1", "switch": "SW2"},
    "192.168.130.11": {"name": "PC5", "gateway": "192.168.130.1", "switch": "SW3"},
    "192.168.130.12": {"name": "PC6", "gateway": "192.168.130.1", "switch": "SW3"},
}

ROUTER_INFO = {
    "MikroTik-1": "Management: 192.168.56.105/24\nTransit: 10.0.12.1/30, 10.0.13.1/30",
    "MikroTik-2": "Transit: 10.0.12.2/30, 10.0.24.1/30\nLAN gateway: 192.168.110.1/24",
    "MikroTik-3": "Transit: 10.0.13.2/30, 10.0.34.1/30\nLAN gateway: 192.168.120.1/24",
    "MikroTik-4": "Transit: 10.0.24.2/30, 10.0.34.2/30\nLAN gateway: 192.168.130.1/24",
}

ROUTER_POSITIONS = {
    "MikroTik-1": "0,0!",
    "MikroTik-2": "5,3.5!",
    "MikroTik-3": "5,-3.5!",
    "MikroTik-4": "10,0!",
}

SWITCH_INFO = {
    "SW1": {"label": "SW1\nLAN 192.168.110.0/24", "router": "MikroTik-2", "port": "ether3", "pos": "5,6.4!"},
    "SW2": {"label": "SW2\nLAN 192.168.120.0/24", "router": "MikroTik-3", "port": "ether3", "pos": "5,-6.4!"},
    "SW3": {"label": "SW3\nLAN 192.168.130.0/24", "router": "MikroTik-4", "port": "ether3", "pos": "14,0!"},
}

HOST_POSITIONS = {
    "192.168.56.102": "-7.5,1.4!",
    "192.168.56.100": "-7.5,-1.4!",
    "192.168.110.11": "2.2,9!",
    "192.168.110.12": "7.8,9!",
    "192.168.120.11": "2.2,-9!",
    "192.168.120.12": "7.8,-9!",
    "192.168.130.11": "17,1.8!",
    "192.168.130.12": "17,-1.8!",
}

ROUTER_LINK_SUBNETS = {
    frozenset(("MikroTik-1", "MikroTik-2")): "10.0.12.0/30",
    frozenset(("MikroTik-1", "MikroTik-3")): "10.0.13.0/30",
    frozenset(("MikroTik-2", "MikroTik-4")): "10.0.24.0/30",
    frozenset(("MikroTik-3", "MikroTik-4")): "10.0.34.0/30",
}


def table_rows(table):
    if isinstance(table, list):
        return table
    if isinstance(table, dict):
        return [{"oid": oid, "value": value} for oid, value in table.items()]
    return []


def get_interface_names(table):
    result = {}
    for row in table_rows(table):
        oid = str(row.get("oid", "")).lstrip(".")
        if oid.startswith(IFNAME_PREFIX + "."):
            try:
                result[int(oid.rsplit(".", 1)[1])] = str(row.get("value", ""))
            except ValueError:
                continue
    return result


def normalize_mac(value):
    raw = str(value).strip()
    hex_value = raw[2:] if raw.lower().startswith("0x") else raw
    if len(hex_value) == 12 and all(c in "0123456789abcdefABCDEF" for c in hex_value):
        return ":".join(hex_value[i : i + 2] for i in range(0, 12, 2)).lower()
    return raw


def get_arp_hosts(table):
    hosts = {}
    prefix = [int(part) for part in ARP_PREFIX.split(".")]

    for row in table_rows(table):
        try:
            oid = [
                int(part)
                for part in str(row.get("oid", "")).lstrip(".").split(".")
            ]
        except ValueError:
            continue

        if oid[: len(prefix)] != prefix:
            continue

        column_position = len(prefix)
        if len(oid) <= column_position + 1:
            continue

        column = oid[column_position]
        suffix = oid[column_position + 1 :]
        if len(suffix) != 5:
            continue

        if_index = suffix[0]
        ip = ".".join(str(part) for part in suffix[1:])
        entry = hosts.setdefault(ip, {"if_index": if_index, "mac": ""})
        if column == 1:
            entry["if_index"] = if_index
        elif column == 2:
            entry["mac"] = normalize_mac(row.get("value", ""))

    return hosts


def main():
    data = json.loads(Path("discovery.json").read_text())
    routers = data.get("routers", [])
    router_names = {router.get("label") for router in routers}

    router_ips = set()
    for router in routers:
        address = router.get("address") or router.get("ip")
        if address:
            router_ips.add(str(address))
        for neighbor in router.get("tables", {}).get("routeros_neighbors", []):
            if neighbor.get("address"):
                router_ips.add(str(neighbor["address"]))

    graph = Graph(
        "CorrectedNetworkTopology",
        filename="topology_corrected",
        format="png",
        engine="neato",
        strict=True,
    )
    graph.attr(
        "graph",
        overlap="false",
        splines="line",
        bgcolor="white",
        dpi="180",
        size="25,21!",
        pad="0.55",
        label=(
            "Router adjacencies: CDP / LLDP / MNDP; end hosts: ARP over SNMPv2c\n"
            "Cloud is shown directly (no cloud switch); LAN switches are illustrative GNS3 nodes"
        ),
        labelloc="t",
        fontsize="15",
        fontname="DejaVu Sans",
    )
    graph.attr("node", fontname="DejaVu Sans", fontsize="10")
    graph.attr("edge", color="#566573", fontname="DejaVu Sans", fontsize="9")

    # Draw router nodes with the current target and routed interface addresses.
    for router in routers:
        name = router.get("label", "Unknown router")
        target = router.get("address") or router.get("ip", "")
        details = ROUTER_INFO.get(name, "")
        label = f"{name}\nSNMP target: {target}\n{details}"
        graph.node(
            name,
            label=label,
            pos=ROUTER_POSITIONS.get(name, "0,0!"),
            pin="true",
            shape="box",
            style="rounded,filled",
            fillcolor="#EAF2F8",
            color="#2874A6",
            margin="0.20,0.14",
        )

    # Use subnet labels on transit links; do not print MikroTik-2 ether1.
    router_edges = set()
    for router in routers:
        local = router.get("label", "Unknown router")
        for neighbor in router.get("tables", {}).get("routeros_neighbors", []):
            remote = neighbor.get("identity")
            if remote not in router_names:
                continue
            pair = frozenset((local, remote))
            if pair in ROUTER_LINK_SUBNETS:
                router_edges.add(pair)

    for pair in router_edges:
        subnet = ROUTER_LINK_SUBNETS[pair]
        router_a, router_b = sorted(pair)
        graph.edge(
            router_a,
            router_b,
            label=f"{subnet}\nCDP / LLDP / MNDP",
            penwidth="1.6",
        )

    # The GNS3 Cloud represents the host-only segment; it is not a switch.
    graph.node(
        "GNS3-Cloud",
        label="GNS3 Cloud\nVirtualBox Host-only\n192.168.56.0/24",
        pos="-4,0!",
        pin="true",
        shape="cloud",
        style="filled",
        fillcolor="#E8F8F5",
        color="#148F77",
        margin="0.22,0.15",
    )
    graph.edge("MikroTik-1", "GNS3-Cloud", label="ether1 / host-only")

    # Draw the three actual PC LAN switches only; there is no switch for Cloud.
    for name, details in SWITCH_INFO.items():
        graph.node(
            name,
            label=details["label"],
            pos=details["pos"],
            pin="true",
            shape="component",
            style="filled",
            fillcolor="#E8DAEF",
            color="#7D3C98",
            margin="0.20,0.14",
        )
        graph.edge(
            details["router"],
            name,
            label=f'{details["port"]} / {details["label"].splitlines()[1]}',
            penwidth="1.5",
        )

    hosts_drawn = set()
    for router in routers:
        router_name = router.get("label", "Unknown router")
        interface_names = get_interface_names(
            router.get("tables", {}).get("interfaces", [])
        )

        for ip, entry in get_arp_hosts(
            router.get("tables", {}).get("arp", [])
        ).items():
            if ip in router_ips or ip == ALPINE_NAT_IP:
                continue

            host_node = "host_" + ip.replace(".", "_")
            pc = PC_INFO.get(ip)
            if pc:
                label = (
                    f'{pc["name"]}\nIP: {ip}/24\n'
                    f'Gateway: {pc["gateway"]}'
                )
                if entry.get("mac"):
                    label += f'\nMAC: {entry["mac"]}'
                parent = pc["switch"]
            elif ip == "192.168.56.102":
                label = (
                    "Alpine Linux\n"
                    "eth0: 192.168.56.102/24\n"
                    "eth1: 10.0.3.15/24 (VirtualBox NAT)\n"
                    "Default gateway: 10.0.3.2\n"
                    "Lab next hop: 192.168.56.105"
                )
                if entry.get("mac"):
                    label += f'\neth0 MAC: {entry["mac"]}'
                parent = "GNS3-Cloud"
            elif ip.startswith("192.168.56."):
                label = f"ARP host\nIP: {ip}"
                if entry.get("mac"):
                    label += f'\nMAC: {entry["mac"]}'
                parent = "GNS3-Cloud"
            else:
                label = f"ARP host\nIP: {ip}"
                if entry.get("mac"):
                    label += f'\nMAC: {entry["mac"]}'
                parent = router_name

            graph.node(
                host_node,
                label=label,
                pos=HOST_POSITIONS.get(ip, "-7.5,-1.4!"),
                pin="true",
                shape="ellipse",
                style="filled",
                fillcolor="#FCF3CF",
                color="#B7950B",
                margin="0.20,0.14",
            )
            hosts_drawn.add(ip)

            if parent == "GNS3-Cloud":
                graph.edge(parent, host_node, label="Host-only endpoint")
            elif parent in SWITCH_INFO:
                graph.edge(parent, host_node, label="LAN endpoint")
            else:
                ifname = interface_names.get(entry["if_index"], "unknown interface")
                graph.edge(parent, host_node, label=f"{ifname} / ARP")

    output = graph.render(cleanup=True)
    print(f"Created: {Path(output).resolve()}")
    print(
        f"Routers: {len(router_names)} | Router links: {len(router_edges)} | "
        f"LAN switches: {len(SWITCH_INFO)} | ARP hosts: {len(hosts_drawn)}"
    )
    print("No switch is drawn for Cloud. Transit edges show subnets, not MikroTik-2 ether1.")


if __name__ == "__main__":
    main()
