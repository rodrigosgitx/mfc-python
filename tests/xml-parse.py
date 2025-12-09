import xml.etree.ElementTree as ET
from dns.rdatatype import AAAA

# Parse an XML file
tree = ET.parse('dft-metainfo.xml')
root = tree.getroot()

# Accessing elements
for child in root:
    if (child.tag in ['message'] and child.attrib['type'] in ['CTS_TR','CTM_DS','CTS_DR']):
        print (child.tag, child.attrib)
        for net in child:
            print (net.tag, net.attrib)
        
'''origen = 'PM1AA001****'
destino = 'PM2AA002****'
matricula= '1234567890**********'
        
message = ''
for child in root:
    if (child.tag in ['message'] and child.attrib['type'] in ['01']):
        for net in child:
            if (net.attrib['name'] == 'source' and origen):
                message = message + origen
            elif (net.attrib['name'] == 'destination' and destino):
                message = message + destino
            elif (net.attrib['name'] == 'tunumber' and matricula):
                message = message + matricula
            else:
                n=int(net.attrib["length"])+1
                for a in range(n): message = message + '*'
            print(message)
print(message)

'''        
            

