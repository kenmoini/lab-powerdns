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

