#!/usr/bin/env python

from scapy.all import *
from upnp_func import *
import sys
import os
import string

def intro():
 print "UPnP Config File Scanner".center(80)
 print "Author: St0rn | anbu-pentest.com\n".center(80)
 print ""

def clear():
 os.system('cls' if os.name == 'nt' else 'clear')
 
upnp = upnp()
clear()

try:
 if len(sys.argv) < 2:
  print "\nUsage: %s [passive | active] [target if activ scan]\n" %(sys.argv[0])
  sys.exit()
 else:
  if string.lower(sys.argv[1]) == "passive":
   intro()
   print "[+] Passive UPnP Scan, Waiting".center(80)
   upnp.passive_scan()
  elif string.lower(sys.argv[1]) == "active":
   if len(sys.argv) < 3:
    print "\nUsage: %s [passiv | activ] [target if activ scan]\n" %(sys.argv[0])
    sys.exit
   else:
    intro()
    print "[+] Active UPnP Scan".center(80)
    upnp.active_scan(sys.argv[2])
except c:
 print "Error: %s\n" %c
 sys.exit()
