import yaml
import argparse
import datetime
import requests
import ipaddress

# =============================================
# Handle command line arguments
parser = argparse.ArgumentParser(
                    prog='sync.py',
                    description='Takes in a GoZones file and syncs to PowerDNS via the API',
                    epilog='Use at your own risk')
parser.add_argument('-f', '--file', help='GoZones file to sync', required=True)
parser.add_argument('-s', '--server', help='PowerDNS Server API eg http://127.0.0.1:8081', required=True)
parser.add_argument('-k', '--key', help='PowerDNS API Key', required=True)
args = parser.parse_args()

# =============================================
# Set request headers
headers = {
    'X-API-Key': args.key,
    'Content-Type': 'application/json'
}

# =============================================
# Perform an API test
response = requests.get(args.server + '/api/v1/servers/localhost', headers=headers)
if response.status_code != 200:
    print('Error: Unable to connect to PowerDNS API')
    exit()

def ip2bin(ip):
    octets = map(int, ip.split('/')[0].split('.')) # '1.2.3.4'=>[1, 2, 3, 4]
    binary = '{0:08b}{1:08b}{2:08b}{3:08b}'.format(*octets)
    range = int(ip.split('/')[1]) if '/' in ip else None
    return binary[:range] if range else binary

def splitV4AddressIntoParts(ipAddress):
    addressArray = ipAddress.split('/')
    address = addressArray[0]
    cidr = addressArray[1]



# =============================================
with open(args.file, "r") as stream:
    try:
        yaml_data = yaml.safe_load(stream)
        # Loop through the YAML file .dns.zones entries
        for zone in yaml_data['dns']['zones']:
            # Check if the zone exists
            #print(zone)
            print('=====================================')
            print("Checking for reverse records in Zone: " + zone['zone'])
            if 'A' in zone['records'].keys():
                # Loop through the A records
                for record in zone['records']['A']:
                    print(record)
                    if '/' in record['value']:
                        ipPart = record['value'].split('/')[0]
                        cidrPart = record['value'].split('/')[1]
                        ipNetwork = ipaddress.ip_network(record['value'], False)
                        ipAddress = ipaddress.ip_address(ipPart)
                        ipBinary = ip2bin(ipPart)
                        print(ipPart + ": " + ipBinary)
                        print(str(ipNetwork.network_address) + " : " + ip2bin(str(ipNetwork.network_address)))
                        print("subtracted: " + str(int(ipBinary, 2) - int(ip2bin(str(ipNetwork.network_address)), 2)))

    except yaml.YAMLError as exc:
        print(exc)