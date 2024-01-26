# PowerDNS on Podman/Kubernetes

## Building the Containers

```bash
podman build -f Containerfile.auth -t pdns-auth .
```

## Running the Containers with Podman

```bash
podman run -d --name pdns-auth --rm -v ./config/auth:/etc/pdns:Z pdns-auth
```