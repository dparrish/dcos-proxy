# dcos-proxy
DCOS Frontend Proxy

This is a reverse load balancer based on Nginx that is designed to run on the public slave nodes of a Mesosphere DCOS cluster.

There is a sample json file for running the balancer, which you can use with:

```
dcos marathon app add frontend-balancer.json
```

The refresh job runs every 10 seconds, looking at all your apps with a `VIRTUAL_HOST` label, and creating a proxy entry
directed to the first port supplied.

```json
{
    "constraints": [["hostname", "UNIQUE"]],
    "container": {
        "type": "DOCKER",
        "docker": {
            "image": "registry"
        }
    },
    "labels": {
        "VIRTUAL_HOST": "registry.your.domain.here"
    },
    "id": "registry",
    "cpus": 1,
    "mem": 256,
    "instances": 2,
    "ports": [5000]
}
```
