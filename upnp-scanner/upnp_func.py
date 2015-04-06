#!/usr/bin/env python

from scapy.all import *

class upnp:

 def passive_scan(self):
  def upnp_sniff(p):
   if p.haslayer(UDP) and p.haslayer(Raw):
    if p[UDP].dport == 1900:
     if "NOTIFY *" in p[Raw].load:
      print "\n\n"+p[Raw].load
  try:
   sniff(prn=upnp_sniff, filter="udp")
  except:
   print "\n[-] Can't launch sniffer :/\n"

 def active_scan(self, target):
  req = 'M-SEARCH * HTTP/1.1\r\nHost:239.255.255.250:1900\r\nST:upnp:rootdevice\r\nMan:"ssdp:discover"\r\nMX:3\r\n\r\n'
  ip=IP(dst=target)
  udp=UDP(sport=random.randint(1,65536), dport=1900)
  pck = ip/udp/req
  try:
   rep = sr1(pck, verbose=0)
   print "\n\n"+rep[Raw].load
  except:
   print "\n[-] Can't send packet :/\n"
