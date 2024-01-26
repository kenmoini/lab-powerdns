# PowerDNS on Podman/Kubernetes

## Building the Containers

```bash
podman build -f Containerfile.auth -t pdns-auth .
```

## Running the Containers with Podman

```bash
podman pod create pdns
podman run -d --pod pdns --name pdns-auth --rm -v ./config/auth:/etc/pdns:Z pdns-auth
podman run -d --pod pdns --name pdns-mysql --rm -v ./config/auth:/etc/pdns:Z pdns-auth
```