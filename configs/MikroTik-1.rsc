# 2026-11-04 23:03:02 by RouterOS 7.24.6
# system id = LNKYdP2/6zI
#
/interface ethernet
set [ find default-name=ether1 ] disable-running-check=no
set [ find default-name=ether2 ] disable-running-check=no
set [ find default-name=ether3 ] disable-running-check=no
set [ find default-name=ether4 ] disable-running-check=no
set [ find default-name=ether5 ] disable-running-check=no
/routing ospf instance
add name=ospf-v2 router-id=10.0.12.1
/routing ospf area
add instance=ospf-v2 name=backbone
/snmp community
set [ find default=yes ] read-access=no
add addresses=192.168.56.102/32 name=TopoRead2026
/ip neighbor discovery-settings
set discover-interface-list=all
/ip address
add address=10.0.12.1/30 interface=ether2 network=10.0.12.0
add address=10.0.13.1/30 interface=ether3 network=10.0.13.0
/ip dhcp-client
add interface=ether1 name=client1
/routing ospf interface-template
add area=backbone networks=10.0.12.0/30
add area=backbone networks=10.0.13.0/30
add area=backbone networks=192.168.56.0/24 passive
/snmp
set enabled=yes
/system identity
set name=MikroTik-1
