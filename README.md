# PowerDNS on Podman/Kubernetes

## Building the Containers

```bash
podman build -f Containerfile.auth -t pdns-auth .
```

## Running the Containers with Podman

```bash
podman run --rm -v ./config/auth:/etc/pdns:Z pdns-auth
```