import urllib
import urllib2
from pprint import pprint
import ssl

url = 'https://10.180.21.67/api/space/device-management/discover-devices'
payload = "<discover-devices> \
            <ipAddressDiscoveryTarget>\
                <ipAddress>10.180.21.200</ipAddress>\
            </ipAddressDiscoveryTarget>\
            <usePing>true</usePing>\
            <sshCredential>\
     	        <userName>root</userName>\
                <password>juniper123</password>\
            </sshCredential>   \
            <manageDiscoveredSystemsFlag>true</manageDiscoveredSystemsFlag>\
        </discover-devices>"

gcontext = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
req = urllib2.Request(url, payload)
req.add_header('authorization', 'Basic c3VwZXI6QW0zckxAYkFtM3JMQGI=')
req.add_header('content-type', 'application/vnd.net.juniper.space.device-management.discover-devices+xml;version=2;charset=UTF-8')

response = urllib2.urlopen(req, context=gcontext).read()

pprint(response)