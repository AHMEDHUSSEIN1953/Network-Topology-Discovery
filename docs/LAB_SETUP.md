# GNS3 Lab Setup and Connectivity Notes

This guide accompanies [`Network-Topology-Discovery-1.zip`](../gns3-project/Network-Topology-Discovery-1.zip). The archive preserves the GNS3 canvas, its 14 nodes and 14 links, per-router project disks, and VPCS startup files. The VPCS startup files set the endpoint IP addresses and gateways listed below.

## Dependencies and portability

The project was saved with GNS3 2.2.61 and local QEMU 3.1.0. Its four QEMU nodes refer to the external image `chr-7.24.6.img`, use 256 MiB RAM, and expose five Ethernet adapters. The CHR base image and Alpine VirtualBox VM are not included in the archive.

Before opening the project on another computer:

1. Install a compatible GNS3 Desktop/QEMU setup and obtain a RouterOS CHR 7.24.6 image through MikroTik's official distribution channel.
2. Configure a QEMU MikroTik CHR template that uses the image name `chr-7.24.6.img`, 256 MiB RAM, one vCPU, five adapters, and an Ethernet adapter model compatible with the saved project.
3. Extract the ZIP, then open `Network-Topology-Discovery-1.gns3` from the extracted folder. If GNS3 reports a missing image, assign the local CHR image to the MikroTik template.
4. Edit `Cloud1` and select the host-only adapter on that computer that connects to its Alpine VM. The supplied project references the creator's `Ethernet 3`; that adapter name may not exist elsewhere. The Cloud link is directly to MikroTik-1; there is no Cloud switch.

The ZIP does not make the Windows host-only adapter portable. Rebinding Cloud on another machine is required for management connectivity. The host-only segment must use `192.168.56.0/24` for the documented addresses, or the router/controller targets and SNMP allowed-source address must be updated together.

## Topology and interface mapping

The GNS3 labels `e0`, `e1`, and `e2` are adapter slots 0, 1, and 2; in this CHR template they map to RouterOS `ether1`, `ether2`, and `ether3` respectively.

| Connection | GNS3 interface mapping | Subnet / segment |
|---|---|---|
| Cloud1 — MikroTik-1 | Cloud `Ethernet 3` — MikroTik-1 `e0` / `ether1` | Host-only `192.168.56.0/24` |
| MikroTik-1 — MikroTik-2 | MikroTik-1 `e1` / `ether2` — MikroTik-2 `e0` / `ether1` | `10.0.12.0/30` |
| MikroTik-1 — MikroTik-3 | MikroTik-1 `e2` / `ether3` — MikroTik-3 `e0` / `ether1` | `10.0.13.0/30` |
| MikroTik-2 — MikroTik-4 | MikroTik-2 `e1` / `ether2` — MikroTik-4 `e0` / `ether1` | `10.0.24.0/30` |
| MikroTik-3 — MikroTik-4 | MikroTik-3 `e1` / `ether2` — MikroTik-4 `e1` / `ether2` | `10.0.34.0/30` |
| MikroTik-2 — Switch1 | MikroTik-2 `e2` / `ether3` — Switch1 `e0` | `192.168.110.0/24` |
| MikroTik-3 — Switch2 | MikroTik-3 `e2` / `ether3` — Switch2 `e0` | `192.168.120.0/24` |
| MikroTik-4 — Switch3 | MikroTik-4 `e2` / `ether3` — Switch3 `e0` | `192.168.130.0/24` |

## Address plan

| Device | Interface | Address |
|---|---|---|
| MikroTik-1 | `ether1` / management | `192.168.56.105/24` |
| MikroTik-1 | `ether2` / MikroTik-2 transit | `10.0.12.1/30` |
| MikroTik-1 | `ether3` / MikroTik-3 transit | `10.0.13.1/30` |
| MikroTik-2 | `ether1` / MikroTik-1 transit | `10.0.12.2/30` |
| MikroTik-2 | `ether2` / MikroTik-4 transit | `10.0.24.1/30` |
| MikroTik-2 | `ether3` / LAN gateway | `192.168.110.1/24` |
| MikroTik-3 | `ether1` / MikroTik-1 transit | `10.0.13.2/30` |
| MikroTik-3 | `ether2` / MikroTik-4 transit | `10.0.34.1/30` |
| MikroTik-3 | `ether3` / LAN gateway | `192.168.120.1/24` |
| MikroTik-4 | `ether1` / MikroTik-2 transit | `10.0.24.2/30` |
| MikroTik-4 | `ether2` / MikroTik-3 transit | `10.0.34.2/30` |
| MikroTik-4 | `ether3` / LAN gateway | `192.168.130.1/24` |
| Alpine Linux | `eth0` / host-only | `192.168.56.102/24` |
| Alpine Linux | `eth1` / VirtualBox NAT | `10.0.3.15/24`, gateway `10.0.3.2` |

MikroTik-1's `ether1` is configured as a DHCP client in the exported RouterOS configuration; the lab currently receives `192.168.56.105`. On a different host, ensure the host-only DHCP service reserves that address for MikroTik-1, or assign the target address consistently and update the Python router target and SNMP source restrictions. The discovery scripts target MikroTik-1 at `192.168.56.105` and allow SNMP from Alpine at `192.168.56.102`.

The other routers use OSPFv2 on the transit links. Allow OSPF to converge after starting the routers before testing traffic between LANs.

## VPCS addresses and ping checks

The packaged `startup.vpc` files configure these addresses automatically when the VPCS nodes start:

| VPCS | Address | Default gateway |
|---|---|---|
| PC1 | `192.168.110.11/24` | `192.168.110.1` |
| PC2 | `192.168.110.12/24` | `192.168.110.1` |
| PC3 | `192.168.120.11/24` | `192.168.120.1` |
| PC4 | `192.168.120.12/24` | `192.168.120.1` |
| PC5 | `192.168.130.11/24` | `192.168.130.1` |
| PC6 | `192.168.130.12/24` | `192.168.130.1` |

After all nodes start, open the PC1 VPCS console and run:

```text
show
ping 192.168.110.1
ping 192.168.120.11
ping 192.168.130.11
```

The first ping checks the local gateway. The other pings check routing to the other two LANs. If the gateway ping fails, check the PC1-to-Switch1 link and MikroTik-2 `ether3`. If cross-LAN pings fail, wait for OSPF convergence and check the router transit links and routes.

## Router configuration exports

Reference exports are in [`../configs/`](../configs/). The project ZIP also includes per-router QEMU disks, which may already retain the lab configuration. Do not import an `.rsc` export over an already configured router: it contains `add` commands that can create duplicate entries. For a fresh router, transfer the matching `.rsc` file into its RouterOS Files list and run `/import file-name=MikroTik-N.rsc` from that router's console. RouterOS exports do not include the system user's password; set credentials locally and do not add them to GitHub.

## Run the discovery engine

Alpine Linux is a separate VirtualBox VM and must be connected to the same host-only segment. Ensure it has routes to the transit and LAN subnets through MikroTik-1, SNMPv2c is enabled with the lab's read-only community, and SSH is reachable on all routers. From the repository root, follow the Python setup in the main README and run:

```sh
python src/snmp_check_routers.py
python src/snmp_discovery.py
python src/add_neighbor_protocols.py
python src/render_corrected_topology.py
```

The discovery scripts need a live, reachable lab. The renderer can also use the committed `discovery.json` to reproduce the diagram without querying routers.
