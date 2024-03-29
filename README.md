# PowerDNS on Podman/Kubernetes

## Building the Containers

```bash
podman build -f Containerfile.auth -t pdns-auth .
podman build -f Containerfile.recursor -t pdns-recursor .
podman build -f Containerfile.mysql -t pdns-mysql .
```

## Running the Containers with Podman

```bash
# Preflight needs
mkdir -p /opt/pdns/data/{mysql,web-ui}
chown 27:27 /opt/pdns/data/mysql
chown 100:101 /opt/pdns/data/web-ui

# Create the Pod
podman pod create --name pdns --network lanBridge --ip "192.168.42.39" -p 5300 -p 5353 -p 3306 -p 80

# Setup the Database
podman run -d --pod pdns --name pdns-mysql --rm -v /opt/pdns/data/mysql:/var/lib/mysql/data:Z pdns-mysql
podman exec pdns-mysql sh -c 'mysql -u $MYSQL_USER --password=$MYSQL_PASSWORD $MYSQL_DATABASE < /opt/app-root/src/mysql-init/schema.sql'
podman exec pdns-mysql sh -c 'mysql -u $MYSQL_USER --password=$MYSQL_PASSWORD $MYSQL_DATABASE < /opt/app-root/src/mysql-init/enable_fkeys.sql'
podman exec pdns-mysql sh -c 'mysqlshow -u $MYSQL_USER --password=$MYSQL_PASSWORD $MYSQL_DATABASE;'

# Run the Authoritative Server
podman run -d --pod pdns --name pdns-auth --rm -v ./config/auth:/etc/pdns:Z pdns-auth

# Run the Recursive Server
podman run -d --pod pdns --name pdns-recursor --rm -v ./config/recursor:/etc/pdns-recursor:Z pdns-recursor

# Run the Web UI
podman run -d --pod pdns --name pdns-ui --rm -v /opt/pdns/data/web-ui:/data:Z docker.io/powerdnsadmin/pda-legacy

# Access the Web UI at http://192.168.42.39
# dig @192.168.42.39 -p 5353 testing.kemo.labs
```

## Deploy to Kubernetes

The deployment and configuration manifests are heavily dependant on environments so there will be modifications needed.

```bash
# Deploy the MySQL server
kubectl apply -k deployment/pdns-mysql/

# Deploy the PowerDNS Stack
kubectl apply -k deployment/overlays/ns-2/
```

Next, access http://ns2.apps.k8s.kemo.labs/ and create an Admin User via the Web UI.  Configure the server endpoint as `http://192.168.42.10:8081`

## Credits

- Many thanks to Brandon B. Jozsa <bjozsa@redhat.com> whom I stole a lot of this from :)
- Also thanks to Habbie in #powerdns OFTC IRC for helping me figure out some configuration issues