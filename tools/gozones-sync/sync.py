import yaml
import argparse
import datetime
import requests

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
#print(response.json())

# =============================================
# Functions
def addLastDot(name):
    if name[-1] != '.':
        name = name + '.'
    return name

def removeLastDot(name):
    if name[-1] == '.':
        name = name[:-1]
    return name

def stripCIDR(name):
    if '/' in name:
        name = name.split('/')[0]
    return name

def processNSRecords(input, defaultTTL):
    anchoredTTLS = {}
    nsRecords = []
    anchoredNSRecords = {}
    nsRRSets = []
    for ns in input['records']['NS']:
        if ns['anchor'] != "@":
            anchor = addLastDot(ns['anchor'])
        else:
            anchor = addLastDot(input['zone'])
        anchoredNSRecords[anchor] = []

        if "ttl" in ns.keys():
            anchoredTTLS[anchor] = str(ns['ttl'])
        else:
            anchoredTTLS[anchor] = defaultTTL

    for ns in input['records']['NS']:
        if ns['anchor'] != "@":
            anchor = addLastDot(ns['anchor'])
        else:
            anchor = addLastDot(input['zone'])

        anchoredNSRecords[anchor].append({
            'content': addLastDot(ns['name'] + '.' + ns['domain']),
            'disabled': False
        })

    # Loop through the anchored NS Records
    for anchor, nsRecords in anchoredNSRecords.items():
        recordTTL = anchoredTTLS[anchor]
        nsRRSets.append({
            'name': anchor,
            'type': 'NS',
            'ttl': recordTTL,
            'changetype': 'REPLACE',
            'records': nsRecords
        })
    return nsRRSets

def processARecords(input, defaultTTL):
    aRecords = []
    anchoredARecords = {}
    aRRSets = []
    anchoredTTLS = {}
    for record in input['records']['A']:
        if record['name'] != "@":
            name = addLastDot(record['name'] + '.' + zone['zone'])
        else:
            name = addLastDot(input['zone'])
        anchoredARecords[name] = []

        if "ttl" in record.keys():
            anchoredTTLS[name] = str(record['ttl'])
        else:
            anchoredTTLS[name] = defaultTTL
    for record in input['records']['A']:
        if record['name'] != "@":
            name = addLastDot(record['name'] + '.' + zone['zone'])
        else:
            name = addLastDot(input['zone'])
        anchoredARecords[name].append({
            'content': stripCIDR(record['value']),
            'disabled': False
        })

    # Loop through the anchored A Records
    for name, aRecords in anchoredARecords.items():
        recordTTL = anchoredTTLS[name]
        aRRSets.append({
            'name': name,
            'type': 'A',
            'ttl': recordTTL,
            'changetype': 'REPLACE',
            'records': aRecords
        })

    return aRRSets


# =============================================
# Open the GoZones file
with open(args.file, "r") as stream:
    try:
        yaml_data = yaml.safe_load(stream)
        # Loop through the YAML file .dns.zones entries
        for zone in yaml_data['dns']['zones']:
            # Check if the zone exists
            #print(zone)
            print('=====================================')
            print("Checking for Zone: " + zone['zone'])
            response = requests.get(args.server + '/api/v1/servers/localhost/zones/' + zone['zone'], headers=headers)
            if response.status_code == 200:
                # Zone exists, update it
                print(' - Zone exists: ' + zone['name'])
                #print(response.json())
            elif response.status_code == 404:
                # Zone does not exist, create it
                print(' - Creating zone: ' + zone['name'])
                # Create form body
                form_body = {
                    'name': addLastDot(zone['zone']),
                    'kind': 'Native',
                    'type': 'Zone',
                    'dnssec': False
                }
                response = requests.post(args.server + '/api/v1/servers/localhost/zones', headers=headers, json=form_body)
                #print(response.json())
            else:
                # Unknown error
                print('Error while checking for zone: ' + entry['name'])

            # =============================================
            # Set the SOA Record
            print(' - Setting SOA Record')
            defaultTTL = str(zone['default_ttl'])
            recordDate = datetime.datetime.now().strftime("%Y%m%d%H")
            form_body = {
                'rrsets': [
                    {
                        'name': addLastDot(zone['zone']),
                        'type': 'SOA',
                        'ttl': defaultTTL,
                        'changetype': 'REPLACE',
                        'records': [
                            {
                                'content': addLastDot(zone['primary_dns_server']) + ' admin.' + addLastDot(zone['zone']) + ' ' + recordDate + ' 10800 ' + defaultTTL +' 604800 ' + defaultTTL,
                                'disabled': False
                            }
                        ]
                    }
                ]
            }
            response = requests.patch(args.server + '/api/v1/servers/localhost/zones/' + zone['zone'], headers=headers, json=form_body)
            if response.status_code == 204:
                print('   - SOA Record updated')

            # =============================================
            # Set the NS Records
            print(' - Setting NS Records')
            # Loop through the NS Records
            nsRRSets = processNSRecords(zone, defaultTTL)
            
            # Send the request
            form_body = {
                'rrsets': nsRRSets
            }

            response = requests.patch(args.server + '/api/v1/servers/localhost/zones/' + zone['zone'], headers=headers, json=form_body)
            if response.status_code == 204:
                print('   - NS Records updated')
            else:
                print(response.json())

            # =============================================
            # Set the A Records
            print(' - Setting A Records')
            # Loop through the A Records
            aRRSets = processARecords(zone, defaultTTL)

            # Send the request
            form_body = {
                'rrsets': aRRSets
            }

            response = requests.patch(args.server + '/api/v1/servers/localhost/zones/' + zone['zone'], headers=headers, json=form_body)
            if response.status_code == 204:
                print('   - A Records updated')
            else:
                print(response.json())

        #print(yaml.safe_load(stream))
    except yaml.YAMLError as exc:
        print(exc)