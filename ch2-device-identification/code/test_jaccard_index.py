
# 2019-07-12 10:41:41,964 [MainThread  ] [INFO ]  Received SSDP record 'NOTIFY * HTTP/1.1: ['CACHE-CONTROL', 'max-age=100']' for device at 192.168.0.102
# 2019-07-12 10:41:41,970 [MainThread  ] [INFO ]  Local device at 192.168.0.102 has characteristics [["Vendor", "Philips Lighting BV"], ["SSDP", "NOTIFY * HTTP/1.1: ['LOCATION', 'http://192.168.0.102:80/description.xml']"], ["SSDP", "NOTIFY * HTTP/1.1: ['HOST', '239.255.255.250:1900']"], ["DNS", "('www.ecdinterface.philips.com', 'A')"], ["SSDP", "NOTIFY * HTTP/1.1: ['CACHE-CONTROL', 'max-age=100']"], ["SSDP", "NOTIFY * HTTP/1.1: ['NTS', 'ssdp:alive']"], ["SSDP", "NOTIFY * HTTP/1.1: ['SERVER', 'FreeRTOS/6.0.5, UPnP/1.0, IpBridge/0.1']"], ["SSDP", "NOTIFY * HTTP/1.1: ['NT', 'upnp:rootdevice']"], ["NUPNP", "None"], ["DNS", "('dcp.dc1.philips.com', 'A')"]], matches Milight iBox 2 Wifi Controller with 5.9323931049921645.


import json
from textdistance import levenshtein

def fuzzy_intersection(a, b):
    if len(a) > len(b):
        a, b = b, a
    s = 0
    for elem in a:
        m = max([levenshtein.normalized_similarity(elem[1], i[1]) for i in b if i[0] == elem[0]] + [0])
        if m:
            s += m
    return s

# dtcs = [["SSDP", "M-SEARCH * HTTP/1.1: ['USER-AGENT', 'Google Chrome/84.0.4147.135 Mac OS X']"], ["SSDP", "M-SEARCH * HTTP/1.1: ['MX', '1']"], ["mDNS", "b'\\x16rpBA=4'].."], ["SSDP", "M-SEARCH * HTTP/1.1: ['MAN', '\"ssdp:discover\"']"], ["SSDP", "M-SEARCH * HTTP/1.1: ['HOST', '239.255.255.250:1900']"], ["mDNS", "_companion-link._tcp.local."], ["SSDP", "M-SEARCH * HTTP/1.1: ['ST', 'urn:dial-multiscreen-org:service:dial:1']"]]
# b = set()
# for c in dtcs:
# 	assert isinstance(c[0], str) and isinstance(c[1], str)
# 	b.add((c[0],c[1]))
# dtc = set([c for c in b])
# test = [["SSDP", "NOTIFY * HTTP/1.1: ['CACHE-CONTROL', 'max-age=100']"]]
# b = set()
# for c in test:
# 	assert isinstance(c[0], str) and isinstance(c[1], str)
# 	b.add((c[0],c[1]))
# test = b

dtc = {('SSDP', "NOTIFY * HTTP/1.1: ['HOST', '239.255.255.250:1900']"), ('SSDP', "NOTIFY * HTTP/1.1: ['SERVER', 'SDK 4.3.0.0 UPnP/1.0 MiniUPnPd/1.6']"), ('SSDP', "NOTIFY * HTTP/1.1: ['NT', 'urn:schemas-upnp-org:service:WANPPPConnection:1']"), ('SSDP', "NOTIFY * HTTP/1.1: ['NT', 'upnp:rootdevice']"), ('SSDP', "NOTIFY * HTTP/1.1: ['BOOTID.UPNP.ORG', '1']"), ('SSDP', "NOTIFY * HTTP/1.1: ['NT', 'urn:schemas-upnp-org:service:WANIPConnection:1']"), ('SSDP', "NOTIFY * HTTP/1.1: ['lOCATION', 'http://192.168.1.1:6352/rootDesc.xml']"), ('SSDP', 'NOTIFY * HTTP/1.1: [\'OPT\', \'"http://schemas.upnp.org/upnp/1/0/";\']'), ('open port', 'tcp/80'), ('SSDP', "NOTIFY * HTTP/1.1: ['01-NLS', '1']"), ('SSDP', "NOTIFY * HTTP/1.1: ['CONFIGID.UPNP.ORG', '1337']"), ('SSDP', "NOTIFY * HTTP/1.1: ['NT', 'urn:schemas-upnp-org:device:WANDevice:1']"), ('SSDP', "NOTIFY * HTTP/1.1: ['Server', 'SDK 4.3.0.0 UPnP/1.0 MiniUPnPd/1.6']"), ('SSDP', "NOTIFY * HTTP/1.1: ['NT', 'urn:schemas-upnp-org:service:Layer3Forwarding:1']"), ('SSDP', "NOTIFY * HTTP/1.1: ['NT', 'urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1']"), ('SSDP', "NOTIFY * HTTP/1.1: ['NTS', 'ssdp:alive']"), ('SSDP', "NOTIFY * HTTP/1.1: ['NT', 'urn:schemas-upnp-org:device:WANConnectionDevice:1']"), ('SSDP', "NOTIFY * HTTP/1.1: ['CACHE-CONTROL', 'max-age=60']"), ('SSDP', "NOTIFY * HTTP/1.1: ['NT', 'urn:schemas-upnp-org:device:InternetGatewayDevice:1']")}
test = {('SSDP', "M-SEARCH * HTTP/1.1: ['USER-AGENT', 'Google Chrome/84.0.4147.135 Mac OS X']"), ('SSDP', "M-SEARCH * HTTP/1.1: ['MX', '1']"), ('mDNS', "b'\\x16rpBA=4'].."), ('SSDP', 'M-SEARCH * HTTP/1.1: [\'MAN\', \'"ssdp:discover"\']'), ('SSDP', "M-SEARCH * HTTP/1.1: ['HOST', '239.255.255.250:1900']"), ('mDNS', '_companion-link._tcp.local.'), ('SSDP', "M-SEARCH * HTTP/1.1: ['ST', 'urn:dial-multiscreen-org:service:dial:1']")}

intersection = fuzzy_intersection(dtc, test)
print(len(dtc))
print(len(test))
print(intersection)
union = len(dtc) + len(test) - intersection
jaccard_index = intersection / union
print(jaccard_index*100)
