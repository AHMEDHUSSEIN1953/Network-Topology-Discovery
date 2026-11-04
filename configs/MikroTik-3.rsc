# 2026-11-04 22:59:53 by RouterOS 7.24.6
# system id = RXUOuYs1WWI
#
/interface ethernet
set [ find default-name=ether1 ] disable-running-check=no
set [ find default-name=ether2 ] disable-running-check=no
set [ find default-name=ether3 ] disable-running-check=no
set [ find default-name=ether4 ] disable-running-check=no
set [ find default-name=ether5 ] disable-running-check=no
/routing ospf instance
add name=ospf-v2 router-id=10.0.13.2
/routing ospf area
add instance=ospf-v2 name=backbone
/snmp community
set [ find default=yes ] read-access=no
add addresses=192.168.56.102/32 name=TopoRead2026
/ip neighbor discovery-settings
set discover-interface-list=all
/ip address
add address=10.0.13.2/30 interface=ether1 network=10.0.13.0
add address=10.0.34.1/30 interface=ether2 network=10.0.34.0
add address=192.168.120.1/24 interface=ether3 network=192.168.120.0
/ip dhcp-client
add interface=ether1 name=client1
/routing ospf interface-template
add area=backbone networks=10.0.13.0/30
add area=backbone networks=10.0.34.0/30
add area=backbone networks=192.168.120.0/24 passive
/snmp
set enabled=yes
/system identity
set name=MikroTik-3
